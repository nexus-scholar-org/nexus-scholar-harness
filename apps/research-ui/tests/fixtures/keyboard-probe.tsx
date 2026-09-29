/**
 * Test-only focusable markup.
 *
 * None of the components in `components/` render an interactive element yet,
 * so there is nothing in the current `/` scaffold for a Tab traversal to move
 * between. This probe supplies ordinary semantic focusable elements — a link
 * and a button — so that traversal itself can be asserted. It asserts nothing
 * about the research domain and is not a route, screen, or shipped component.
 */
export function KeyboardProbe() {
  return (
    <nav aria-label="Probe navigation">
      <a href="#first">First link</a>
      <button type="button">Second action</button>
      <input aria-label="Third field" />
    </nav>
  );
}
