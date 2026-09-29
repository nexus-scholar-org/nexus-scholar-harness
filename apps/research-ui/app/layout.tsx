import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";

import "./globals.css";

export const metadata: Metadata = {
  title: "Nexus Scholar",
  description: "Traceable systematic-review workflows for research teams.",
};

/**
 * The document language, declared once and exported so a test can mirror it
 * onto the real `document.documentElement` instead of inventing a value.
 */
export const DOCUMENT_LANG = "en";

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang={DOCUMENT_LANG}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
