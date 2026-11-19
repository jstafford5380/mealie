import type { Slot, VNode } from "vue";
import { Comment, Fragment, Text } from "vue";

export { default as MdiIcon } from "./MdiIcon.vue";

/**
 * Legacy Vuetify components accept an icon path as slot text (`<template #icon>{{ path }}</template>`).
 * Returns that text so it can be passed to MdiIcon, or undefined when the slot has no text.
 */
export function slotText(slot: Slot | undefined): string | undefined {
  if (!slot) {
    return undefined;
  }
  const collect = (nodes: VNode[]): string => nodes.map((node) => {
    if (node.type === Comment) {
      return "";
    }
    if (node.type === Text) {
      return String(node.children ?? "");
    }
    if (node.type === Fragment && Array.isArray(node.children)) {
      return collect(node.children as VNode[]);
    }
    return typeof node.children === "string" ? node.children : "";
  }).join("");
  const text = collect(slot()).trim();
  return text || undefined;
}
