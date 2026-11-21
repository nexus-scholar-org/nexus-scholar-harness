/**
 * Whether each kind of Triage mark is on, remembered on this computer (spec 03,
 * M8b point 2; decision 18). Read after render, in an effect, never during it
 * (N12): the first render shows both kinds on, then the remembered choice.
 * Not stored in the workspace.
 */

export const TERMS_KEY = "nexus.triage.marks.terms";
export const QUOTES_KEY = "nexus.triage.marks.quotes";

/** A switch is on unless this computer remembers it off ("0"). */
export function rememberedOn(key: string): boolean {
  try {
    return window.localStorage.getItem(key) !== "0";
  } catch {
    return true;
  }
}

export function rememberOn(key: string, on: boolean) {
  try {
    window.localStorage.setItem(key, on ? "1" : "0");
  } catch {
    /* storage refused: the choice lasts this page only */
  }
}
