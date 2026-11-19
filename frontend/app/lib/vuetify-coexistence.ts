/**
 * Coexistence helpers for Reka UI overlays that contain Vuetify controls.
 *
 * Vuetify renders menus, selects and autocompletes in `.v-overlay-container` at the end of
 * <body>, outside a Reka dialog's content. Without these helpers a click in such a menu counts
 * as an outside click (closing the dialog), and Escape meant for the menu closes the dialog too.
 * Delete this file when Vuetify is removed.
 */

const PASS_THROUGH = ".v-overlay-container, [data-sonner-toaster], [data-slot=loading-notice]";

export function isInsideVuetifyOverlay(target: EventTarget | null): boolean {
  return target instanceof Element && !!target.closest(PASS_THROUGH);
}

/** True while a Vuetify menu/select/tooltip opened on top of the page is showing. */
export function hasActiveVuetifyOverlay(): boolean {
  return !!document.querySelector(".v-overlay-container .v-overlay--active:not(.v-tooltip)");
}

/** Use for Reka `@pointer-down-outside`, `@focus-outside` and `@interact-outside`. */
export function keepOpenForVuetifyOverlay(event: { target: EventTarget | null; preventDefault: () => void; detail?: { originalEvent?: Event } }) {
  const target = event.detail?.originalEvent?.target ?? event.target;
  if (isInsideVuetifyOverlay(target)) {
    event.preventDefault();
  }
}

// Vuetify closes its menu while handling the same Escape keydown, before Reka sees it, so the
// state is recorded in the capture phase, ahead of every other handler.
let vuetifyOverlayOpenAtEscape = false;
if (typeof window !== "undefined") {
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      vuetifyOverlayOpenAtEscape = hasActiveVuetifyOverlay();
    }
  }, { capture: true });
}

/** Use for Reka `@escape-key-down`: let an open Vuetify menu handle Escape first. */
export function escapeClosesVuetifyOverlayFirst(event: KeyboardEvent) {
  if (vuetifyOverlayOpenAtEscape || hasActiveVuetifyOverlay()) {
    event.preventDefault();
  }
}
