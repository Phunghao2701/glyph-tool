import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { createProject, startAnalysis, uploadSource } from "../api/font-import.api";
import { AppLink, useNavigate } from "../../../app/providers/NavigationProvider";
import { Button, ErrorBox } from "../../../shared/ui";
import { Icon } from "../../../shared/ui/Icon";
import { getError } from "../../../shared/utils/errors";
import { Input } from "../../../shared/ui/primitives/input";
import { AnimatePresence, motion } from "motion/react";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";

export function NewProjectPage() {
  const { t } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError("");
    if (!file) { setError(t("import.chooseFile")); return; }
    if (!/\.(ttf|otf)$/i.test(file.name)) { setError(t("import.onlyFontFiles")); return; }
    setBusy(true);
    try {
      const project = await createProject(name.trim() || file.name.replace(/\.(ttf|otf)$/i, ""));
      await uploadSource(project.id, file);
      const job = await startAnalysis(project.id);
      navigate("/projects/" + project.id + "?job=" + encodeURIComponent(job.id));
    } catch (e) { setError(getError(e)); setBusy(false); }
  };
  return <section className="page new-project-page">
    <div className="page-head"><div><div className="eyebrow">{t("import.eyebrow")}</div><h1 className="page-title">{t("import.title")}</h1><p className="page-description">{t("import.description")}</p></div></div>
    <form className="card settings-card form-stack" onSubmit={submit}>
      <label className="form-label">{t("import.name")} <Input className="form-input" value={name} onChange={e => setName(e.target.value)} placeholder={t("import.namePlaceholder")} /></label>
      <label className="dropzone"><input type="file" accept=".ttf,.otf,font/ttf,font/otf" onChange={e => setFile(e.target.files?.[0] || null)} />
        <span className="drop-icon"><Icon name="upload-cloud" /></span><AnimatePresence initial={false} mode="wait"><motion.strong key={file?.name || "prompt"} style={{ display: "inline-block" }} initial={reduceMotion ? false : { opacity: 0, y: 3 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -3 }} transition={{ duration: reduceMotion ? 0 : 0.14 }}>{file ? file.name : t("import.drop")}</motion.strong></AnimatePresence><p>{file ? (file.size / 1024 / 1024).toFixed(2) + " MB" : t("import.fileLimit")}</p>
      </label>
      {error && <ErrorBox error={error} />}
      <div className="modal-bottom"><AppLink to="/projects" className="btn btn-light">{t("common.cancel")}</AppLink><Button type="submit" kind="primary" disabled={busy}>{busy ? t("import.uploading") : t("import.create")}</Button></div>
    </form>
  </section>;
}
