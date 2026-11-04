import type { ButtonHTMLAttributes, ReactNode } from "react";

/**
 * Foundation components of the brand design system (production plan §3, M0).
 *
 * Each one carries a brand-book rule so screens do not restate it:
 * - `Button`: one `primary` (brand fill) per screen; every variant is at least
 *   44px tall; `radius-md`.
 * - `DecisionBadge`: a decision outcome as a word on its role's `-soft` tint,
 *   in the role's full colour; status is never colour alone.
 * - `GatePanel`: the one confirmation gate of a screen: `brand-soft` fill,
 *   dashed `brand` border, a `brand` label, `radius-lg`.
 * - `EvidenceQuote`: a verbatim quote on `anchor-soft`, its source in `anchor`.
 * - `DataCell`: an identifier (DOI, `STU-` id, fingerprint, path) in mono.
 *
 * They hold no text of their own; every visible string arrives as a prop from
 * the catalogs. Screen-specific components (decision bar, record card, queue)
 * are built with their screens in M1b.
 */

type ButtonVariant = "primary" | "secondary" | "quiet";

const BUTTON_BASE =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-md px-4 text-[0.9375rem] font-medium leading-[1.375rem] disabled:cursor-not-allowed disabled:opacity-50";

const BUTTON_VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-brand text-on-brand hover:opacity-90",
  secondary: "border border-rule-strong bg-leaf text-ink hover:bg-leaf-raised",
  quiet: "text-brand underline decoration-transparent underline-offset-4 hover:decoration-brand",
};

export function Button({
  variant = "secondary",
  className = "",
  type = "button",
  ...props
}: Readonly<ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }>) {
  return (
    <button
      type={type}
      className={`${BUTTON_BASE} ${BUTTON_VARIANTS[variant]} ${className}`.trim()}
      {...props}
    />
  );
}

export type DecisionRole = "include" | "unclear" | "blocked" | "exclude";

const DECISION_STYLES: Record<DecisionRole, string> = {
  include: "bg-include-soft text-include",
  unclear: "bg-unclear-soft text-unclear",
  blocked: "bg-blocked-soft text-blocked",
  exclude: "bg-exclude-soft text-exclude",
};

export function DecisionBadge({ role, children }: Readonly<{ role: DecisionRole; children: ReactNode }>) {
  return (
    <span
      data-role={role}
      className={`inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-semibold leading-4 ${DECISION_STYLES[role]}`}
    >
      {children}
    </span>
  );
}

export function GatePanel({
  label,
  children,
  actions,
}: Readonly<{ label: ReactNode; children: ReactNode; actions?: ReactNode }>) {
  return (
    <section className="rounded-lg border border-dashed border-brand bg-brand-soft p-4">
      <p className="text-xs font-semibold uppercase leading-4 tracking-[0.05em] text-brand rtl:tracking-normal">
        {label}
      </p>
      <div className="mt-2 text-[0.9375rem] leading-[1.375rem] text-ink">{children}</div>
      {actions ? <div className="mt-4 flex flex-wrap gap-2">{actions}</div> : null}
    </section>
  );
}

export function EvidenceQuote({ children, source }: Readonly<{ children: ReactNode; source?: ReactNode }>) {
  return (
    <figure className="rounded-md bg-anchor-soft px-4 py-3">
      <blockquote className="text-[0.9375rem] leading-[1.375rem] text-ink">{children}</blockquote>
      {source ? (
        <figcaption className="mt-2 font-mono text-[0.8125rem] leading-[1.125rem] text-anchor">{source}</figcaption>
      ) : null}
    </figure>
  );
}

export function DataCell({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <span dir="ltr" className="font-mono text-[0.8125rem] leading-[1.125rem] text-ink [overflow-wrap:anywhere]">
      {children}
    </span>
  );
}
