<script setup lang="ts">
import type { AppCreateLink } from "~/composables/use-app-navigation";
import { PlusIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";

withDefaults(defineProps<{
  links: AppCreateLink[];
  /** "button" for the sidebar, "fab" for the phone tab bar. */
  variant?: "button" | "fab";
}>(), {
  variant: "button",
});
</script>

<template>
  <DropdownMenu :modal="false">
    <DropdownMenuTrigger as-child>
      <Button
        v-if="variant === 'button'"
        class="w-full"
      >
        <PlusIcon class="size-[18px]" />
        {{ $t("new-recipe.add-recipe") }}
      </Button>
      <button
        v-else
        type="button"
        class="-mt-3 inline-flex size-[52px] items-center justify-center rounded-[16px] bg-primary text-primary-foreground shadow-md transition-transform active:scale-95 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        :aria-label="$t('new-recipe.add-recipe')"
      >
        <PlusIcon class="size-6" />
      </button>
    </DropdownMenuTrigger>
    <DropdownMenuContent
      :side="variant === 'fab' ? 'top' : 'bottom'"
      :align="variant === 'fab' ? 'center' : 'start'"
      :side-offset="8"
      class="w-72"
    >
      <DropdownMenuItem
        v-for="link in links"
        :key="link.key"
        as-child
        class="items-start gap-3 py-2.5"
      >
        <NuxtLink :to="link.to">
          <span class="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-item bg-highlight text-highlight-foreground">
            <MdiIcon
              :path="link.icon"
              class="size-[18px] text-highlight-foreground"
            />
          </span>
          <span class="flex min-w-0 flex-col">
            <span class="text-sm font-semibold text-foreground">{{ link.title }}</span>
            <span class="text-[13px] text-muted-foreground">{{ link.subtitle }}</span>
          </span>
        </NuxtLink>
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
