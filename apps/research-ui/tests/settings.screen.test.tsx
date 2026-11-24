import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SettingsScreen } from "@/components/settings-screen";
import { SETTINGS_COPY, type SettingsCopyKey } from "@/lib/settings-copy";
import { KEY_NAMES, type KeyName, type SettingsView } from "@/lib/settings-api";

import { blockingViolations } from "./accessibility-in-process.test";

/**
 * The Settings screen (M13 Part B; `docs/ux/shared/final/05-settings.md`) against a
 * stateful fake of the engine's `settings-v1` routes. Made-up keys only; every
 * answer the fake sends is checked never to hold a key's value.
 */

const MADE_UP = "sk-ant-MADE-UP-SECRET-0001";

type Fake = {
  view: SettingsView;
  calls: { method: string; path: string; body: Record<string, unknown> | null }[];
  answers: string[];
  next?: { path: string; status: number; code: string; details?: unknown }[];
  chosen?: string | null;
};

function base(overrides: Partial<SettingsView> = {}): SettingsView {
  const keys = Object.fromEntries(KEY_NAMES.map((n) => [n, { set: false, source: null }])) as SettingsView["keys"];
  return {
    shape: "settings-v1",
    started_as: "installed",
    setup: "done",
    settings_folder: "C:\\Users\\r\\AppData\\Roaming\\Nexus Scholar",
    contact_email: { value: null, source: null },
    keys,
    workspaces_root: { path: "C:\\Users\\r\\Documents\\Nexus Scholar\\workspaces", source: "default" },
    key_store: { kind: "keychain", file: "C:\\Users\\r\\AppData\\Roaming\\Nexus Scholar\\keys.json" },
    ...overrides,
  };
}

function engine(view: SettingsView, options: Partial<Fake> = {}): Fake {
  const fake: Fake = { view, calls: [], answers: [], next: [], ...options };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console", "");
      const method = (init?.method ?? "GET").toUpperCase();
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
      fake.calls.push({ method, path, body });
      const refusal = fake.next?.findIndex((n) => n.path === path) ?? -1;
      const reply = (status: number, payload: unknown) => {
        const text = JSON.stringify(payload);
        fake.answers.push(text);
        return new Response(text, { status, headers: { "content-type": "application/json" } });
      };
      if (refusal >= 0) {
        const r = fake.next!.splice(refusal, 1)[0];
        return reply(r.status, { detail: { code: r.code, message: r.code.toLowerCase(), details: r.details } });
      }
      if (path === "/api/v1/settings" && method === "GET") return reply(200, fake.view);
      if (path === "/api/v1/settings/contact-email") {
        const value = String(body?.value ?? "");
        fake.view = { ...fake.view, contact_email: value ? { value, source: "settings" } : { value: null, source: null } };
        return reply(200, fake.view);
      }
      const key = path.match(/^\/api\/v1\/settings\/keys\/([a-z_]+)(\/remove)?$/);
      if (key) {
        const name = key[1] as KeyName;
        const set = !key[2];
        const where = body?.use_file ? "file" : "keychain";
        fake.view = {
          ...fake.view,
          keys: { ...fake.view.keys, [name]: { set, source: set ? where : null } },
          key_store: body?.use_file ? { ...fake.view.key_store, kind: "file" } : fake.view.key_store,
        };
        return reply(200, fake.view);
      }
      if (path === "/api/v1/settings/folder/choose") {
        const chosen = fake.chosen ?? null;
        if (chosen) fake.view = { ...fake.view, workspaces_root: { path: chosen, source: "settings" } };
        return reply(chosen ? 202 : 200, { chosen, restarting: Boolean(chosen) });
      }
      if (path === "/api/v1/settings/setup") {
        fake.view = { ...fake.view, setup: body?.choice as SettingsView["setup"] };
        return reply(200, fake.view);
      }
      return reply(404, { detail: { code: "NOT_FOUND", message: "" } });
    }),
  );
  return fake;
}

function at(search: string) {
  window.history.replaceState(null, "", `/en/settings/${search}`);
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  at("");
});

describe("settings.screen", () => {
  it("settings mode: three cards in order, no brand button, a way back", async () => {
    engine(base());
    render(<SettingsScreen locale="en" />);
    await screen.findByText("Default location"); // the loading view has the same heading
    expect(screen.getByRole("heading", { level: 1, name: "Settings" })).toBeInTheDocument();
    const cards = [...document.querySelectorAll("[data-card]")].map((c) => c.getAttribute("data-card"));
    expect(cards).toEqual(["email", "keys", "folder"]);
    expect(document.querySelector('[data-variant="primary"]')).toBeNull();
    expect(screen.getByRole("link", { name: "Back to Workspaces" })).toHaveAttribute("href", "/en/workspaces/");
    // The empty look: every key "Not set", the folder at its default.
    expect(screen.getAllByText("Not set")).toHaveLength(5);
    expect(screen.getByText("Default location")).toBeInTheDocument();
  });

  it("first run: setup heading, focus on the e-mail, Done waits for the e-mail, then finishes", async () => {
    at("?setup=1");
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign, reload: vi.fn(), search: "?setup=1", href: "http://localhost/en/settings/?setup=1" });
    const fake = engine(base({ setup: "pending" }));
    render(<SettingsScreen locale="en" />);
    const field = await screen.findByLabelText("E-mail address");
    expect(screen.getByRole("heading", { level: 1, name: "Set up Nexus Scholar" })).toBeInTheDocument();
    await waitFor(() => expect(field).toHaveFocus());
    const done = screen.getByRole("button", { name: "Done" });
    expect(done).toHaveAttribute("aria-disabled", "true");
    expect(done).toHaveAccessibleDescription("Done is available once your e-mail address is saved.");
    fireEvent.click(done);
    expect(fake.calls.some((c) => c.path === "/api/v1/settings/setup")).toBe(false);

    fireEvent.change(field, { target: { value: "reviewer@example.org" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Done" })).toHaveAttribute("aria-disabled", "false"));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith("/en/workspaces/"));
    expect(fake.calls.find((c) => c.path === "/api/v1/settings/setup")?.body).toEqual({ choice: "done" });
  });

  it("Later is always offered and is remembered by the engine", async () => {
    at("?setup=1");
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign, search: "?setup=1", href: "http://localhost/en/settings/?setup=1" });
    const fake = engine(base({ setup: "pending" }));
    render(<SettingsScreen locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Later" }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith("/en/workspaces/"));
    expect(fake.calls.find((c) => c.path === "/api/v1/settings/setup")?.body).toEqual({ choice: "later" });
  });

  it("?setup=1 with setup already chosen renders settings mode: the engine decides, not the URL", async () => {
    at("?setup=1");
    engine(base({ setup: "later" }));
    render(<SettingsScreen locale="en" />);
    expect(await screen.findByRole("heading", { level: 1, name: "Settings" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Done" })).toBeNull();
  });
});

describe("settings.email", () => {
  it("saves, announces, and refuses a bad address with the field kept", async () => {
    const fake = engine(base());
    render(<SettingsScreen locale="en" />);
    const field = await screen.findByLabelText("E-mail address");
    expect(field).toHaveAttribute("type", "email");
    fake.next = [{ path: "/api/v1/settings/contact-email", status: 422, code: "SETTING_INVALID" }];
    fireEvent.change(field, { target: { value: "not-an-address" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("That does not look like an e-mail address. Check it and save again. Nothing was sent.");
    expect(alert).toHaveTextContent("SETTING_INVALID");
    expect(field).toHaveValue("not-an-address");

    fireEvent.change(field, { target: { value: "reviewer@example.org" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(document.querySelector("[data-announce]")).toHaveTextContent("E-mail address saved."));
    expect(fake.calls.filter((c) => c.path === "/api/v1/settings/contact-email").at(-1)).toEqual({ method: "PUT", path: "/api/v1/settings/contact-email", body: { value: "reviewer@example.org" } });
    fireEvent.click(screen.getByRole("button", { name: "Remove" }));
    await waitFor(() => expect(document.querySelector("[data-announce]")).toHaveTextContent("E-mail address removed."));
    expect(fake.calls.at(-1)?.body).toEqual({ value: "" });
  });
});

describe("settings.keys", () => {
  it("a key leaves the page with its request and is never shown again", async () => {
    const fake = engine(base());
    render(<SettingsScreen locale="en" />);
    await screen.findByRole("heading", { level: 1 });
    const row = document.querySelector('[data-key-row="anthropic"]') as HTMLElement;
    const field = within(row).getByLabelText("Paste the key");
    expect(field).toHaveAttribute("type", "password");
    expect(field).toHaveAttribute("autocomplete", "off");
    expect(within(row).queryByRole("button", { name: /show|reveal|copy/i })).toBeNull();
    fireEvent.change(field, { target: { value: MADE_UP } });
    fireEvent.click(within(row).getByRole("button", { name: "Save key" }));
    expect(field).toHaveValue(""); // dropped when the request is sent
    await waitFor(() => expect(within(row).getByText("Set")).toBeInTheDocument());
    expect(within(row).queryByLabelText("Paste the key")).toBeNull();
    expect(within(row).getByText("Kept in the system keychain")).toBeInTheDocument();
    expect(document.body.innerHTML).not.toContain(MADE_UP);
    expect(fake.calls.find((c) => c.path === "/api/v1/settings/keys/anthropic")?.body).toEqual({ value: MADE_UP, use_file: false });
    for (const answer of fake.answers) expect(answer).not.toContain(MADE_UP);
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Anthropic key saved.");

    // Replace moves focus to the field; Escape returns it to Replace.
    fireEvent.click(within(row).getByRole("button", { name: "Replace" }));
    const again = within(row).getByLabelText("Paste the key");
    await waitFor(() => expect(again).toHaveFocus());
    fireEvent.keyDown(again, { key: "Escape" });
    await waitFor(() => expect(within(row).getByRole("button", { name: "Replace" })).toHaveFocus());

    fireEvent.click(within(row).getByRole("button", { name: "Remove" }));
    await waitFor(() => expect(within(row).getByText("Not set")).toBeInTheDocument());
    expect(fake.calls.at(-1)).toEqual({ method: "POST", path: "/api/v1/settings/keys/anthropic/remove", body: {} });
  });

  it("no keychain: asks first, then keeps the key in the file, or drops it", async () => {
    const file = "/home/r/.config/nexus-scholar/keys.json";
    const fake = engine(base({ key_store: { kind: "none", file } }));
    render(<SettingsScreen locale="en" />);
    expect(await screen.findByText(/This computer has no keychain Nexus Scholar can use/)).toBeInTheDocument();
    const row = document.querySelector('[data-key-row="openalex"]') as HTMLElement;
    fake.next = [{ path: "/api/v1/settings/keys/openalex", status: 409, code: "KEYCHAIN_UNAVAILABLE", details: { file } }];
    fireEvent.change(within(row).getByLabelText("Paste the key"), { target: { value: "oa-MADE-UP" } });
    fireEvent.click(within(row).getByRole("button", { name: "Save key" }));
    const confirm = await within(row).findByText(/Keep the keys in a file only you can read\?/);
    expect(confirm).toHaveTextContent(file);
    await waitFor(() => expect(confirm).toHaveFocus());
    fireEvent.click(within(row).getByRole("button", { name: "Keep the key in that file" }));
    await waitFor(() => expect(within(row).getByText("Set")).toBeInTheDocument());
    expect(fake.calls.at(-1)?.body).toEqual({ value: "oa-MADE-UP", use_file: true });

    const s2 = document.querySelector('[data-key-row="semanticscholar"]') as HTMLElement;
    fake.next = [{ path: "/api/v1/settings/keys/semanticscholar", status: 409, code: "KEYCHAIN_UNAVAILABLE", details: { file } }];
    fireEvent.change(within(s2).getByLabelText("Paste the key"), { target: { value: "s2-MADE-UP" } });
    fireEvent.click(within(s2).getByRole("button", { name: "Save key" }));
    const before = fake.calls.length;
    fireEvent.click(await within(s2).findByRole("button", { name: "Do not save" }));
    expect(fake.calls.length).toBe(before);
    expect(within(s2).getByText("Not set")).toBeInTheDocument();
  });
});

describe("settings.elsewhere", () => {
  it("a value set in the environment or .env is printed with its source and cannot be edited", async () => {
    const view = base({
      setup: "pending",
      contact_email: { value: "env@example.org", source: "environment" },
      workspaces_root: { path: "/srv/reviews", source: "flag" },
    });
    view.keys.openalex = { set: true, source: "env_file", variable: "SCHOLAR_OPENALEX_KEY" };
    view.keys.gemini = { set: true, source: "environment", variable: "GEMINI_API_KEY" };
    at("?setup=1");
    engine(view);
    render(<SettingsScreen locale="en" />);
    expect(await screen.findByText("Set in the environment (SCHOLAR_MAILTO)")).toBeInTheDocument();
    expect(screen.queryByLabelText("E-mail address")).toBeNull();
    const oa = document.querySelector('[data-key-row="openalex"]') as HTMLElement;
    expect(within(oa).getByText("Set in the .env file")).toBeInTheDocument();
    expect(within(oa).queryByRole("button")).toBeNull();
    expect(within(document.querySelector('[data-key-row="gemini"]') as HTMLElement).getByText("Set in the environment (GEMINI_API_KEY)")).toBeInTheDocument();
    expect(screen.getByText("Set when the app was started (--root)")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Change…" })).toBeNull();
    expect(screen.getByRole("button", { name: "Done" })).toHaveAttribute("aria-disabled", "false"); // the e-mail is set elsewhere
  });
});

describe("settings.folder", () => {
  it("a cancel changes nothing; a chosen folder waits for the engine, then reloads", async () => {
    const reload = vi.fn();
    vi.stubGlobal("location", { ...window.location, reload, assign: vi.fn(), search: "", href: "http://localhost/en/settings/" });
    const fake = engine(base(), { chosen: null });
    render(<SettingsScreen locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Change…" }));
    await waitFor(() => expect(fake.calls.some((c) => c.path === "/api/v1/settings/folder/choose")).toBe(true));
    await waitFor(() => expect(screen.getByRole("button", { name: "Change…" })).not.toBeDisabled());
    expect(screen.queryByRole("alert")).toBeNull();

    fake.chosen = "D:\\Reviews";
    fireEvent.click(screen.getByRole("button", { name: "Change…" }));
    const moving = await screen.findByText(/Moving to/, { selector: "[data-restarting]" });
    expect(moving).toHaveTextContent("D:\\Reviews");
    await waitFor(() => expect(reload).toHaveBeenCalled(), { timeout: 4000 });
  });

  it("names why a folder cannot be chosen; the --root hint only for a terminal start", async () => {
    const fake = engine(base({ started_as: "installed" }));
    render(<SettingsScreen locale="en" />);
    fake.next = [{ path: "/api/v1/settings/folder/choose", status: 409, code: "FOLDER_DIALOG_UNAVAILABLE" }];
    fireEvent.click(await screen.findByRole("button", { name: "Change…" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Nexus Scholar cannot open a folder window because this computer has no desktop for it.");
    expect(alert.textContent).not.toContain("--root");
    fake.next = [{ path: "/api/v1/settings/folder/choose", status: 501, code: "RESTART_UNSUPPORTED" }];
    fireEvent.click(screen.getByRole("button", { name: "Change…" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("This copy of Nexus Scholar cannot restart itself."));
  });

  it("the terminal start gets the --root hint", async () => {
    const fake = engine(base({ started_as: "terminal" }));
    render(<SettingsScreen locale="en" />);
    fake.next = [{ path: "/api/v1/settings/folder/choose", status: 409, code: "FOLDER_DIALOG_UNAVAILABLE" }];
    fireEvent.click(await screen.findByRole("button", { name: "Change…" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Start the app with --root <folder>, or set NEXUS_WORKSPACES_ROOT.");
  });
});

describe("settings.states", () => {
  it("loading shows no 'Not set' before the first answer", async () => {
    let release: (value: Response) => void = () => {};
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { release = resolve; })));
    render(<SettingsScreen locale="en" />);
    expect(document.querySelector("[data-settings-loading]")).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByText("Not set")).toBeNull();
    await act(async () => release(new Response(JSON.stringify(base()), { status: 200, headers: { "content-type": "application/json" } })));
    expect(await screen.findAllByText("Not set")).toHaveLength(5);
  });

  it("a phone token sees only the desktop pointer", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ detail: { code: "TOKEN_SCOPE_REFUSED", message: "" } }), { status: 403, headers: { "content-type": "application/json" } })));
    render(<SettingsScreen locale="en" />);
    expect(await screen.findByText(/Settings are changed on the computer that runs Nexus Scholar/)).toBeInTheDocument();
    expect(screen.queryByLabelText("E-mail address")).toBeNull();
  });

  it("an unreachable engine keeps the last values and disables every write", async () => {
    const fake = engine(base({ contact_email: { value: "r@example.org", source: "settings" } }));
    render(<SettingsScreen locale="en" />);
    await screen.findByLabelText("E-mail address");
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("connection refused"); }));
    await act(async () => window.dispatchEvent(new Event("focus")));
    expect(await screen.findByText(/As of/)).toBeInTheDocument();
    expect(screen.getByLabelText("E-mail address")).toHaveValue("r@example.org");
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
    expect(fake.calls.length).toBeGreaterThan(0);
  });
});

describe("settings.i18n", () => {
  it("every key exists in en, fr and ar with the same parameters", () => {
    const keys = Object.keys(SETTINGS_COPY.en) as SettingsCopyKey[];
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const locale of ["fr", "ar"] as const) {
      expect(Object.keys(SETTINGS_COPY[locale]).sort()).toEqual([...keys].sort());
      for (const key of keys) {
        expect(SETTINGS_COPY[locale][key].trim(), `${locale} ${key}`).not.toBe("");
        expect(holes(SETTINGS_COPY[locale][key]), `${locale} ${key}`).toEqual(holes(SETTINGS_COPY.en[key]));
      }
    }
  });

  it("the key rows are exactly the five keys the engine stores", () => {
    expect([...KEY_NAMES].sort()).toEqual(["anthropic", "gemini", "openai_compatible", "openalex", "semanticscholar"]);
  });
});

describe("settings.a11y (in-process axe; jsdom computes no contrast, so that stays a check by hand)", () => {
  for (const [locale, theme] of [["en", "light"], ["en", "dark"], ["ar", "light"]] as const) {
    it(`no blocking violation in ${locale}, ${theme} theme, first run and a refusal`, async () => {
      document.documentElement.dataset.theme = theme;
      document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
      at("?setup=1");
      const fake = engine(base({ setup: "pending" }));
      const { container } = render(<SettingsScreen locale={locale} />);
      await screen.findAllByRole("heading", { level: 2 });
      fake.next = [{ path: "/api/v1/settings/contact-email", status: 422, code: "SETTING_INVALID" }];
      fireEvent.click(screen.getAllByRole("button", { name: SETTINGS_COPY[locale]["settings.email.save"] })[0]);
      await screen.findByRole("alert");
      const results = await axe.run(container);
      expect(results.violations.length + results.incomplete.length + results.passes.length).toBeGreaterThan(0);
      expect(blockingViolations(results).map((v) => `${v.id}: ${v.help}`)).toEqual([]);
      delete document.documentElement.dataset.theme;
      document.documentElement.dir = "ltr";
    });
  }
});
