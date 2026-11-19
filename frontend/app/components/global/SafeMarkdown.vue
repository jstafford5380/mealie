<template>
  <div v-html="value" />
</template>

<script setup lang="ts">
import type { PropType } from "vue";
import { renderMarkdown } from "~/lib/sanitize";

const props = defineProps({
  source: {
    type: String as PropType<string | null>,
    default: "",
  },
});

const { $appInfo } = useNuxtApp();

const value = computed(() => renderMarkdown(props.source, $appInfo?.allowedIframeHosts ?? []));
</script>

<style scoped>
:deep(table) {
  border-collapse: collapse;
  width: 100%;
}

:deep(th),
:deep(td) {
  border: 1px solid;
  padding: 8px;
  text-align: left;
}

:deep(th) {
  font-weight: bold;
}

:deep(ul),
:deep(ol) {
  margin: 8px 0;
  padding-inline-start: 20px;
}

:deep(ul) {
  list-style: disc;
}

:deep(ol) {
  list-style: decimal;
}

:deep(a) {
  color: var(--primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}

:deep(h1),
:deep(h2),
:deep(h3),
:deep(h4) {
  margin: 0.75em 0 0.35em;
  font-weight: 700;
  line-height: 1.25;
}

:deep(h1) {
  font-size: 1.5em;
}

:deep(h2) {
  font-size: 1.3em;
}

:deep(h3) {
  font-size: 1.15em;
}

:deep(blockquote) {
  margin: 0.5em 0;
  padding-inline-start: 0.75em;
  border-inline-start: 3px solid var(--border);
  color: var(--muted-foreground);
}

:deep(code) {
  border-radius: 4px;
  background: var(--muted);
  padding: 0.1em 0.3em;
  font-size: 0.9em;
}

/* The app removes paragraph margins globally, which would show a blank line in the
   source as a plain line break. Space only between paragraphs, so a single paragraph
   keeps its layout. */
:deep(p + p) {
  margin-top: 0.5em;
}
</style>
