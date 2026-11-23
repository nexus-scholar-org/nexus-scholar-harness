/**
 * What a screen shows while the engine answers (H-screening-read-performance,
 * question 5, decided 2026-11-22; finding 47's blank first paint): the page's
 * name as its heading, the sentence the screen already had, and empty cards
 * where the content will be. No animation.
 */
export function LoadingFrame({ heading, sentence, cards = 2 }: Readonly<{ heading: string; sentence: string; cards?: number }>) {
  return (
    <div className="space-y-6" aria-busy="true" data-loading-frame>
      <header>
        <h1 className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{heading}</h1>
        <p className="mt-2 text-ink-muted" role="status">
          {sentence}
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-2" aria-hidden="true">
        {Array.from({ length: cards }, (_, i) => (
          <div key={i} className="min-h-32 rounded-lg border border-rule bg-leaf" data-loading-card />
        ))}
      </div>
    </div>
  );
}
