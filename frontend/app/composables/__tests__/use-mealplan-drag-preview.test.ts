import { expect, test } from "vitest";
import { effectScope } from "vue";
import { useMealPlanDragPreview } from "../use-mealplan-drag-preview";

test("Shift restores the source preview after the card has crossed days, and keyup switches back", () => {
  const scope = effectScope();
  const board = document.createElement("div");
  const source = document.createElement("div");
  const target = document.createElement("div");
  const item = document.createElement("div");
  item.dataset.id = "7";
  item.className = "opacity-40";
  item.textContent = "Pancakes";
  const add = document.createElement("button");
  add.textContent = "Add";
  const ghost = document.createElement("div");
  ghost.className = "meal-plan-drag-preview";
  source.append(item, add);
  board.append(source, target, ghost);
  document.body.append(board);
  try {
    const preview = scope.run(useMealPlanDragPreview)!;
    preview.startMealDrag({ item, from: source });
    target.append(item);
    preview.refreshMealDragPreview();
    expect(source.textContent).toBe("Add");

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Shift" }));
    expect(source.textContent).toBe("PancakesAdd");
    expect(source.querySelector("[aria-hidden=true]")?.hasAttribute("data-id")).toBe(false);
    expect(ghost.classList.contains("meal-plan-copy-ghost")).toBe(true);

    window.dispatchEvent(new KeyboardEvent("keyup", { key: "Shift" }));
    expect(source.textContent).toBe("Add");
    expect(ghost.classList.contains("meal-plan-copy-ghost")).toBe(false);

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Shift" }));
    window.dispatchEvent(new MouseEvent("mouseup"));
    expect(source.textContent).toBe("Add");
    expect(ghost.classList.contains("meal-plan-copy-ghost")).toBe(false);
    expect(target.firstElementChild).toBe(item);
  }
  finally {
    scope.stop();
    board.remove();
  }
});
