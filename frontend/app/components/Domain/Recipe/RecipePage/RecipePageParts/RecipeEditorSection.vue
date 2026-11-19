<script setup lang="ts">
/** A titled card in the recipe editor; `id` is the jump-list anchor. */
defineProps<{ id: string; title: string; description?: string }>();
</script>

<template>
  <section
    :id="id"
    :aria-labelledby="`${id}-title`"
    class="scroll-mt-36 rounded-panel border bg-card p-5 font-sans sm:p-6"
  >
    <header class="mb-5 flex flex-wrap items-center gap-3">
      <div class="min-w-0 flex-1">
        <h2
          :id="`${id}-title`"
          class="m-0 text-lg font-bold tracking-tight"
        >
          {{ title }}
        </h2>
        <p
          v-if="description"
          class="m-0 mt-0.5 text-sm text-muted-foreground"
        >
          {{ description }}
        </p>
      </div>
      <slot name="actions" />
    </header>
    <slot />
  </section>
</template>
