"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { type Locale } from "@/i18n";

/**
 * Forwards an address that has no screen of its own (`/<locale>`, the old
 * `/<locale>/screening`) to the one that does, keeping the query (a
 * development build's `?console=`). The pages are prerendered files, so the forward
 * happens in the browser; the link is there for a reader without scripts.
 */
export function RouteRedirect({ locale, to, label }: Readonly<{ locale: Locale; to: string; label: string }>) {
  const router = useRouter();
  const href = `/${locale}${to}`;
  useEffect(() => {
    router.replace(`${href}${window.location.search}`);
  }, [router, href]);
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Link href={href} className="text-sm font-medium text-brand underline underline-offset-4">
        {label}
      </Link>
    </div>
  );
}
