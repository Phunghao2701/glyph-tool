import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { deleteExport, listExports, listProjects, updateExport, type ExportArtifact, type Project } from "../api/published-fonts.api";
import { Button, CrudActions, ErrorBox, Icon, Loading } from "../../../shared/ui";
import { Input } from "../../../shared/ui/primitives/input";
import { getError } from "../../../shared/utils/errors";
import "../published-fonts.css";

type ExportGroup = { latest: ExportArtifact; earlier: ExportArtifact[] };

function normalizeSearch(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase().trim();
}

export function PublishedFontsPage() {
  const { t, i18n } = useTranslation();
  const [artifacts, setArtifacts] = useState<ExportArtifact[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [nextArtifacts, nextProjects] = await Promise.all([listExports(), listProjects()]);
      setArtifacts(nextArtifacts);
      setProjects(nextProjects);
    } catch (reason) {
      setError(getError(reason));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const projectNames = useMemo(() => new Map(projects.map(project => [project.id, project.name])), [projects]);
  const exportGroups = useMemo(() => {
    const sorted = [...artifacts].sort((left, right) => (Date.parse(right.createdAt || "") || 0) - (Date.parse(left.createdAt || "") || 0));
    const groups = new Map<string, ExportGroup>();
    for (const artifact of sorted) {
      const key = [
        artifact.projectId || "",
        artifact.revisionId,
        artifact.format.toLocaleLowerCase(),
        artifact.filename.normalize("NFKC").toLocaleLowerCase(),
      ].join("\u0000");
      const group = groups.get(key);
      if (group) group.earlier.push(artifact);
      else groups.set(key, { latest: artifact, earlier: [] });
    }
    return [...groups.values()];
  }, [artifacts]);
  const filteredArtifacts = useMemo(() => {
    const term = normalizeSearch(search);
    return exportGroups
      .filter(group => {
        const artifact = group.latest;
        if (!term) return true;
        const projectName = artifact.projectId ? projectNames.get(artifact.projectId) : undefined;
        return normalizeSearch(`${artifact.filename} ${projectName || ""}`).includes(term);
      })
  }, [exportGroups, projectNames, search]);

  const dateLabel = (createdAt?: string) => {
    const date = createdAt ? new Date(createdAt) : null;
    if (!date || Number.isNaN(date.getTime())) return t("publishedFonts.invalidDate");
    const locale = i18n.resolvedLanguage?.startsWith("vi") ? "vi-VN" : "en-US";
    return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(date);
  };

  return <section className="page published-fonts-page">
    <div className="page-head">
      <div>
        <div className="eyebrow">{t("publishedFonts.eyebrow")}</div>
        <h1 className="page-title">{t("publishedFonts.title")}</h1>
        <p className="page-description">{t("publishedFonts.description")}</p>
      </div>
    </div>

    <section className="published-fonts-library card" aria-label={t("publishedFonts.title")}>
      <div className="published-fonts-toolbar">
        <label className="published-fonts-search">
          <Icon name="search" size={17} />
          <Input
            value={search}
            onChange={event => setSearch(event.target.value)}
            placeholder={t("publishedFonts.search")}
            aria-label={t("publishedFonts.searchLabel")}
          />
        </label>
        {!loading && !error && <span className="published-fonts-count">{t("publishedFonts.count", { count: filteredArtifacts.length })}</span>}
      </div>

      {loading ? <Loading /> : error ? <ErrorBox error={error} retry={() => void load()} /> : filteredArtifacts.length === 0 ? (
        search.trim()
          ? <div className="published-fonts-empty"><Icon name="search" size={24} /><p>{t("publishedFonts.noResults")}</p></div>
          : <div className="published-fonts-empty"><Icon name="archive" size={24} /><h2>{t("publishedFonts.empty")}</h2><p>{t("publishedFonts.emptyDescription")}</p></div>
      ) : <div className="published-fonts-grid">
        {filteredArtifacts.map(({ latest: artifact, earlier }) => {
          const projectName = artifact.projectId ? projectNames.get(artifact.projectId) : undefined;
          return <article className="published-font-card" key={artifact.id}>
            <div className="published-font-card-icon"><Icon name="file-type" size={21} /></div>
            <div className="published-font-card-main">
              <h2 title={artifact.filename}>{artifact.filename}</h2>
              <div className="published-font-meta">
                <span><Icon name="folder-open" size={14} />{projectName || t("publishedFonts.noProject")}</span>
                <span><Icon name="clock" size={14} />{dateLabel(artifact.createdAt)}</span>
              </div>
              {earlier.length > 0 && <details className="published-font-versions">
                <summary>{t("publishedFonts.earlierExports", { count: earlier.length })}</summary>
                <ul>{earlier.map(version => <li key={version.id}>
                  <span>{dateLabel(version.createdAt)}</span>
                  <a href={version.downloadUrl} download={version.filename}>{t("publishedFonts.download")}</a>
                  <CrudActions name={version.filename} onRename={async filename => { await updateExport(version.id, filename); await load(); }} onDelete={async () => { await deleteExport(version.id); await load(); }} />
                </li>)}</ul>
              </details>}
            </div>
            <span className="published-font-format">{artifact.format.toUpperCase()}</span>
            <div className="published-font-actions">
              <Button asChild kind="primary" className="published-font-download">
                <a href={artifact.downloadUrl} download={artifact.filename} aria-label={`${t("publishedFonts.download")} ${artifact.filename}`}>
                  <Icon name="arrow-down" size={16} /><span>{t("publishedFonts.download")}</span>
                </a>
              </Button>
              <CrudActions name={artifact.filename} onRename={async filename => { await updateExport(artifact.id, filename); await load(); }} onDelete={async () => { await deleteExport(artifact.id); await load(); }} deleteKind="secondary" />
            </div>
          </article>;
        })}
      </div>}
    </section>
  </section>;
}
