import { consoleBase, postJson, readJson } from "./screening-api";

/**
 * The Settings routes (M13 Part B; `docs/architecture/settings-api.md`). Desktop
 * only and workspace-free. No answer ever holds a key's value: a key is `set`
 * or not, and where it is kept.
 */

export const KEY_NAMES = ["openalex", "semanticscholar", "anthropic", "openai_compatible", "gemini"] as const;
export type KeyName = (typeof KEY_NAMES)[number];
export const DATABASE_KEYS: readonly KeyName[] = ["openalex", "semanticscholar"];
export const AI_KEYS: readonly KeyName[] = ["anthropic", "openai_compatible", "gemini"];

export type SettingSource = "environment" | "env_file" | "settings" | "keychain" | "file" | "flag" | "default";

export interface KeyState {
  set: boolean;
  source: SettingSource | null;
  /** The environment variable that wins over the screen (a name, never a value). */
  variable?: string;
}

export interface SettingsView {
  shape: "settings-v1";
  started_as: "installed" | "terminal" | null;
  setup: "pending" | "done" | "later";
  settings_folder: string;
  contact_email: { value: string | null; source: SettingSource | null };
  keys: Record<KeyName, KeyState>;
  workspaces_root: { path: string; source: SettingSource };
  key_store: { kind: "keychain" | "file" | "none"; file: string };
}

export interface FolderAnswer {
  chosen: string | null;
  restarting: boolean;
}

/** A value set in the environment or `.env` wins over the screen and is not changed here (answer 2). */
export function setElsewhere(source: SettingSource | null): boolean {
  return source === "environment" || source === "env_file" || source === "flag";
}

const BASE = "/api/v1/settings";

export function getSettings(origin: string, signal?: AbortSignal): Promise<SettingsView> {
  return readJson<SettingsView>(BASE, consoleBase(origin), signal);
}

export function saveContactEmail(origin: string, value: string): Promise<SettingsView> {
  return postJson<SettingsView>(`${BASE}/contact-email`, origin, { value }, undefined, "PUT");
}

export function saveKey(origin: string, name: KeyName, value: string, useFile = false): Promise<SettingsView> {
  return postJson<SettingsView>(`${BASE}/keys/${name}`, origin, { value, use_file: useFile }, undefined, "PUT");
}

export function removeKey(origin: string, name: KeyName): Promise<SettingsView> {
  return postJson<SettingsView>(`${BASE}/keys/${name}/remove`, origin, {});
}

export function chooseFolder(origin: string): Promise<FolderAnswer> {
  return postJson<FolderAnswer>(`${BASE}/folder/choose`, origin, {});
}

export function finishSetup(origin: string, choice: "done" | "later"): Promise<SettingsView> {
  return postJson<SettingsView>(`${BASE}/setup`, origin, { choice });
}
