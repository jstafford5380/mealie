import type { SortableEvent } from "sortablejs";
import { useEventListener } from "@vueuse/core";

export function useMealPlanDragPreview() {
  let dragPreview: {
    item: HTMLElement;
    source: HTMLElement;
    next: Element | null;
    original: HTMLElement;
    ghost: HTMLElement | null;
    copying: boolean;
  } | null = null;

  function refreshMealDragPreview() {
    if (!dragPreview) return;
    const { item, source, next, original, ghost, copying } = dragPreview;
    const following = item.nextElementSibling;
    const inOriginalSlot = item.parentElement === source
      && (following === next || (following === original && original.nextElementSibling === next));
    item.classList.toggle("meal-plan-copy-origin", copying && inOriginalSlot);
    ghost?.classList.toggle("meal-plan-copy-ghost", copying);
    if (copying && !inOriginalSlot) {
      if (!original.isConnected) source.insertBefore(original, next?.parentElement === source ? next : null);
    }
    else {
      original.remove();
    }
  }

  function startMealDrag(event: Pick<SortableEvent, "item" | "from"> & { originalEvent?: MouseEvent | TouchEvent }) {
    const { item, from: source } = event;
    const original = item.cloneNode(true) as HTMLElement;
    original.removeAttribute("data-id");
    original.removeAttribute("id");
    original.querySelectorAll("[id]").forEach(element => element.removeAttribute("id"));
    original.setAttribute("aria-hidden", "true");
    original.inert = true;
    original.classList.remove("opacity-40");
    dragPreview = {
      item,
      source,
      next: item.nextElementSibling,
      original,
      ghost: source.ownerDocument.querySelector(".meal-plan-drag-preview"),
      copying: event.originalEvent?.shiftKey === true,
    };
    refreshMealDragPreview();
  }

  function setCopyPreview(copying: boolean) {
    if (!dragPreview || dragPreview.copying === copying) return;
    dragPreview.copying = copying;
    refreshMealDragPreview();
  }

  function clearMealDragPreview() {
    dragPreview?.original.remove();
    dragPreview?.item.classList.remove("meal-plan-copy-origin");
    dragPreview?.ghost?.classList.remove("meal-plan-copy-ghost");
    dragPreview = null;
  }

  useEventListener("keydown", (event) => {
    if (event.key === "Shift") setCopyPreview(true);
  });
  useEventListener("keyup", (event) => {
    if (event.key === "Shift") setCopyPreview(false);
  });
  useEventListener("blur", () => setCopyPreview(false));
  // Remove the visual-only card before Sortable reads child indices on drop.
  useEventListener(["pointerup", "mouseup", "touchend", "touchcancel"], clearMealDragPreview, { capture: true });
  onScopeDispose(clearMealDragPreview);

  return { startMealDrag, refreshMealDragPreview, clearMealDragPreview };
}
