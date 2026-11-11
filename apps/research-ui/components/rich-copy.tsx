import { Fragment, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { INCEPTION_COPY, type InceptionCopyKey } from "@/lib/inception-copy";

/**
 * A catalogued sentence with element values (I18N.md §3): the sentence keeps the
 * page direction, and only a value that is an identifier, date, code or
 * fingerprint is isolated left-to-right. Wrapping the whole sentence in
 * `dir="ltr"` reverses an Arabic sentence's segments, so it is never done.
 */
export function fillRich(template: string, values: Record<string, ReactNode>): ReactNode[] {
  return template.split(/\{(\w+)\}/g).map((part, i) => {
    if (i % 2 === 0) return part ? <Fragment key={i}>{part}</Fragment> : null;
    if (!(part in values)) throw new Error(`inception copy needs {${part}}`);
    return <Fragment key={i}>{values[part]}</Fragment>;
  });
}

export function inceptionRichT(locale: Locale) {
  return (key: InceptionCopyKey, values: Record<string, ReactNode>) => fillRich(INCEPTION_COPY[locale][key], values);
}

/** One left-to-right value inside a sentence (a date, code, DOI, fingerprint, language codes). */
export function Ltr({ children, mono = false }: Readonly<{ children: ReactNode; mono?: boolean }>) {
  return (
    <bdi dir="ltr" className={mono ? "font-mono" : undefined} data-ltr-value>
      {children}
    </bdi>
  );
}
