/**
 * The stored theme and the script that applies it before paint (production plan §3, M0).
 *
 * This module has no directive on purpose. The component that owns `<html>` renders on
 * the server and puts {@link THEME_BOOT_SCRIPT} in `<head>`. Imported from a client module, the string
 * reached the page as a reference to that module rather than as text; when its code
 * arrived after hydration began, `<head>` waited for it and React could not match the
 * document (#418 on every page, H-hydration-418). From here the server writes the text
 * itself. `tests/server-client-boundary.test.ts` keeps it so.
 */

export const THEME_STORAGE_KEY = "nexus-scholar-theme";

/** Runs in `<head>` before the body paints: a stored `light` or `dark` sets `data-theme` on `<html>`. */
export const THEME_BOOT_SCRIPT = `(function(){try{var t=localStorage.getItem(${JSON.stringify(
  THEME_STORAGE_KEY,
)});if(t==="light"||t==="dark"){document.documentElement.setAttribute("data-theme",t);}}catch(e){}})();`;
