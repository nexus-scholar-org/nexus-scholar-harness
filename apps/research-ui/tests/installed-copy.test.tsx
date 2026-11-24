import { render, screen, waitFor } from "@testing-library/react";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";

import { MailtoCard, OpenAlexKeyCard } from "@/components/discovery-frame";
import { StateCard } from "@/components/screening-state-card";
import { CHARTING_COPY } from "@/lib/charting-copy";
import { discoveryT } from "@/lib/discovery-copy";
import { STARTED_AS_COOKIE, startedAsFrom } from "@/lib/engine-start";
import { INSTALLED_SCOPE, STATES, inceptionStateKey, installedStateKey, stateCopy } from "@/lib/screening-states";

/**
 * M13 Part A, second pull request: the installed app (started from an icon) has
 * no terminal. The engine's launch link says how it was started (a readable
 * cookie); the app then names its window and settings folder instead of a
 * command, an environment variable or the console's terminal.
 */

const LOCALES = ["en", "fr", "ar"] as const;
/** Words that send a user to a terminal or a command line, per language. */
const TERMINAL_WORDS = /terminal|uv run|nexus-scholar (keys|ui|accept)|scholar-agent|console's environment|environnement de la console|الطرفية|بيئة وحدة التحكم/i;

function setCookie(value: string | null) {
  document.cookie = value === null ? `${STARTED_AS_COOKIE}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/` : `${STARTED_AS_COOKIE}=${value}; path=/`;
}

afterEach(() => setCookie(null));

describe("how the engine was started", () => {
  it("reads the launch link's cookie; anything else is a terminal start", () => {
    expect(startedAsFrom("")).toBe("terminal");
    expect(startedAsFrom("a=1; nexus_started_as=installed; b=2")).toBe("installed");
    expect(startedAsFrom("nexus_started_as=terminal")).toBe("terminal");
    expect(startedAsFrom("nexus_started_as=something")).toBe("terminal");
    expect(startedAsFrom("other_nexus_started_as=installed")).toBe("terminal");
  });
});

describe("installed cards", () => {
  const installedKeys = Object.keys(STATES).filter((k) => k.startsWith(INSTALLED_SCOPE));

  it("exist for the settings and keys a terminal start names, in every language, without a terminal", () => {
    expect(installedKeys.sort()).toEqual([
      "installed.DRIVER_UNAVAILABLE",
      "installed.MAILTO_NOT_SET",
      "installed.OPENALEX_KEY_NOT_SET",
      "installed.PROVIDER_KEY_MISSING",
      "installed.SNAPSHOT_NOT_ACCEPTED",
      "installed.inception.MAILTO_NOT_SET",
    ]);
    for (const key of installedKeys) {
      const base = STATES[key.slice(INSTALLED_SCOPE.length)];
      expect(base, key).toBeDefined();
      for (const locale of LOCALES) {
        const copy = STATES[key].copy[locale];
        for (const part of [copy.title, copy.body, copy.affects, copy.action]) {
          expect(part.trim(), `${key} ${locale}`).not.toBe("");
          expect(part, `${key} ${locale}`).not.toMatch(TERMINAL_WORDS);
        }
      }
      expect(STATES[key].action).not.toBe("terminal");
      expect(STATES[key].command ?? "", key).not.toMatch(TERMINAL_WORDS);
    }
  });

  it("are picked only when the engine says it was installed", () => {
    expect(stateCopy("en", "MAILTO_NOT_SET").body).toContain("console's environment");
    expect(stateCopy("en", "MAILTO_NOT_SET", true).body).toContain("settings folder");
    expect(stateCopy("en", "MAILTO_NOT_SET", true).code).toBe("MAILTO_NOT_SET"); // the code shown stays the engine's
    expect(installedStateKey(inceptionStateKey("MAILTO_NOT_SET"), true)).toBe("installed.inception.MAILTO_NOT_SET");
    expect(installedStateKey("STALE_BINDING", true)).toBe("STALE_BINDING"); // no installed card: the usual one
    expect(stateCopy("en", "PROVIDER_KEY_MISSING", true).action).toBe("none");
  });

  it("no longer say the approval code is in the terminal, for either start", () => {
    for (const code of ["APPROVAL_MISSING", "PAIRING_CODE_INVALID"]) {
      for (const locale of LOCALES) expect(STATES[code].copy[locale].body, `${code} ${locale}`).not.toMatch(TERMINAL_WORDS);
    }
  });

  it("the discovery and charting words have an installed variant in every language", () => {
    for (const locale of LOCALES) {
      const t = discoveryT(locale);
      for (const key of ["mailto.whereInstalled", "openalexKey.whereInstalled"] as const) {
        expect(t(key), `${locale} ${key}`).not.toMatch(TERMINAL_WORDS);
        expect(t(key)).toContain(".env");
      }
      expect(CHARTING_COPY[locale]["charting.refusal.mailtoInstalled"]).not.toMatch(TERMINAL_WORDS);
    }
  });
});

describe("the screens", () => {
  it("a state card names the settings folder once the page knows the engine was installed", async () => {
    setCookie("installed");
    render(<StateCard locale="en" code="MAILTO_NOT_SET" />);
    await waitFor(() => expect(screen.getByText(/settings folder/)).toBeInTheDocument());
    expect(screen.getByText("MAILTO_NOT_SET")).toBeInTheDocument();
  });

  it("a terminal start keeps the words it had", () => {
    render(<StateCard locale="en" code="MAILTO_NOT_SET" />);
    expect(screen.getByText(/console's environment/)).toBeInTheDocument();
  });

  it("the contact-email and OpenAlex cards say where the line goes in the installed app", async () => {
    setCookie("installed");
    render(
      <>
        <MailtoCard locale="fr" />
        <OpenAlexKeyCard locale="fr" />
      </>,
    );
    await waitFor(() => expect(screen.getAllByText(/dossier des réglages de Nexus Scholar/)).toHaveLength(2));
  });

  it("the first render matches the static export (no hydration mismatch), whatever the cookie", () => {
    setCookie("installed");
    const html = renderToString(<MailtoCard locale="en" />);
    expect(html).toContain("console&#x27;s environment"); // the pre-rendered words; the cookie applies after mount
  });
});
