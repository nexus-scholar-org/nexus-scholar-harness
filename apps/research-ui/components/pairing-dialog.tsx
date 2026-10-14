"use client";

import { Dialog, DialogBackdrop, DialogPanel } from "@headlessui/react";
import { useEffect, useRef, useState, type FormEvent } from "react";

import type { Locale } from "@/i18n";

/**
 * The pairing-code approval dialog (packet UI-07, action side).
 *
 * The operator stages a single-use challenge in their terminal and reads the
 * code from their own screen; the reader types it here. The typed code lives
 * in component state only: it is never written to browser storage, never
 * placed in navigation state, and the field is cleared on every submit and
 * on every close, so a consumed or expired code leaves nothing behind to
 * steal. The dialog posts the code once over loopback and retains nothing
 * afterwards.
 *
 * Modal behaviour (focus trap, `Escape`, focus restoration) comes from the
 * same Headless UI `Dialog` the navigation disclosure uses, so keyboard
 * handling is shared rather than re-derived. The visible title is a plain
 * paragraph, not a heading: the screening composition owns the h1 → h2
 * order and this dialog must not add to it.
 *
 * The strings below sit beside the component rather than in the catalogs
 * because the catalogs are frozen to their packet's scope; they are
 * demonstration-grade translations pending fluent review, and every
 * server-supplied value around them (fingerprints, codes, refusal text)
 * keeps its own element, untranslated, exactly as served.
 */
export const ACTION_CHROME = {
  en: {
    actionsTitle: "Operator approval",
    actionsLede:
      "Approval is an operator act in the terminal. The browser only carries the single-use code the operator staged.",
    challengeLabel: "Challenge",
    loadingLabel: "Checking the staged challenge…",
    approveButton: "Approve with pairing code",
    deferButton: "Defer with reason",
    publishButton: "Publish",
    reasonLabel: "Reason for deferral",
    dialogTitle: "Enter the pairing code",
    dialogLede:
      "Type the single-use code shown in the operator terminal. It is checked once and never stored in this browser.",
    codeLabel: "Pairing code",
    codeHint: "Letters and digits as shown; dashes and case do not matter.",
    submitCodeButton: "Check code and approve",
    cancelButton: "Cancel",
    workingLabel: "Working…",
    approvedNote: "Approval recorded.",
    deferredNote: "Batch deferred; nothing was published.",
    publishedNote: "Publication is current.",
    requestLabel: "Request",
  },
  fr: {
    actionsTitle: "Approbation de l'opératrice ou de l'opérateur",
    actionsLede:
      "L'approbation est un acte de l'opératrice ou de l'opérateur dans le terminal. Le navigateur ne porte que le code à usage unique préparé.",
    challengeLabel: "Défi",
    loadingLabel: "Vérification du défi préparé…",
    approveButton: "Approuver avec le code d'appariement",
    deferButton: "Reporter avec un motif",
    publishButton: "Publier",
    reasonLabel: "Motif du report",
    dialogTitle: "Saisir le code d'appariement",
    dialogLede:
      "Saisissez le code à usage unique affiché dans le terminal. Il est vérifié une seule fois et jamais conservé dans ce navigateur.",
    codeLabel: "Code d'appariement",
    codeHint: "Lettres et chiffres tels qu'affichés ; tirets et casse indifférents.",
    submitCodeButton: "Vérifier le code et approuver",
    cancelButton: "Annuler",
    workingLabel: "En cours…",
    approvedNote: "Approbation enregistrée.",
    deferredNote: "Vague reportée ; rien n'a été publié.",
    publishedNote: "La publication est à jour.",
    requestLabel: "Demande",
  },
  ar: {
    actionsTitle: "اعتماد المشغّل",
    actionsLede:
      "الاعتماد فعل يجريه المشغّل في الطرفية. لا يحمل المتصفح سوى الرمز وحيد الاستخدام الذي جهّزه المشغّل.",
    challengeLabel: "التحدي",
    loadingLabel: "جارٍ التحقق من التحدي المُجهّز…",
    approveButton: "اعتماد برمز الإقران",
    deferButton: "التأجيل مع ذكر السبب",
    publishButton: "نشر",
    reasonLabel: "سبب التأجيل",
    dialogTitle: "أدخل رمز الإقران",
    dialogLede:
      "اكتب الرمز وحيد الاستخدام الظاهر في طرفية المشغّل. يُتحقق منه مرة واحدة ولا يُخزَّن في هذا المتصفح أبدًا.",
    codeLabel: "رمز الإقران",
    codeHint: "حروف وأرقام كما تظهر؛ الشرطات وحالة الأحرف غير مهمة.",
    submitCodeButton: "التحقق من الرمز والاعتماد",
    cancelButton: "إلغاء",
    workingLabel: "جارٍ العمل…",
    approvedNote: "تم تسجيل الاعتماد.",
    deferredNote: "تم تأجيل الدفعة؛ ولم يُنشر شيء.",
    publishedNote: "النشر محدّث.",
    requestLabel: "الطلب",
  },
} as const;

export interface PairingServerError {
  code: string;
  message: string;
}

interface PairingDialogProps {
  locale: Locale;
  open: boolean;
  pending: boolean;
  serverError: PairingServerError | null;
  snapshotFingerprint: string | null;
  onClose: () => void;
  onSubmit: (code: string) => void;
}

export function PairingDialog({
  locale,
  open,
  pending,
  serverError,
  snapshotFingerprint,
  onClose,
  onSubmit,
}: Readonly<PairingDialogProps>) {
  const chrome = ACTION_CHROME[locale];
  const [code, setCode] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Memory-only discipline: the field starts empty on every open and is
    // wiped on every close, so no typed code outlives the dialog.
    setCode("");
    if (!open) return;
    const timer = window.setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [open ]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const typed = code;
    setCode("");
    inputRef.current?.focus();
    if (typed.trim() !== "") onSubmit(typed);
  }

  function handleCancel() {
    setCode("");
    onClose();
  }

  return (
    <Dialog open={open} onClose={handleCancel} aria-label={chrome.dialogTitle}>
      <DialogBackdrop className="fixed inset-0 bg-ink/40" />
      <DialogPanel className="fixed inset-y-0 end-0 w-full max-w-sm overflow-y-auto border-s border-rule-strong bg-leaf p-6">
        <p id="pairing-dialog-title" className="font-display text-xl leading-8 text-ink">
          {chrome.dialogTitle}
        </p>
        <p className="mt-1 text-sm leading-6 text-ink-muted">{chrome.dialogLede}</p>
        {snapshotFingerprint ? (
          <p className="mt-3 text-sm leading-6 text-ink-muted">
            {chrome.challengeLabel}
            {": "}
            <bdi dir="ltr">{snapshotFingerprint}</bdi>
          </p>
        ) : null}
        <form onSubmit={handleSubmit} className="mt-3">
          <label htmlFor="pairing-code" className="block text-sm font-medium text-ink">
            {chrome.codeLabel}
          </label>
          <p id="pairing-code-hint" className="mt-1 text-sm leading-6 text-ink-muted">
            {chrome.codeHint}
          </p>
          <input
            ref={inputRef}
            id="pairing-code"
            name="pairing-code"
            type="text"
            autoComplete="off"
            autoCapitalize="characters"
            autoCorrect="off"
            spellCheck={false}
            value={code}
            onChange={(event) => setCode(event.target.value)}
            aria-describedby="pairing-code-hint"
            className="mt-2 block w-full border border-rule-strong bg-leaf px-3 py-2 text-sm leading-6 text-ink"
          />
          {serverError ? (
            <p role="alert" className="mt-2 text-sm leading-6 text-warning">
              <bdi dir="ltr">{serverError.code}</bdi>
              {": "}
              <bdi dir="ltr">{serverError.message}</bdi>
            </p>
          ) : null}
          <div className="mt-8 border-t border-rule pt-5">
            <button
              type="submit"
              disabled={pending || code.trim() === ""}
              className="inline-flex items-center gap-2 border border-rule-strong bg-leaf px-3 py-2 text-sm font-medium text-ink hover:bg-paper disabled:cursor-not-allowed disabled:border-rule disabled:text-ink-faint"
            >
              {pending ? chrome.workingLabel : chrome.submitCodeButton}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="inline-flex items-center gap-2 border border-rule-strong px-3 py-2 text-sm font-medium text-ink hover:bg-paper"
            >
              {chrome.cancelButton}
            </button>
          </div>
        </form>
      </DialogPanel>
    </Dialog>
  );
}
