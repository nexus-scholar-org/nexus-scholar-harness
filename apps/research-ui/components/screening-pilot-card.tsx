"use client";

import { useCallback, useEffect, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, PRIMARY_LINK } from "@/components/ui/base";
import { StateCard } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import { drawPilot, getCriteria, getSummary, type CriteriaView, type PilotDraw, type Summary } from "@/lib/screening-v1";

/**
 * Prepare's pilot card (spec 13, state A; M11b part C). It shows once batches
 * exist: before a pilot, a size and the brand button "Draw a pilot of {n}"
 * (question 7, settled 2026-11-21); while a pilot is open, its progress; after
 * it, the way to its result. Every number is the engine's (`GET /summary`, the
 * draw's dry call); nothing is drawn before the confirmation.
 */

const COPY = {
  en: {
    title: "Pilot your criteria first",
    body: "Read a small random sample under your criteria before you screen everything. You see where a criterion is hard to judge, and you can reword it while little is decided.",
    size: "Records in the pilot",
    sizeHint: "20 to 100 records. About half an hour for 50.",
    draw: "Draw a pilot of {n}",
    skip: "Screen everything",
    inProgress: "Pilot in progress · {k} of {n} decided",
    complete: "Pilot complete · {k} of {n} decided",
    ended: "Pilot ended · {k} of {n} decided",
    continue: "Continue the pilot",
    soFar: "See the result so far",
    result: "See the result",
    more: "Pilot {n} more records",
    rest: "Screen the rest",
    recheck: "{n} records are shown again because a criterion changed.",
    openThem: "Open them",
    drawTitle: "Draw the pilot?",
    drawBody:
      "Draw {n} records at random from the {N} in your corpus? The app picks records you have not decided yet and records the random seed it used, so the draw can be repeated. Your decisions on them are kept apart and are not counted. These records come back in the main screening, where you screen them again without seeing your pilot decision.",
    drawLeft: "{left} records have no decision and are in no earlier pilot.",
    drawConfirm: "Draw the pilot",
    drawCancel: "Not now",
    fixed: "A batch is already approved, so the criteria are fixed. To change them after publication, start a new screening from this protocol.",
    protocolChanged: "Batches no longer match the protocol",
    loading: "Reading the pilot…",
  },
  fr: {
    title: "Pilotez d'abord vos critères",
    body: "Lisez un petit échantillon aléatoire selon vos critères avant de tout trier. Vous voyez où un critère est difficile à juger, et vous pouvez le reformuler tant que peu est décidé.",
    size: "Notices dans le pilote",
    sizeHint: "De 20 à 100 notices. Environ une demi-heure pour 50.",
    draw: "Tirer un pilote de {n}",
    skip: "Tout trier",
    inProgress: "Pilote en cours · {k} sur {n} décidées",
    complete: "Pilote terminé · {k} sur {n} décidées",
    ended: "Pilote arrêté · {k} sur {n} décidées",
    continue: "Continuer le pilote",
    soFar: "Voir le résultat à ce stade",
    result: "Voir le résultat",
    more: "Piloter {n} notices de plus",
    rest: "Trier le reste",
    recheck: "{n} notices sont présentées à nouveau parce qu'un critère a changé.",
    openThem: "Les ouvrir",
    drawTitle: "Tirer le pilote ?",
    drawBody:
      "Tirer au hasard {n} notices parmi les {N} de votre corpus ? L'application choisit des notices que vous n'avez pas encore décidées et enregistre la graine aléatoire utilisée, pour que le tirage puisse être refait. Vos décisions sur elles sont gardées à part et ne sont pas comptées. Ces notices reviennent dans le tri principal, où vous les triez à nouveau sans voir votre décision du pilote.",
    drawLeft: "{left} notices n'ont pas de décision et ne sont dans aucun pilote antérieur.",
    drawConfirm: "Tirer le pilote",
    drawCancel: "Pas maintenant",
    fixed: "Un lot est déjà approuvé, les critères sont donc figés. Pour les changer après publication, commencez un nouveau tri à partir de ce protocole.",
    protocolChanged: "Les lots ne correspondent plus au protocole",
    loading: "Lecture du pilote…",
  },
  ar: {
    title: "جرّب معاييرك أولًا",
    body: "اقرأ عينة عشوائية صغيرة وفق معاييرك قبل فرز كل شيء. ترى أين يصعب الحكم على معيار، ويمكنك إعادة صياغته ما دام القليل قد حُسم.",
    size: "عدد السجلات في التجربة",
    sizeHint: "من 20 إلى 100 سجل. نحو نصف ساعة لـ 50.",
    draw: "اسحب تجربة من {n}",
    skip: "افرز الكل",
    inProgress: "تجربة جارية · {k} من {n} محسومة",
    complete: "اكتملت التجربة · {k} من {n} محسومة",
    ended: "انتهت التجربة · {k} من {n} محسومة",
    continue: "تابع التجربة",
    soFar: "اعرض النتيجة حتى الآن",
    result: "اعرض النتيجة",
    more: "جرّب {n} سجلات أخرى",
    rest: "افرز الباقي",
    recheck: "تُعرض {n} سجلات مرة أخرى لأن معيارًا تغيّر.",
    openThem: "افتحها",
    drawTitle: "سحب التجربة؟",
    drawBody:
      "اسحب {n} سجلًا عشوائيًا من أصل {N} في مجموعتك؟ يختار التطبيق سجلات لم تحسمها بعد ويسجّل البذرة العشوائية المستخدمة، فيمكن إعادة السحب. تُحفظ قراراتك عليها جانبًا ولا تُحتسب. تعود هذه السجلات إلى الفرز الرئيسي، حيث تفرزها من جديد دون أن ترى قرارك في التجربة.",
    drawLeft: "{left} سجلًا بلا قرار وليست في أي تجربة سابقة.",
    drawConfirm: "اسحب التجربة",
    drawCancel: "ليس الآن",
    fixed: "اعتُمدت دفعة بالفعل، فالمعايير ثابتة. لتغييرها بعد النشر، ابدأ فرزًا جديدًا من هذا البروتوكول.",
    protocolChanged: "الدفعات لم تعد تطابق البروتوكول",
    loading: "جارٍ قراءة التجربة…",
  },
} as const;

export type PilotCardKey = keyof (typeof COPY)["en"];
export const PILOT_CARD_COPY: Record<Locale, Record<PilotCardKey, string>> = COPY;

export function fill(template: string, values: Readonly<Record<string, string | number>>): string {
  return template.replace(/\{(\w+)\}/g, (_m, k: string) => (k in values ? String(values[k]) : `{${k}}`));
}

export function pilotHref(locale: Locale, pilotId: string, origin = ""): string {
  const query = new URLSearchParams({ id: pilotId });
  if (origin) query.set("console", origin);
  return `/${locale}/screening/pilot?${query.toString()}`;
}

export function triageHref(locale: Locale, view: string, origin = ""): string {
  const query = new URLSearchParams({ view });
  if (origin) query.set("console", origin);
  return `/${locale}/screening/triage?${query.toString()}`;
}

function codeOf(error: unknown): { code: string; message: string } {
  return isScreeningApiError(error) ? { code: error.code, message: error.serverMessage } : { code: "ENGINE_UNREACHABLE", message: "" };
}

/**
 * The draw control: the size, the brand button, and the confirmation. Shared
 * by Prepare's card and the result's "Pilot {n} more records".
 */
export function DrawPilot({
  locale,
  origin,
  corpus,
  brand = true,
  label,
  onDrawn,
}: Readonly<{
  locale: Locale;
  origin: string;
  corpus: number;
  brand?: boolean;
  label?: (n: number) => string;
  onDrawn: (draw: PilotDraw) => void;
}>) {
  const t = (key: PilotCardKey, values: Readonly<Record<string, string | number>> = {}) => fill(COPY[locale][key], values);
  const [size, setSize] = useState(50);
  const [dry, setDry] = useState<PilotDraw | null>(null);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);

  async function ask() {
    setBusy(true);
    setRefusal(null);
    try {
      setDry(await drawPilot(origin, size, false));
    } catch (error) {
      setRefusal(codeOf(error));
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    setBusy(true);
    setRefusal(null);
    try {
      onDrawn(await drawPilot(origin, size, true));
      setDry(null);
    } catch (error) {
      setRefusal(codeOf(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 space-y-3" data-pilot-draw>
      {dry ? (
        <div
          role="alertdialog"
          aria-labelledby="pilot-draw-title"
          aria-describedby="pilot-draw-body"
          className="rounded-md border border-brand p-4"
          onKeyDown={(e) => e.key === "Escape" && setDry(null)}
        >
          <p id="pilot-draw-title" className="font-semibold text-ink">
            {t("drawTitle")}
          </p>
          <p id="pilot-draw-body" className="mt-1 text-sm text-ink">
            {t("drawBody", { n: formatNumber(locale, dry.n), N: formatNumber(locale, corpus) })}
          </p>
          <p className="mt-1 text-sm text-ink-muted">{t("drawLeft", { left: formatNumber(locale, dry.available) })}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button variant="primary" autoFocus disabled={busy} onClick={() => void confirm()}>
              {t("drawConfirm")}
            </Button>
            <Button disabled={busy} onClick={() => setDry(null)}>
              {t("drawCancel")}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap items-end gap-3">
          <label className="block text-sm text-ink">
            {t("size")}
            <input
              type="number"
              min={20}
              max={100}
              step={10}
              value={size}
              aria-describedby="pilot-size-hint"
              onChange={(e) => setSize(Math.min(100, Math.max(20, Math.round((Number(e.target.value) || 50) / 10) * 10)))}
              className="mt-1 block w-28 rounded-md border border-rule bg-paper p-2 text-ink"
            />
          </label>
          <Button variant={brand ? "primary" : "secondary"} disabled={busy} onClick={() => void ask()}>
            {label ? label(size) : t("draw", { n: formatNumber(locale, size) })}
          </Button>
        </div>
      )}
      <p id="pilot-size-hint" className="text-xs text-ink-muted">
        {t("sizeHint")}
      </p>
      {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
    </div>
  );
}

export function PilotCard({ locale, origin }: Readonly<{ locale: Locale; origin: string }>) {
  const t = (key: PilotCardKey, values: Readonly<Record<string, string | number>> = {}) => fill(COPY[locale][key], values);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [criteria, setCriteria] = useState<CriteriaView | null>(null);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);

  const load = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([getSummary(origin), getCriteria(origin)]);
      setSummary(s);
      setCriteria(c);
      setError(null);
    } catch (e) {
      setError(codeOf(e));
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error) return <StateCard locale={locale} code={error.code} message={error.message} consoleOrigin={origin} onRetry={() => void load()} />;
  if (!summary || !criteria) return <p className="text-sm text-ink-muted" role="status">{t("loading")}</p>;
  if (!criteria.batches_prepared) return null;

  const pilot = summary.pilot ?? null;
  const recheck = summary.recheck ?? 0;
  const n = (v: number) => formatNumber(locale, v);
  const heading = !pilot
    ? t("title")
    : pilot.open
      ? t("inProgress", { k: n(pilot.decided), n: n(pilot.n) })
      : pilot.closed_reason === "ended"
        ? t("ended", { k: n(pilot.decided), n: n(pilot.n) })
        : t("complete", { k: n(pilot.decided), n: n(pilot.n) });

  return (
    <section aria-labelledby="pilot-card-title" className="rounded-lg border border-rule bg-leaf p-5" data-pilot-card>
      <h2 id="pilot-card-title" className="font-semibold text-ink">
        {heading}
      </h2>
      {summary.protocol_changed ? (
        <p className="mt-2 text-sm text-ink-muted">{t("protocolChanged")}</p>
      ) : criteria.batch_approved ? (
        <>
          <p className="mt-2 text-sm text-ink">{t("fixed")}</p>
          {pilot ? (
            <a className="mt-2 inline-block text-sm underline" href={pilotHref(locale, pilot.pilot_id, origin)}>
              {t("result")}
            </a>
          ) : null}
        </>
      ) : !pilot ? (
        <>
          <p className="mt-2 text-sm text-ink">{t("body")}</p>
          <DrawPilot
            locale={locale}
            origin={origin}
            corpus={summary.total}
            onDrawn={(draw) => {
              if (draw.pilot_id) window.location.href = triageHref(locale, "pilot", origin);
            }}
          />
          <a className="mt-2 inline-block text-sm underline" href={triageHref(locale, "needs_you", origin)}>
            {t("skip")}
          </a>
        </>
      ) : pilot.open ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <a className={PRIMARY_LINK} href={triageHref(locale, "pilot", origin)}>
            {t("continue")}
          </a>
          <a className="inline-flex min-h-11 items-center px-2 text-sm underline" href={pilotHref(locale, pilot.pilot_id, origin)}>
            {t("soFar")}
          </a>
        </div>
      ) : (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <a className={PRIMARY_LINK} href={pilotHref(locale, pilot.pilot_id, origin)}>
            {t("result")}
          </a>
          <a className="inline-flex min-h-11 items-center px-2 text-sm underline" href={triageHref(locale, "needs_you", origin)}>
            {t("rest")}
          </a>
        </div>
      )}
      {recheck > 0 ? (
        <p className="mt-3 text-sm text-ink">
          {t("recheck", { n: n(recheck) })}{" "}
          <a className="underline" href={triageHref(locale, "recheck", origin)}>
            {t("openThem")}
          </a>
        </p>
      ) : null}
    </section>
  );
}
