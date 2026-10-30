import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { downloadExportsBackup, listExports, uploadExportsBackupToDrive, type ExportArtifact, type ExportsBackupResult } from "../../../shared/lib/api";
import { Button, Icon, Loading } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";
import { connectGoogleDrive, isGoogleDriveOAuthConfigured, isGoogleDrivePickerConfigured, pickGoogleDriveFolder } from "../google-drive-picker";
import { useDriveSession } from "../drive-session";
import "../backups.css";

type BusyAction = "download" | "connect" | "pick" | "upload" | null;

export function BackupsPage() {
  const { t, i18n } = useTranslation();
  const [exports, setExports] = useState<ExportArtifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<BusyAction>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const { connection: driveConnection, setConnection: setDriveConnection, folder, setFolder } = useDriveSession();
  const [backupResult, setBackupResult] = useState<ExportsBackupResult | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setExports(await listExports());
    } catch (reason) {
      setError(getError(reason));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const downloadBackup = async () => {
    setError("");
    setNotice("");
    setBackupResult(null);
    setBusy("download");
    try {
      const result = await downloadExportsBackup();
      const url = URL.createObjectURL(result.blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = result.filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice(t("backup.downloadSuccess", {
        count: result.fileCount,
        collapsed: result.collapsedVersions,
        naming: result.aiAssisted ? t("backup.aiNaming") : t("backup.metadataNaming"),
      }));
    } catch (reason) {
      setError(getError(reason));
    } finally {
      setBusy(null);
    }
  };

  const connectDrive = async () => {
    setError("");
    setNotice("");
    setBackupResult(null);
    setBusy("connect");
    try {
      const connection = await connectGoogleDrive();
      setDriveConnection(connection);
      setFolder(null);
      setNotice(t("backup.driveConnectedNotice"));
    } catch (reason) {
      setError(getError(reason));
    } finally {
      setBusy(null);
    }
  };

  const chooseFolder = async () => {
    if (!driveConnection) return;
    setError("");
    setNotice("");
    setBackupResult(null);
    setBusy("pick");
    try {
      const selected = await pickGoogleDriveFolder(i18n.resolvedLanguage || i18n.language, driveConnection.accessToken);
      if (!selected) return;
      setFolder(selected);
      setNotice(t("backup.folderSelected", { name: selected.name }));
    } catch (reason) {
      setError(getError(reason));
    } finally {
      setBusy(null);
    }
  };

  const uploadBackup = async () => {
    if (!folder || !driveConnection) return;
    if (driveConnection.expiresAt <= Date.now()) {
      setDriveConnection(null);
      setFolder(null);
      const message = t("backup.driveExpired");
      setError(message);
      window.alert(message);
      return;
    }
    setError("");
    setNotice("");
    setBackupResult(null);
    setBusy("upload");
    try {
      const result = await uploadExportsBackupToDrive(folder.id, driveConnection.accessToken);
      setBackupResult(result);
      const message = t("backup.driveSuccess", { name: result.folderName });
      setNotice(message);
      window.alert(message);
    } catch (reason) {
      const message = getError(reason);
      setError(message);
      window.alert(t("backup.driveFailure", { reason: message }));
      if (reason && typeof reason === "object" && "status" in reason && reason.status === 401) {
        setDriveConnection(null);
        setFolder(null);
      }
    } finally {
      setBusy(null);
    }
  };

  const backupExportCount = new Set(exports.map(artifact => [
    artifact.projectId || artifact.variantId,
    artifact.format.toLocaleLowerCase(),
  ].join("\u0000"))).size;
  const hasExports = backupExportCount > 0;

  return <section className="page backups-page">
    <div className="page-head">
      <div>
        <div className="eyebrow">{t("backup.eyebrow")}</div>
        <h1 className="page-title">{t("backup.title")}</h1>
        <p className="page-description">{t("backup.description")}</p>
      </div>
    </div>

    {error && <div className="backup-message is-error" role="alert">{error}</div>}
    {notice && <div className="backup-message is-success" role="status">{notice}</div>}

    <div className="backup-options">
      <section className="backup-option card">
        <div className="backup-option-icon"><Icon name="archive" size={22} /></div>
        <div className="backup-option-copy">
          <div className="eyebrow">{t("backup.localEyebrow")}</div>
          <h2>{t("backup.localTitle")}</h2>
          <p>{t("backup.localDescription")}</p>
          <div className="backup-count">
            <strong>{loading ? "—" : backupExportCount}</strong>
            <span>{t("backup.exportCount")}</span>
          </div>
        </div>
        <Button kind="primary" type="button" disabled={loading || !hasExports || busy !== null} onClick={() => void downloadBackup()}>
          <Icon name="arrow-down" size={16} />
          {busy === "download" ? t("backup.preparing") : t("backup.download")}
        </Button>
      </section>

      <section className="backup-option card">
        <div className="backup-option-icon"><Icon name="upload-cloud" size={22} /></div>
        <div className="backup-option-copy">
          <div className="eyebrow">{t("backup.driveEyebrow")}</div>
          <h2>{t("backup.driveTitle")}</h2>
          <p>{t("backup.driveDescription")}</p>
          {folder ? (
            <div className="backup-selected-folder"><Icon name="folder-open" size={16} /><span>{folder.name}</span></div>
          ) : <div className="backup-picker-note">{t(driveConnection ? "backup.driveChooseFolderNote" : "backup.drivePickerNote")}</div>}
        </div>
        <div className="backup-drive-actions">
          <Button kind="secondary" type="button" disabled={!isGoogleDriveOAuthConfigured || busy !== null} onClick={() => void connectDrive()}>
            {busy === "connect" ? t("backup.connectingDrive") : driveConnection ? t("backup.changeDriveAccount") : t("backup.connectDrive")}
          </Button>
          {driveConnection && <span className="backup-drive-connected" role="status"><Icon name="check" size={14} />{t("backup.driveConnected")}</span>}
          <Button kind="secondary" type="button" disabled={!isGoogleDrivePickerConfigured || !driveConnection || busy !== null} onClick={() => void chooseFolder()}>
            {busy === "pick" ? t("backup.openingPicker") : folder ? t("backup.changeFolder") : t("backup.chooseFolder")}
          </Button>
          <Button kind="primary" type="button" disabled={!folder || !driveConnection || !hasExports || busy !== null} onClick={() => void uploadBackup()}>
            <Icon name="upload-cloud" size={16} />
            {busy === "upload" ? t("backup.uploading") : t("backup.uploadDrive")}
          </Button>
        </div>
        {!isGoogleDrivePickerConfigured && <p className="backup-config-note">{t("backup.driveNotConfigured")}</p>}
      </section>
    </div>

    {backupResult && <section className="backup-result card" aria-live="polite">
      <h2>{t("backup.resultTitle")}</h2>
      <div className="backup-result-stats">
        <span><strong>{backupResult.fontFoldersCreated}</strong>{t("backup.foldersCreated")}</span>
        <span><strong>{backupResult.filesUploaded}</strong>{t("backup.filesUploaded")}</span>
        <span><strong>{backupResult.filesUpdated}</strong>{t("backup.filesUpdated")}</span>
        <span><strong>{backupResult.filesSkipped}</strong>{t("backup.filesSkipped")}</span>
        {backupResult.filesRenamed > 0 && <span><strong>{backupResult.filesRenamed}</strong>{t("backup.filesRenamed")}</span>}
        {backupResult.collapsedVersions > 0 && <span><strong>{backupResult.collapsedVersions}</strong>{t("backup.versionsCollapsed")}</span>}
      </div>
      {backupResult.duplicateMatches > 0 && <p className="backup-result-note">{t("backup.duplicatesFound", { count: backupResult.duplicateMatches })}</p>}
      <p className="backup-result-note">{backupResult.aiAssisted ? t("backup.aiNaming") : t("backup.metadataNaming")}</p>
    </section>}

    <section className="backup-info card">
      <h2>{t("backup.namingTitle")}</h2>
      <p>{t("backup.namingDescription")}</p>
      <ul>
        <li>{t("backup.namingFolder")}</li>
        <li>{t("backup.namingFile")}</li>
        <li>{t("backup.namingPrivacy")}</li>
        <li>{t("backup.namingDuplicate")}</li>
        <li>{t("backup.namingOriginal")}</li>
      </ul>
    </section>

    {loading && <Loading />}
    {!loading && !error && !hasExports && <div className="backup-empty card">
      <Icon name="archive" size={24} />
      <h2>{t("backup.emptyTitle")}</h2>
      <p>{t("backup.emptyDescription")}</p>
    </div>}
  </section>;
}
