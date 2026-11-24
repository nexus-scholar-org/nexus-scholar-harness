"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { StateCard } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import {
  AI_KEYS,
  DATABASE_KEYS,
  chooseFolder,
  finishSetup,
  getSettings,
  removeKey,
  saveContactEmail,
  saveKey,
  setElsewhere,
  type KeyName,
  type SettingSource,
  type SettingsView,
} from "@/lib/settings-api";
import { SETTING_VARIABLES, settingsT, type SettingsCopyKey } from "@/lib/settings-copy";

/**
 * The Settings screen and first-run setup (M13 Part B;
 * `docs/ux/shared/final/05-settings.md`, FINAL). Three parts, each saved on its
 * own: the contact e-mail, the keys, the reviews folder. The engine decides
 * everything (which value wins, whether a keychain exists, whether setup is
 * pending); the page prints what it answers.
 *
 * A key is never kept on the page: the field is emptied the moment its request
 * is sent, and no answer holds a key's value. The one exception is the
 * keychain confirmation, which keeps the typed value in memory for its one
 * resend and drops it on either answer.
 */

type Refusal = { code: string; message: string; details?: unknown };

function refusalOf(error: unknown): Refusal {
  return isScreeningApiError(error)
    ? { code: error.code, message: error.serverMessage, details: error.serverDetails }
    : { code: "ENGINE_UNREACHABLE", message: "" };
}

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

function setupRequested(): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("setup") === "1";
}

const FIELD = "block min-h-11 w-full max-w-xl rounded-md border border-rule bg-paper px-2 text-ink";
const CARD = "rounded-lg border border-rule bg-leaf p-5";

const KEY_LABEL: Record<KeyName, SettingsCopyKey> = {
  openalex: "settings.key.openalex.label",
  semanticscholar: "settings.key.semanticscholar.label",
  anthropic: "settings.key.anthropic.label",
  openai_compatible: "settings.key.openai_compatible.label",
  gemini: "settings.key.gemini.label",
};
const KEY_HELP: Partial<Record<KeyName, SettingsCopyKey>> = {
  openalex: "settings.key.openalex.help",
  semanticscholar: "settings.key.semanticscholar.help",
};

export function SettingsScreen({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: SettingsCopyKey, values?: Record<string, string | number>) => settingsT(locale, key, values), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [view, setView] = useState<SettingsView | null>(null);
  const [loadError, setLoadError] = useState<Refusal | null>(null);
  const [asOf, setAsOf] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [announce, setAnnounce] = useState("");
  const [wantsSetup, setWantsSetup] = useState(false);
  const [restarting, setRestarting] = useState<string | null>(null);
  const emailField = useRef<HTMLInputElement>(null);
  const restartLine = useRef<HTMLParagraphElement>(null);

  const apply = useCallback((answer: SettingsView) => {
    setView(answer);
    setOffline(false);
    setAsOf(new Date().toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" }));
  }, [locale]);

  const load = useCallback(async () => {
    try {
      apply(await getSettings(origin));
      setLoadError(null);
    } catch (error) {
      const refusal = refusalOf(error);
      setLoadError(refusal);
      if (refusal.code === "ENGINE_UNREACHABLE" || refusal.code === "CONSOLE_UNREACHABLE" || refusal.code === "CONSOLE_TIMEOUT") setOffline(true);
    }
  }, [apply, origin]);

  useEffect(() => {
    setWantsSetup(setupRequested());
    void load();
    const onFocus = () => void load();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [load]);

  // The engine's `setup` wins over `?setup=1` (the query is only a hint).
  const setupMode = wantsSetup && view?.setup === "pending";
  useEffect(() => {
    if (wantsSetup && view && view.setup !== "pending") {
      const url = new URL(window.location.href);
      url.searchParams.delete("setup");
      window.history.replaceState(null, "", url.toString());
      setWantsSetup(false);
    }
  }, [wantsSetup, view]);

  // First run: the e-mail field is the first thing needed.
  const focused = useRef(false);
  useEffect(() => {
    if (setupMode && view && !focused.current) {
      focused.current = true;
      emailField.current?.focus();
    }
  }, [setupMode, view]);

  useEffect(() => {
    if (restarting) restartLine.current?.focus();
  }, [restarting]);

  const disabled = offline;

  if (!view && loadError?.code === "TOKEN_SCOPE_REFUSED") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6" data-settings-phone>
        <div className={CARD}>
          <p className="text-ink">{t("settings.phone.desktopOnly")}</p>
          <a className="mt-3 inline-flex min-h-11 items-center text-brand underline" href={`/${locale}/screening/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`}>{t("settings.phone.toScreening")}</a>
        </div>
      </div>
    );
  }
  if (!view && loadError) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <StateCard pageHeading locale={locale} code={loadError.code} message={loadError.message} consoleOrigin={origin} onRetry={() => void load()} />
      </div>
    );
  }
  if (!view) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-8 sm:px-6" aria-busy="true" data-settings-loading>
        <h1 className="font-display text-3xl text-ink">{t(wantsSetup ? "settings.title.setup" : "settings.title.settings")}</h1>
        <p role="status" className="text-ink-muted">{t("settings.loading")}</p>
        {[0, 1, 2].map((n) => (
          <div key={n} className={`${CARD} h-28 animate-pulse motion-reduce:animate-none`} />
        ))}
      </div>
    );
  }

  const waitForFolder = async (path: string) => {
    setRestarting(path);
    setAnnounce(t("settings.folder.restarting", { path }));
    for (let attempt = 0; attempt < 120; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      try {
        const answer = await getSettings(origin);
        if (answer.workspaces_root.path === path) {
          window.location.reload();
          return;
        }
      } catch {
        // The old engine has stopped and the new one is not up yet.
      }
    }
    setRestarting(null);
    setLoadError({ code: "ENGINE_UNREACHABLE", message: "" });
    setOffline(true);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6" data-settings data-mode={setupMode ? "setup" : "settings"}>
      <p role="status" aria-live="polite" className="sr-only" data-announce>{announce}</p>
      <header>
        {setupMode ? (
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("settings.eyebrow.setup")}</p>
        ) : null}
        <h1 className="mt-2 font-display text-3xl text-ink">{t(setupMode ? "settings.title.setup" : "settings.title.settings")}</h1>
        <p className="mt-2 max-w-2xl text-ink-muted">{t(setupMode ? "settings.lede.setup" : "settings.lede.settings")}</p>
        {setupMode ? <p className="mt-2 max-w-2xl text-sm text-ink-muted" data-first-run-note>{t("settings.firstRunNote")}</p> : null}
      </header>

      {offline ? (
        <div data-offline>
          <StateCard locale={locale} code="ENGINE_UNREACHABLE" consoleOrigin={origin} onRetry={() => void load()} />
          {asOf ? <p className="mt-2 text-sm text-ink-muted">{t("settings.liveAsOf", { time: asOf })}</p> : null}
        </div>
      ) : null}

      {restarting ? (
        <p role="status" ref={restartLine} tabIndex={-1} className="text-lg text-ink" data-restarting>
          {settingsT(locale, "settings.folder.restarting", { path: "⁨" + restarting + "⁩" })}
        </p>
      ) : (
        <>
          <EmailCard locale={locale} origin={origin} view={view} disabled={disabled} setupMode={setupMode} field={emailField} onAnswer={apply} onAnnounce={setAnnounce} onRefresh={() => void load()} />
          <KeysCard locale={locale} origin={origin} view={view} disabled={disabled} onAnswer={apply} onAnnounce={setAnnounce} onRefresh={() => void load()} />
          <FolderCard locale={locale} origin={origin} view={view} disabled={disabled} onRestart={(path) => void waitForFolder(path)} />
          {setupMode ? (
            <SetupActions locale={locale} origin={origin} view={view} disabled={disabled} />
          ) : (
            <p>
              <a className="inline-flex min-h-11 items-center text-brand underline" href={`/${locale}/workspaces/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`} data-back>
                {t("settings.back")}
              </a>
            </p>
          )}
        </>
      )}
    </div>
  );
}

function SourceLine({ locale, source, variable, file, id }: Readonly<{ locale: Locale; source: SettingSource | null; variable?: string; file?: string; id?: string }>) {
  if (!source) return null;
  const words =
    source === "environment"
      ? settingsT(locale, "settings.source.environment", { name: variable ?? "" })
      : source === "file"
        ? settingsT(locale, "settings.source.file", { path: "⁨" + (file ?? "") + "⁩" })
        : settingsT(locale, `settings.source.${source}` as SettingsCopyKey);
  return (
    <p id={id} className="mt-1 text-sm text-ink-muted [overflow-wrap:anywhere]" data-source={source}>
      {words}
    </p>
  );
}

function RowError({ refusal, sentence }: Readonly<{ locale: Locale; refusal: Refusal; sentence: string }>) {
  return (
    <div role="alert" className="mt-2 text-sm text-blocked" data-refusal={refusal.code}>
      <p>{sentence}</p>
      <p className="font-mono text-xs" dir="ltr">{refusal.code}</p>
    </div>
  );
}

type CardProps = {
  locale: Locale;
  origin: string;
  view: SettingsView;
  disabled: boolean;
  onAnswer: (answer: SettingsView) => void;
  onAnnounce: (words: string) => void;
  onRefresh: () => void;
};

function EmailCard({ locale, origin, view, disabled, setupMode, field, onAnswer, onAnnounce, onRefresh }: CardProps & { setupMode: boolean; field: React.RefObject<HTMLInputElement | null> }) {
  const t = (key: SettingsCopyKey, values?: Record<string, string | number>) => settingsT(locale, key, values);
  const heading = useId();
  const help = useId();
  const source = useId();
  const elsewhere = setElsewhere(view.contact_email.source);
  const [draft, setDraft] = useState(view.contact_email.value ?? "");
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  useEffect(() => setDraft(view.contact_email.value ?? ""), [view.contact_email.value]);

  const send = async (value: string) => {
    setBusy(true);
    setRefusal(null);
    try {
      onAnswer(await saveContactEmail(origin, value));
      onAnnounce(t(value ? "settings.email.saved" : "settings.email.removed"));
    } catch (error) {
      const r = refusalOf(error);
      setRefusal(r);
      if (r.code === "SETTING_SET_ELSEWHERE") onRefresh();
      field.current?.focus();
    } finally {
      setBusy(false);
    }
  };

  return (
    <section aria-labelledby={heading} className={CARD} data-card="email">
      <h2 id={heading} className="font-semibold text-ink">{t("settings.email.heading")}</h2>
      {setupMode ? <p className="mt-1 text-sm font-semibold text-ink">{t("settings.email.required")}</p> : null}
      <p id={help} className="mt-1 text-sm text-ink-muted">{t("settings.email.help")}</p>
      {elsewhere ? (
        <div className="mt-3">
          <p className="text-ink [overflow-wrap:anywhere]" dir="ltr">{view.contact_email.value}</p>
          <SourceLine locale={locale} source={view.contact_email.source} variable={SETTING_VARIABLES.contact_email} id={source} />
        </div>
      ) : (
        <form
          className="mt-3 space-y-2"
          // The engine judges the address (SETTING_INVALID), never the browser's own check.
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            void send(draft.trim());
          }}
        >
          <label id="settings-email-label" htmlFor="settings-email" className="block text-sm text-ink">{t("settings.email.label")}</label>
          <input
            id="settings-email"
            ref={field}
            type="email"
            autoComplete="email"
            dir="ltr"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            aria-describedby={[help, view.contact_email.source ? source : ""].filter(Boolean).join(" ")}
            className={FIELD}
          />
          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={busy || disabled} aria-disabled={busy || disabled}>{busy ? t("settings.saving") : t("settings.email.save")}</Button>
            {view.contact_email.value ? (
              <Button variant="quiet" id="settings-email-remove" aria-labelledby="settings-email-remove settings-email-label" disabled={busy || disabled} onClick={() => void send("")}>{t("settings.email.remove")}</Button>
            ) : null}
          </div>
          <SourceLine locale={locale} source={view.contact_email.source} id={source} />
        </form>
      )}
      {refusal ? (
        <RowError
          locale={locale}
          refusal={refusal}
          sentence={refusal.code === "SETTING_INVALID" ? t("settings.refusal.SETTING_INVALID.email") : refusal.code === "SETTING_SET_ELSEWHERE" ? t("settings.elsewhere") : refusal.message}
        />
      ) : null}
    </section>
  );
}

function storeWords(locale: Locale, view: SettingsView): string {
  return view.key_store.kind === "file"
    ? settingsT(locale, "settings.store.file", { path: "⁨" + view.key_store.file + "⁩" })
    : settingsT(locale, "settings.store.keychain");
}

function KeysCard(props: CardProps) {
  const { locale, view } = props;
  const t = (key: SettingsCopyKey) => settingsT(locale, key);
  const heading = useId();
  return (
    <section aria-labelledby={heading} className={CARD} data-card="keys">
      <h2 id={heading} className="font-semibold text-ink">{t("settings.keys.heading")}</h2>
      <p className="mt-1 text-sm text-ink-muted [overflow-wrap:anywhere]" data-keys-where>{settingsT(locale, "settings.keys.where", { where: storeWords(locale, view) })}</p>
      {view.key_store.kind === "none" && !Object.values(view.keys).some((k) => k.set) ? (
        <p className="mt-1 text-sm text-ink" data-store-none>{t("settings.store.none")}</p>
      ) : null}
      <h3 className="mt-4 text-sm font-semibold text-ink">{t("settings.keys.group.databases")}</h3>
      <ul className="mt-2 space-y-4">
        {DATABASE_KEYS.map((name) => <KeyRow key={name} name={name} {...props} />)}
      </ul>
      <h3 className="mt-5 text-sm font-semibold text-ink">{t("settings.keys.group.ai")}</h3>
      <p className="text-sm text-ink-muted">{t("settings.keys.group.aiHelp")}</p>
      <ul className="mt-2 space-y-4">
        {AI_KEYS.map((name) => <KeyRow key={name} name={name} {...props} />)}
      </ul>
    </section>
  );
}

function KeyRow({ locale, origin, view, disabled, onAnswer, onAnnounce, onRefresh, name }: CardProps & { name: KeyName }) {
  const t = (key: SettingsCopyKey, values?: Record<string, string | number>) => settingsT(locale, key, values);
  const state = view.keys[name];
  const label = t(KEY_LABEL[name]);
  const fieldId = `settings-key-${name}`;
  const help = useId();
  const source = useId();
  const confirmHeading = useId();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  // The keychain confirmation keeps the typed value for its one resend only.
  const [confirm, setConfirm] = useState<{ value: string; file: string } | null>(null);
  const field = useRef<HTMLInputElement>(null);
  const replaceButton = useRef<HTMLButtonElement>(null);
  const confirmTitle = useRef<HTMLParagraphElement>(null);
  // Where focus goes once the row has re-rendered (the control that had it may be gone).
  const [focusTo, setFocusTo] = useState<"replace" | "field" | null>(null);
  const elsewhere = setElsewhere(state.source);
  const showField = !elsewhere && (!state.set || editing);
  const nameId = useId();
  const fieldLabelId = useId();
  const replaceId = useId();
  const removeId = useId();

  useEffect(() => {
    const target = focusTo === "replace" ? replaceButton.current : focusTo === "field" ? field.current : null;
    if (target) {
      target.focus();
      setFocusTo(null);
    }
  });

  useEffect(() => {
    if (editing) field.current?.focus();
  }, [editing]);
  useEffect(() => {
    if (confirm) confirmTitle.current?.focus();
  }, [confirm]);

  const send = async (value: string, useFile: boolean) => {
    setBusy(true);
    setRefusal(null);
    setDraft(""); // the key leaves the page with the request
    try {
      onAnswer(await saveKey(origin, name, value, useFile));
      setEditing(false);
      setConfirm(null);
      onAnnounce(t("settings.key.saved", { label }));
      setFocusTo("replace");
    } catch (error) {
      const r = refusalOf(error);
      if (r.code === "KEYCHAIN_UNAVAILABLE" && !useFile) {
        const file = (r.details as { file?: string } | undefined)?.file ?? view.key_store.file;
        setConfirm({ value, file });
      } else {
        setConfirm(null);
        setRefusal(r);
        if (r.code === "SETTING_SET_ELSEWHERE") onRefresh();
        setTimeout(() => field.current?.focus(), 0);
      }
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    setRefusal(null);
    try {
      onAnswer(await removeKey(origin, name));
      onAnnounce(t("settings.key.removed", { label }));
      setFocusTo("field");
    } catch (error) {
      setRefusal(refusalOf(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <li data-key-row={name}>
      <p className="font-medium text-ink">
        <span id={nameId}>{label}</span>{" "}
        <DecisionBadge role={state.set ? "include" : "unclear"}>{t(state.set ? "settings.key.set" : "settings.key.notSet")}</DecisionBadge>
      </p>
      {KEY_HELP[name] ? <p id={help} className="text-sm text-ink-muted">{t(KEY_HELP[name]!)}</p> : null}
      {confirm ? (
        <div className="mt-2 rounded-md border border-rule p-3" data-keychain-confirm>
          <p ref={confirmTitle} tabIndex={-1} className="text-ink">
            {settingsT(locale, "settings.keychain.ask", { path: "" })}
            <bdi dir="ltr" className="font-mono text-sm [overflow-wrap:anywhere]">{confirm.file}</bdi>
          </p>
          <div className="mt-2 flex flex-wrap gap-3">
            <Button disabled={busy} onClick={() => void send(confirm.value, true)}>{t("settings.keychain.yes")}</Button>
            <Button
              variant="quiet"
              disabled={busy}
              onClick={() => {
                setConfirm(null);
                setFocusTo("field");
              }}
            >
              {t("settings.keychain.no")}
            </Button>
          </div>
        </div>
      ) : showField ? (
        <form
          className="mt-2 flex flex-wrap items-end gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            void send(draft, false);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape" && editing) {
              setEditing(false);
              setDraft("");
              setFocusTo("replace");
            }
          }}
        >
          <div className="min-w-0 flex-1">
            <label id={fieldLabelId} htmlFor={fieldId} className="block text-sm text-ink">{t("settings.key.field")}</label>
            <input
              id={fieldId}
              ref={field}
              name={`nexus-key-${name}`}
              type="password"
              autoComplete="off"
              autoCapitalize="off"
              spellCheck={false}
              dir="ltr"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              aria-labelledby={`${fieldLabelId} ${nameId}`}
              aria-describedby={[KEY_HELP[name] ? help : "", state.source ? source : ""].filter(Boolean).join(" ") || undefined}
              className={FIELD}
            />
          </div>
          <Button type="submit" disabled={busy || disabled} aria-disabled={busy || disabled}>{busy ? t("settings.saving") : t("settings.key.save")}</Button>
          {editing ? (
            <Button
              variant="quiet"
              onClick={() => {
                setEditing(false);
                setDraft("");
                setFocusTo("replace");
              }}
            >
              {t("settings.key.cancel")}
            </Button>
          ) : null}
        </form>
      ) : !elsewhere ? (
        <div className="mt-2 flex flex-wrap gap-3">
          <Button ref={replaceButton} id={replaceId} aria-labelledby={`${replaceId} ${nameId}`} disabled={busy || disabled} onClick={() => setEditing(true)}>{t("settings.key.replace")}</Button>
          <Button variant="quiet" id={removeId} aria-labelledby={`${removeId} ${nameId}`} disabled={busy || disabled} onClick={() => void remove()}>{t("settings.key.remove")}</Button>
        </div>
      ) : null}
      <SourceLine locale={locale} source={state.source} variable={state.variable} file={view.key_store.file} id={source} />
      {state.set && !elsewhere && AI_KEYS.includes(name) ? <p className="text-xs text-ink-muted">{t("settings.key.removeNote")}</p> : null}
      {refusal ? (
        <RowError
          locale={locale}
          refusal={refusal}
          sentence={refusal.code === "SETTING_INVALID" ? t("settings.refusal.SETTING_INVALID.key") : refusal.code === "SETTING_SET_ELSEWHERE" ? t("settings.elsewhere") : refusal.message}
        />
      ) : null}
    </li>
  );
}

function FolderCard({ locale, origin, view, disabled, onRestart }: Readonly<{ locale: Locale; origin: string; view: SettingsView; disabled: boolean; onRestart: (path: string) => void }>) {
  const t = (key: SettingsCopyKey, values?: Record<string, string | number>) => settingsT(locale, key, values);
  const heading = useId();
  const [dialog, setDialog] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const change = useRef<HTMLButtonElement>(null);
  const root = view.workspaces_root;
  const pinned = setElsewhere(root.source);

  const choose = async () => {
    setDialog(true);
    setRefusal(null);
    try {
      const answer = await chooseFolder(origin);
      setDialog(false);
      if (answer.chosen && answer.restarting) {
        onRestart(answer.chosen);
        return;
      }
      setTimeout(() => change.current?.focus(), 0);
    } catch (error) {
      setDialog(false);
      setRefusal(refusalOf(error));
      setTimeout(() => change.current?.focus(), 0);
    }
  };

  const sentence = (r: Refusal): string | null => {
    if (r.code === "FOLDER_DIALOG_UNAVAILABLE") {
      const hint = view.started_as === "terminal" ? t("settings.refusal.FOLDER_DIALOG_UNAVAILABLE.hint") : "";
      return t("settings.refusal.FOLDER_DIALOG_UNAVAILABLE", { hint }).trim();
    }
    if (r.code === "RESTART_UNSUPPORTED") return t("settings.refusal.RESTART_UNSUPPORTED");
    if (r.code === "SETTING_SET_ELSEWHERE") return t("settings.elsewhere");
    return null;
  };

  return (
    <section aria-labelledby={heading} className={CARD} data-card="folder">
      <h2 id={heading} className="font-semibold text-ink">{t("settings.folder.heading")}</h2>
      <p className="mt-2 font-mono text-sm text-ink [overflow-wrap:anywhere]" dir="ltr" data-folder-path>{root.path}</p>
      <SourceLine locale={locale} source={root.source} variable={SETTING_VARIABLES.workspaces_root} />
      <p className="mt-2 text-sm text-ink-muted">{t("settings.folder.help")}</p>
      {pinned ? null : (
        <div className="mt-3">
          <Button ref={change} disabled={dialog || disabled} aria-disabled={dialog || disabled} onClick={() => void choose()}>{t("settings.folder.change")}</Button>
          <p className="mt-1 text-xs text-ink-muted sm:hidden">{t("settings.folder.whereDialog")}</p>
          {dialog ? <p role="status" className="mt-2 text-ink" data-dialog-open>{t("settings.folder.dialogOpen")}</p> : null}
        </div>
      )}
      {refusal ? (
        sentence(refusal) !== null ? (
          <RowError locale={locale} refusal={refusal} sentence={sentence(refusal)!} />
        ) : (
          <div className="mt-3">
            <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} />
          </div>
        )
      ) : null}
    </section>
  );
}

function SetupActions({ locale, origin, view, disabled }: Readonly<{ locale: Locale; origin: string; view: SettingsView; disabled: boolean }>) {
  const t = (key: SettingsCopyKey) => settingsT(locale, key);
  const note = useId();
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const emailSaved = view.contact_email.value !== null;
  const workspaces = `/${locale}/workspaces/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`;

  const finish = async (choice: "done" | "later") => {
    setBusy(true);
    setRefusal(null);
    try {
      await finishSetup(origin, choice);
      window.location.assign(workspaces);
    } catch (error) {
      setRefusal(refusalOf(error));
      setBusy(false);
    }
  };

  return (
    <div className="space-y-2" data-setup-actions>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Button
          variant="primary"
          className={`w-full sm:w-auto ${emailSaved ? "" : "cursor-not-allowed opacity-60"}`}
          aria-disabled={!emailSaved || busy || disabled}
          aria-describedby={emailSaved ? undefined : note}
          onClick={() => {
            if (emailSaved && !busy && !disabled) void finish("done");
          }}
        >
          {t("settings.setup.done")}
        </Button>
        <Button className="w-full sm:w-auto" disabled={busy || disabled} onClick={() => void finish("later")}>{t("settings.setup.later")}</Button>
      </div>
      {emailSaved ? null : <p id={note} className="text-sm text-ink-muted">{t("settings.setup.doneNeedsEmail")}</p>}
      {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
    </div>
  );
}
