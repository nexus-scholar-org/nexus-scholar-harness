"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { StateCard } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import {
  createWorkspace,
  currentWorkspacePath,
  getWorkspaces,
  openWorkspace,
  previewSlug,
  type CreatedWorkspace,
  type WorkspaceItem,
  type WorkspaceListing,
} from "@/lib/workspaces";

/**
 * The minimal workspace screen (spec `phase2-screening/final/00-workspaces.md`,
 * M5-slim): list the workspaces under the root, create one, open one. Open asks
 * the engine to restart on that folder (workspaces API §4), so the page waits
 * for the new engine to answer and then loads screening. Every check (validity,
 * busy, the root) is the engine's; the screen only shows its answers.
 */

const COPY = {
  en: {
    eyebrow: "Workspaces",
    title: "Which review are you working on?",
    lede: "Each review is one folder on this computer. The list shows the folders under {root}.",
    liveStamp: "Live data from this computer",
    loading: "Reading the workspaces…",
    "cta.new": "New workspace",
    "cta.newReview": "New review",
    "cta.open": "Open",
    openNow: "Open now",
    "table.caption": "Workspaces in {root}",
    "table.title": "Title and folder",
    "table.status": "Status",
    "table.lastActivity": "Last activity",
    "table.action": "Action",
    "status.noCorpus": "No corpus yet",
    "status.corpusAccepted": "Corpus accepted",
    "status.screening": "Screening in progress",
    "status.published": "Published",
    "status.publishedChanged": "Published, decisions since",
    untitled: "Untitled",
    never: "No activity yet",
    "create.label": "New workspace",
    "create.titleField": "Title of the review",
    "create.titleHelp": "The folder is named after the title.",
    "create.folderCaption": "Folder: {path}",
    "create.folderEmpty": "Type a title to see its folder.",
    "create.submit": "Create",
    "create.cancel": "Cancel",
    "create.submitting": "Creating the workspace…",
    "create.placeholderProtocol": "Placeholder protocol. Run the Inception wizard from the terminal to replace it.",
    "next.title": "Workspace created",
    "next.body": "Screening starts from an accepted corpus. Accept it from the terminal:",
    "next.copy": "Copy the command",
    "next.copied": "Copied",
    "next.open": "Open it",
    "empty.title": "No workspaces yet",
    "empty.body": "Your reviews will appear here. To use a folder you already have, start the app on it from the terminal.",
    opening: "Opening {title}…",
    "skipped.count": "{n} folders skipped",
    "skipped.show": "Show them",
    "skipped.hide": "Hide them",
    "invalid.reason.noProject": "no project.json",
    "invalid.reason.noProtocol": "no protocol.json",
    "invalid.reason.noJournal": "no audit journal",
    "invalid.reason.unreadable": "the folder cannot be read",
    notAWorkspace: "Not a workspace: {reason}",
    "busy.run": "An agent run is active in this workspace. Opening another workspace restarts the app and would stop it.",
    "busy.pairing": "An approval is open. Opening another workspace restarts the app and would lose it.",
    "busy.goHome": "Go to screening home",
    "phone.desktopOnly": "Choose the workspace on your desktop. The phone works on the one that is open.",
    "phone.toScreening": "Go to screening",
    footer: "This computer · engine running · {root}",
  },
  fr: {
    eyebrow: "Espaces de travail",
    title: "Sur quelle revue travaillez-vous ?",
    lede: "Chaque revue est un dossier sur cet ordinateur. La liste montre les dossiers de {root}.",
    liveStamp: "Données réelles de cet ordinateur",
    loading: "Lecture des espaces…",
    "cta.new": "Nouvel espace",
    "cta.newReview": "Nouvelle revue",
    "cta.open": "Ouvrir",
    openNow: "Ouvert",
    "table.caption": "Espaces dans {root}",
    "table.title": "Titre et dossier",
    "table.status": "État",
    "table.lastActivity": "Dernière activité",
    "table.action": "Action",
    "status.noCorpus": "Pas encore de corpus",
    "status.corpusAccepted": "Corpus accepté",
    "status.screening": "Sélection en cours",
    "status.published": "Publiée",
    "status.publishedChanged": "Publiée, décisions depuis",
    untitled: "Sans titre",
    never: "Aucune activité",
    "create.label": "Nouvel espace",
    "create.titleField": "Titre de la revue",
    "create.titleHelp": "Le dossier porte le nom du titre.",
    "create.folderCaption": "Dossier : {path}",
    "create.folderEmpty": "Saisissez un titre pour voir son dossier.",
    "create.submit": "Créer",
    "create.cancel": "Annuler",
    "create.submitting": "Création de l'espace…",
    "create.placeholderProtocol": "Protocole provisoire. Lancez l'assistant d'Inception depuis le terminal pour le remplacer.",
    "next.title": "Espace créé",
    "next.body": "La sélection part d'un corpus accepté. Acceptez-le depuis le terminal :",
    "next.copy": "Copier la commande",
    "next.copied": "Copiée",
    "next.open": "L'ouvrir",
    "empty.title": "Aucun espace pour l'instant",
    "empty.body": "Vos revues apparaîtront ici. Pour utiliser un dossier existant, lancez l'application dessus depuis le terminal.",
    opening: "Ouverture de {title}…",
    "skipped.count": "{n} dossiers ignorés",
    "skipped.show": "Les afficher",
    "skipped.hide": "Les masquer",
    "invalid.reason.noProject": "pas de project.json",
    "invalid.reason.noProtocol": "pas de protocol.json",
    "invalid.reason.noJournal": "pas de journal d'audit",
    "invalid.reason.unreadable": "le dossier est illisible",
    notAWorkspace: "Pas un espace : {reason}",
    "busy.run": "Un passage de l'agent est en cours dans cet espace. Ouvrir un autre espace redémarre l'application et l'arrêterait.",
    "busy.pairing": "Une approbation est ouverte. Ouvrir un autre espace redémarre l'application et la perdrait.",
    "busy.goHome": "Aller à l'accueil de la sélection",
    "phone.desktopOnly": "Choisissez l'espace sur votre ordinateur. Le téléphone travaille sur celui qui est ouvert.",
    "phone.toScreening": "Aller à la sélection",
    footer: "Cet ordinateur · moteur en marche · {root}",
  },
  ar: {
    eyebrow: "مساحات العمل",
    title: "على أي مراجعة تعمل؟",
    lede: "كل مراجعة مجلد واحد على هذا الحاسوب. تعرض القائمة المجلدات الموجودة في {root}.",
    liveStamp: "بيانات حقيقية من هذا الحاسوب",
    loading: "جارٍ قراءة مساحات العمل…",
    "cta.new": "مساحة عمل جديدة",
    "cta.newReview": "مراجعة جديدة",
    "cta.open": "فتح",
    openNow: "مفتوحة الآن",
    "table.caption": "مساحات العمل في {root}",
    "table.title": "العنوان والمجلد",
    "table.status": "الحالة",
    "table.lastActivity": "آخر نشاط",
    "table.action": "إجراء",
    "status.noCorpus": "لا يوجد متن بعد",
    "status.corpusAccepted": "قُبل المتن",
    "status.screening": "الفرز جارٍ",
    "status.published": "منشور",
    "status.publishedChanged": "منشور، مع قرارات بعده",
    untitled: "بلا عنوان",
    never: "لا نشاط بعد",
    "create.label": "مساحة عمل جديدة",
    "create.titleField": "عنوان المراجعة",
    "create.titleHelp": "يُسمّى المجلد باسم العنوان.",
    "create.folderCaption": "المجلد: {path}",
    "create.folderEmpty": "اكتب عنوانًا لترى مجلده.",
    "create.submit": "إنشاء",
    "create.cancel": "إلغاء",
    "create.submitting": "جارٍ إنشاء مساحة العمل…",
    "create.placeholderProtocol": "بروتوكول مؤقت. شغّل معالج التأسيس من الطرفية لاستبداله.",
    "next.title": "أُنشئت مساحة العمل",
    "next.body": "يبدأ الفرز من متن مقبول. اقبله من الطرفية:",
    "next.copy": "نسخ الأمر",
    "next.copied": "نُسخ",
    "next.open": "فتحها",
    "empty.title": "لا توجد مساحات عمل بعد",
    "empty.body": "ستظهر مراجعاتك هنا. لاستخدام مجلد موجود لديك، شغّل التطبيق عليه من الطرفية.",
    opening: "جارٍ فتح {title}…",
    "skipped.count": "{n} مجلدات مُتخطّاة",
    "skipped.show": "إظهارها",
    "skipped.hide": "إخفاؤها",
    "invalid.reason.noProject": "لا يوجد project.json",
    "invalid.reason.noProtocol": "لا يوجد protocol.json",
    "invalid.reason.noJournal": "لا يوجد سجل تدقيق",
    "invalid.reason.unreadable": "تتعذّر قراءة المجلد",
    notAWorkspace: "ليست مساحة عمل: {reason}",
    "busy.run": "يجري تشغيل للوكيل في مساحة العمل هذه. فتح مساحة أخرى يعيد تشغيل التطبيق ويوقفه.",
    "busy.pairing": "توجد موافقة مفتوحة. فتح مساحة أخرى يعيد تشغيل التطبيق ويضيّعها.",
    "busy.goHome": "الانتقال إلى صفحة الفرز الرئيسية",
    "phone.desktopOnly": "اختر مساحة العمل من حاسوبك. يعمل الهاتف على المساحة المفتوحة.",
    "phone.toScreening": "الانتقال إلى الفرز",
    footer: "هذا الحاسوب · المحرك يعمل · {root}",
  },
} as const;

export type WorkspacesCopyKey = keyof (typeof COPY)["en"];
export const WORKSPACES_COPY: Record<Locale, Record<WorkspacesCopyKey, string>> = COPY;

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`workspaces copy needs {${k}}`);
    return String(values[k]);
  });
}

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

type Refusal = { code: string; message: string; details?: unknown };

function refusalOf(error: unknown): Refusal {
  return isScreeningApiError(error)
    ? { code: error.code, message: error.serverMessage, details: error.serverDetails }
    : { code: "ENGINE_UNREACHABLE", message: "" };
}

/** The reason a folder is not a workspace, from the engine's `invalid_reason`. */
function reasonText(t: (key: WorkspacesCopyKey) => string, reason: string | undefined): string {
  if (!reason || reason === "unreadable") return t("invalid.reason.unreadable");
  const parts: string[] = [];
  if (reason.includes("project.json")) parts.push(t("invalid.reason.noProject"));
  if (reason.includes("protocol.json")) parts.push(t("invalid.reason.noProtocol"));
  if (reason.includes("journal")) parts.push(t("invalid.reason.noJournal"));
  return parts.length > 0 ? parts.join(", ") : reason;
}

function statusOf(item: WorkspaceItem): { role: "include" | "unclear" | "blocked"; key: WorkspacesCopyKey } {
  // The engine's status (M6-beta) decides; the older fields stay as a fallback.
  if (item.status === "PUBLISHED") return { role: "include", key: "status.published" };
  if (item.status === "PUBLISHED_CHANGED") return { role: "unclear", key: "status.publishedChanged" };
  if (item.status === "SCREENING") return { role: "include", key: "status.screening" };
  if (item.status === "CORPUS_ACCEPTED") return { role: "include", key: "status.corpusAccepted" };
  if (item.status === "NEW") return { role: "unclear", key: "status.noCorpus" };
  if (item.screening_started) return { role: "include", key: "status.screening" };
  if (item.has_corpus) return { role: "include", key: "status.corpusAccepted" };
  return { role: "unclear", key: "status.noCorpus" };
}

function acceptCommand(path: string): string {
  return `nexus-scholar accept-corpus --workspace "${path}"`;
}

export function WorkspacesScreen({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: WorkspacesCopyKey, values?: Record<string, string | number>) => fill(WORKSPACES_COPY[locale][key], values), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [listing, setListing] = useState<WorkspaceListing | null>(null);
  const [loadError, setLoadError] = useState<Refusal | null>(null);
  const [showInvalid, setShowInvalid] = useState(false);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [created, setCreated] = useState<CreatedWorkspace | null>(null);
  const [copied, setCopied] = useState(false);
  const [opening, setOpening] = useState<string | null>(null);
  const titleField = useRef<HTMLInputElement>(null);
  const nextHeading = useRef<HTMLHeadingElement>(null);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      setListing(await getWorkspaces(origin, showInvalid));
    } catch (error) {
      setLoadError(refusalOf(error));
    }
  }, [origin, showInvalid]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (creating) titleField.current?.focus();
  }, [creating]);

  useEffect(() => {
    if (created) nextHeading.current?.focus();
  }, [created]);

  // `n` opens the create panel (spec 00, Keyboard), unless the reader is typing.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (event.key !== "n" || event.ctrlKey || event.metaKey || event.altKey) return;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) return;
      event.preventDefault();
      setCreating(true);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const closeCreate = () => {
    setCreating(false);
    setTitle("");
    document.getElementById("new-workspace")?.focus();
  };

  const submit = async () => {
    if (busy) return;
    setBusy(true);
    setRefusal(null);
    try {
      const made = await createWorkspace(origin, title.trim());
      setCreated(made);
      setCreating(false);
      setTitle("");
      await load();
    } catch (error) {
      setRefusal(refusalOf(error));
    } finally {
      setBusy(false);
    }
  };

  const open = async (item: { slug: string; title: string | null; path: string }) => {
    setRefusal(null);
    try {
      const answer = await openWorkspace(origin, item.slug);
      const landing = `/${locale}/screening/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`;
      if (!answer.restarting) {
        window.location.assign(landing);
        return;
      }
      setOpening(item.title ?? item.slug);
      // The engine restarts on the folder; wait until the new one answers for it.
      for (let attempt = 0; attempt < 120; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        try {
          if ((await currentWorkspacePath(origin)) === answer.path) {
            window.location.assign(landing);
            return;
          }
        } catch {
          // The old engine has stopped and the new one is not up yet.
        }
      }
      setOpening(null);
      setRefusal({ code: "ENGINE_UNREACHABLE", message: "" });
    } catch (error) {
      setRefusal(refusalOf(error));
    }
  };

  const root = listing?.root ?? "";
  const slug = previewSlug(title);
  const busyNow = listing ? listing.busy.run_active || listing.busy.pairing_open : false;
  const valid = listing?.items.filter((i) => i.valid) ?? [];
  const invalid = listing?.items.filter((i) => !i.valid) ?? [];
  const busyCode = refusal?.code === "WORKSPACE_BUSY";
  const busyDetails = (busyCode ? refusal?.details : listing?.busy) as { run_active?: boolean; pairing_open?: boolean } | undefined;

  const desktop = (() => {
    if (loadError) return <StateCard pageHeading locale={locale} code={loadError.code} message={loadError.message} consoleOrigin={origin} onRetry={() => void load()} />;
    if (!listing) return <p role="status" className="text-ink-muted">{t("loading")}</p>;
    if (opening) return <p role="status" className="text-lg text-ink" data-opening>{t("opening", { title: opening })}</p>;
    return (
      <div className="space-y-6">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
          <h1 className="mt-2 font-display text-3xl text-ink">{t("title")}</h1>
          <p className="mt-2 max-w-2xl text-ink-muted">{fill(WORKSPACES_COPY[locale].lede, { root: "⁨" + root + "⁩" })}</p>
          <p className="mt-2 inline-block border border-rule px-2 py-0.5 text-xs text-ink-muted">{t("liveStamp")}</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Button variant="primary" id="new-workspace" onClick={() => setCreating(true)} aria-expanded={creating} aria-controls="create-panel">
              {t("cta.new")}
            </Button>
            {/* M4b: a review set up step by step (inception specs 01–08), not only a placeholder protocol. */}
            <a
              href={`/${locale}/inception/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`}
              className="inline-flex min-h-11 items-center justify-center rounded-md border border-rule-strong bg-leaf px-4 text-[0.9375rem] font-medium leading-[1.375rem] text-ink hover:bg-leaf-raised"
              data-new-review
            >
              {t("cta.newReview")}
            </a>
          </div>
        </header>

        {creating ? (
          <section id="create-panel" aria-labelledby="create-label" className="rounded-lg border border-rule bg-leaf p-5">
            <h2 id="create-label" className="font-semibold text-ink">{t("create.label")}</h2>
            <form
              className="mt-3 space-y-2"
              onSubmit={(event) => {
                event.preventDefault();
                void submit();
              }}
              onKeyDown={(event) => {
                if (event.key === "Escape") closeCreate();
              }}
            >
              <label htmlFor="workspace-title" className="block text-sm text-ink">{t("create.titleField")}</label>
              <input
                id="workspace-title"
                ref={titleField}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                aria-describedby="workspace-folder workspace-help"
                className="block min-h-11 w-full max-w-xl rounded-md border border-rule bg-paper px-2 text-ink"
              />
              <p id="workspace-help" className="text-xs text-ink-muted">{t("create.titleHelp")}</p>
              <p id="workspace-folder" aria-live="polite" className="text-sm text-ink-muted" data-folder>
                {slug ? fill(WORKSPACES_COPY[locale]["create.folderCaption"], { path: "" }) : t("create.folderEmpty")}
                {slug ? <bdi dir="ltr">{`${root}${root.includes("\\") ? "\\" : "/"}${slug}`}</bdi> : null}
              </p>
              <div className="flex gap-3 pt-1">
                <Button variant="primary" type="submit" disabled={busy || !title.trim()}>
                  {busy ? t("create.submitting") : t("create.submit")}
                </Button>
                <Button onClick={closeCreate}>{t("create.cancel")}</Button>
              </div>
            </form>
          </section>
        ) : null}

        {refusal ? (
          <div data-refusal={refusal.code}>
            <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} onRetry={() => void load()} command={refusal.code === "RESTART_UNSUPPORTED" ? "uv run nexus-scholar ui" : undefined} />
          </div>
        ) : null}

        {created ? (
          <section aria-labelledby="next-step" className="rounded-lg border border-rule bg-leaf p-5" data-next-step>
            <h2 id="next-step" ref={nextHeading} tabIndex={-1} className="font-semibold text-ink">{t("next.title")}</h2>
            <p className="mt-1 text-ink">{t("next.body")}</p>
            <p className="mt-2 rounded-md bg-paper p-2 font-mono text-sm text-ink">
              <bdi dir="ltr">{acceptCommand(created.path)}</bdi>
            </p>
            <div className="mt-2 flex flex-wrap gap-3">
              <Button
                onClick={() => {
                  void navigator.clipboard?.writeText(acceptCommand(created.path)).then(() => setCopied(true));
                }}
              >
                <span aria-live="polite">{copied ? t("next.copied") : t("next.copy")}</span>
              </Button>
              <Button onClick={() => void open({ slug: created.slug, title: null, path: created.path })}>{t("next.open")}</Button>
            </div>
            <p className="mt-3 border border-dashed border-rule p-2 text-sm text-ink-muted" data-draft>{t("create.placeholderProtocol")}</p>
          </section>
        ) : null}

        {busyNow || busyCode ? (
          <p className="text-sm text-ink" data-busy>
            {busyDetails?.run_active ? t("busy.run") : t("busy.pairing")}{" "}
            <a className="text-brand underline" href={`/${locale}/screening/home/`}>{t("busy.goHome")}</a>
          </p>
        ) : null}

        {valid.length === 0 && invalid.length === 0 ? (
          <section className="rounded-lg border border-rule bg-leaf p-5" data-empty>
            <h2 className="font-semibold text-ink">{t("empty.title")}</h2>
            <p className="mt-1 text-ink-muted">{t("empty.body")}</p>
          </section>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-rule bg-leaf">
            <table className="w-full text-start text-sm">
              <caption className="sr-only">{fill(WORKSPACES_COPY[locale]["table.caption"], { root })}</caption>
              <thead>
                <tr className="border-b border-rule text-ink-muted">
                  <th scope="col" className="p-3 text-start font-medium">{t("table.title")}</th>
                  <th scope="col" className="p-3 text-start font-medium">{t("table.status")}</th>
                  <th scope="col" className="p-3 text-start font-medium">{t("table.lastActivity")}</th>
                  <th scope="col" className="p-3 text-start font-medium">{t("table.action")}</th>
                </tr>
              </thead>
              <tbody>
                {valid.map((item) => {
                  const status = statusOf(item);
                  return (
                    <tr key={item.path} className="border-b border-rule last:border-0" aria-current={item.is_current ? "true" : undefined} data-row={item.slug}>
                      <td className="p-3">
                        <p className="font-medium text-ink">{item.title ?? t("untitled")}</p>
                        <p className="text-xs text-ink-muted"><bdi dir="ltr">{item.path}</bdi></p>
                      </td>
                      <td className="p-3">
                        <span className="flex flex-wrap items-center gap-2">
                          <DecisionBadge role={status.role}>{t(status.key)}</DecisionBadge>
                          {/* A status chip, never a wrapped button (M6-beta, review U-3). */}
                          {item.is_current ? (
                            <span className="whitespace-nowrap rounded-sm border border-brand px-2 py-0.5 text-xs text-brand" data-open-now>
                              {t("openNow")}
                            </span>
                          ) : null}
                        </span>
                      </td>
                      <td className="p-3 text-ink-muted">
                        {item.last_event?.at ? (
                          <><bdi dir="ltr">{item.last_event.at.slice(0, 16).replace("T", " ")}</bdi> · <bdi dir="ltr">{item.last_event.action}</bdi></>
                        ) : t("never")}
                      </td>
                      <td className="p-3">
                        {item.is_current ? (
                          <a className="inline-flex min-h-11 items-center whitespace-nowrap text-brand underline" href={`/${locale}/screening/home/`}>
                            {t("busy.goHome")}
                          </a>
                        ) : (
                          <Button disabled={busyNow} onClick={() => void open(item)}>
                            {t("cta.open")}
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {invalid.map((item) => (
                  <tr key={item.path} className="border-b border-rule text-ink-muted last:border-0" aria-disabled="true" data-invalid={item.slug}>
                    <td className="p-3">
                      <p>{item.slug}</p>
                      <p className="text-xs"><bdi dir="ltr">{item.path}</bdi></p>
                    </td>
                    <td className="p-3" colSpan={3}>{t("notAWorkspace", { reason: reasonText(t, item.invalid_reason) })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {listing.skipped_count > 0 ? (
          <p className="text-sm text-ink-muted" data-skipped>
            {t("skipped.count", { n: formatNumber(locale, listing.skipped_count) })} ·{" "}
            <Button variant="quiet" className="px-0" onClick={() => setShowInvalid((v) => !v)}>
              {showInvalid ? t("skipped.hide") : t("skipped.show")}
            </Button>
          </p>
        ) : null}

        <p className="text-xs text-ink-muted">{fill(WORKSPACES_COPY[locale].footer, { root: "⁨" + root + "⁩" })}</p>
      </div>
    );
  })();

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <section className="rounded-lg border border-rule bg-leaf p-5 sm:hidden" data-phone>
        {/* On a phone this sentence is the whole screen, so it is the page's h1. */}
        <h1 className="text-base font-normal text-ink">{t("phone.desktopOnly")}</h1>
        <a className="mt-3 inline-flex min-h-11 items-center text-brand underline" href={`/${locale}/screening/home/`}>{t("phone.toScreening")}</a>
      </section>
      <div className="hidden sm:block">{desktop}</div>
    </div>
  );
}
