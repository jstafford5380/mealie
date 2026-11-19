/**
 * Overlay helpers for Reka dialogs.
 *
 * Toasts and the loading notice render outside a dialog's content, at the end of <body>.
 * Clicking one must not count as an outside click that closes the dialog.
 * (The file name predates the Vuetify removal; the exports keep their names for BaseDialog.)
 */

const PASS_THROUGH = "[data-sonner-toaster], [data-slot=loading-notice]";

export function isInsideVuetifyOverlay(target: EventTarget | null): boolean {
  return target instanceof Element && !!target.closest(PASS_THROUGH);
}

/** Use for Reka `@pointer-down-outside`, `@focus-outside` and `@interact-outside`. */
export function keepOpenForVuetifyOverlay(event: { target: EventTarget | null; preventDefault: () => void; detail?: { originalEvent?: Event } }) {
  const target = event.detail?.originalEvent?.target ?? event.target;
  if (isInsideVuetifyOverlay(target)) {
    event.preventDefault();
  }
}

/** Use for Reka `@escape-key-down`. Nothing else handles Escape first any more. */
export function escapeClosesVuetifyOverlayFirst(_event: KeyboardEvent) {}
