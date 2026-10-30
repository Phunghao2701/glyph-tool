import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError, saveGlyphEdit, type EditorDocument, type GlyphEdit } from "../../../shared/lib/api";
import { editorFrameResources } from "../../../shared/i18n/resources";

type SaveState = "saved" | "saving" | "error";
type Props = {
  revisionId: string;
  document: EditorDocument;
  onFlushReady: (flush: () => Promise<void>) => void;
  onSaveState: (state: SaveState) => void;
};
type FrameEdit = GlyphEdit & { id: string; key: string };
type FrameMessage = {
  type: string;
  nonce?: string;
  requestId?: string;
  revisionId?: string;
  key?: string;
  edit?: FrameEdit;
  ok?: boolean;
  error?: string;
  language?: string;
};

function safeJson(value: unknown) {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}
function requestId() {
  return globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default function GlyphEditorFrame({ revisionId, document, onFlushReady, onSaveState }: Props) {
  const { t, i18n } = useTranslation();
  const iframe = useRef<HTMLIFrameElement>(null);
  const port = useRef<MessagePort | null>(null);
  const nonce = useRef(requestId());
  const versions = useRef(new Map<string, number>());
  const dirtyKeys = useRef(new Set<string>());
  const dirtyVersions = useRef(new Map<string, number>());
  const queues = useRef(new Map<string, Promise<void>>());
  const flushWaiters = useRef(new Map<string, { resolve: () => void; reject: (error: Error) => void }>());
  const [template, setTemplate] = useState("");
  const [templateError, setTemplateError] = useState("");
  const [pending, setPending] = useState(0);

  const edits = (document.edits || []).map(edit => {
    const id = edit.targetId || edit.id || "";
    return { ...edit, id, key: (edit.kind === "mark" ? "m-" : "g-") + id } as FrameEdit;
  });
  useEffect(() => {
    for (const edit of edits) versions.current.set(edit.kind + ":" + edit.id, edit.version);
  }, [document]);
  useEffect(() => {
    let active = true;
    fetch("/font-editor/editor-shell-template.html").then(response => {
      if (!response.ok) throw new Error(t("editor.templateError"));
      return response.text();
    }).then(value => { if (active) setTemplate(value); }).catch(error => {
      if (active) setTemplateError(error instanceof Error ? error.message : t("editor.templateError"));
    });
    return () => { active = false; };
  }, [t]);

  const rawFv = "fv" in document.document ? document.document.fv : document.document;
  const srcDoc = template ? template
    .replace("__FV_JSON__", safeJson(rawFv))
    .replace("__EDITS_JSON__", safeJson(edits))
    .replace("__EDITOR_I18N_JSON__", safeJson(editorFrameResources))
    .replace("__FRAME_NONCE__", safeJson(nonce.current).slice(1, -1))
    .replace("__REVISION_ID__", safeJson(revisionId).slice(1, -1)) : "";

  const send = useCallback((payload: object) => {
    port.current?.postMessage({ ...payload, nonce: nonce.current });
  }, []);

  const connect = useCallback(() => {
    const target = iframe.current?.contentWindow;
    if (!target || port.current) return;
    const channel = new MessageChannel();
    const hostPort = channel.port1;
    port.current = hostPort;
    hostPort.onmessage = async (event: MessageEvent<FrameMessage>) => {
      const data = event.data;
      if (!data || data.nonce !== nonce.current) return;
      if (data.type === "editor:dirty" && data.key) {
        dirtyKeys.current.add(data.key);
        dirtyVersions.current.set(data.key, (dirtyVersions.current.get(data.key) || 0) + 1);
        onSaveState("saving");
        return;
      }
      if (data.type === "glyph:save" && data.edit && data.requestId && data.revisionId === revisionId) {
        const edit = data.edit;
        const key = edit.kind + ":" + edit.id;
        const dirtyKey = edit.key || (edit.kind === "mark" ? "m-" : "g-") + edit.id;
        const dirtyVersion = dirtyVersions.current.get(dirtyKey) || 0;
        setPending(count => count + 1);
        onSaveState("saving");
        const previous = queues.current.get(key) || Promise.resolve();
        const task = previous.catch(() => undefined).then(async () => {
          const saved = await saveGlyphEdit(revisionId, {
            kind: edit.kind,
            id: edit.id,
            expectedVersion: versions.current.get(key) ?? null,
            w: Number(edit.w || 0),
            touched: !!edit.touched,
            note: edit.note || "",
            contours: edit.contours || [],
            strokes: edit.strokes || [],
            layer: edit.layer || null
          });
          versions.current.set(key, saved.version);
          if ((dirtyVersions.current.get(dirtyKey) || 0) === dirtyVersion) dirtyKeys.current.delete(dirtyKey);
          send({ type: "glyph:save-result", requestId: data.requestId, ok: true, version: saved.version });
        });
        queues.current.set(key, task);
        try {
          await task;
          if (dirtyKeys.current.size === 0) onSaveState("saved");
        } catch (error) {
          const message = error instanceof ApiError ? error.message : error instanceof Error ? error.message : t("editor.cannotSave");
          send({ type: "glyph:save-result", requestId: data.requestId, ok: false, error: message });
          onSaveState("error");
        } finally {
          setPending(count => Math.max(0, count - 1));
          if (queues.current.get(key) === task) queues.current.delete(key);
        }
        return;
      }
      if (data.type === "flush:result" && data.requestId) {
        const waiter = flushWaiters.current.get(data.requestId);
        if (!waiter) return;
        flushWaiters.current.delete(data.requestId);
        if (data.ok) waiter.resolve();
        else waiter.reject(new Error(data.error || t("editor.flushError")));
      }
    };
    hostPort.start();
    target.postMessage({ type: "vfk:connect", nonce: nonce.current, language: i18n.resolvedLanguage || i18n.language }, "*", [channel.port2]);
  }, [i18n.language, i18n.resolvedLanguage, onSaveState, send, revisionId, t]);

  useEffect(() => {
    send({ type: "editor:locale", language: i18n.resolvedLanguage || i18n.language });
  }, [i18n.language, i18n.resolvedLanguage, send]);

  const flush = useCallback(() => new Promise<void>((resolve, reject) => {
    if (!port.current) { reject(new Error(t("editor.notConnected"))); return; }

    const id = requestId();
    flushWaiters.current.set(id, { resolve, reject });
    port.current.postMessage({ type: "flush", nonce: nonce.current, requestId: id });
  }), [t]);

  useEffect(() => { onFlushReady(flush); }, [flush, onFlushReady]);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirtyKeys.current.size || pending) { event.preventDefault(); event.returnValue = ""; }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [pending]);
  useEffect(() => () => { port.current?.close(); port.current = null; }, []);

  if (templateError) return <div className="error-box" role="alert">{templateError}</div>;
  if (!template) return <div className="editor-loading">{t("common.loadingEditor")}</div>;
  return <div className="editor-host">
    <iframe ref={iframe} title={t("editorFrame.drawing")} sandbox="allow-scripts" srcDoc={srcDoc} onLoad={connect} />
    <span className="editor-host-note">{pending ? t("editor.savingCount", { count: pending }) : t("editor.autosaveNote")}</span>
  </div>;
}
