<template>
  <ul
    class="m-0 list-none p-0 font-mono text-[13px]"
    :class="depth > 0 && 'ms-4 border-s ps-3'"
  >
    <li
      v-for="node in nodes"
      :key="node.id ?? node.title"
    >
      <span class="flex items-center gap-1.5 py-0.5">
        <MdiIcon
          v-if="node.icon"
          :path="node.icon"
          class="size-4 shrink-0 text-muted-foreground"
        />
        {{ node.title }}
      </span>
      <GroupMigrationFileTree
        v-if="node.children && node.children.length"
        :nodes="node.children"
        :depth="depth + 1"
      />
    </li>
  </ul>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";

interface TreeNode {
  id?: number;
  title: string;
  icon?: string;
  children?: TreeNode[];
}

withDefaults(defineProps<{ nodes: TreeNode[]; depth?: number }>(), { depth: 0 });
</script>
