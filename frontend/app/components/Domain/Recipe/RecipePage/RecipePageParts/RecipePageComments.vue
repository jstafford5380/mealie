<template>
  <section
    class="mx-auto w-full max-w-[760px] font-sans"
    :aria-label="$t('recipe.comments')"
  >
    <h2 class="m-0 mb-4 flex items-center gap-2 text-xl font-bold tracking-tight">
      {{ $t("recipe.comments") }}
      <span
        v-if="recipe.comments.length"
        class="rounded-full bg-subtle px-2 text-sm font-semibold text-subtle-foreground"
      >{{ recipe.comments.length }}</span>
    </h2>
    <form
      v-if="user.id"
      class="mb-6 flex items-start gap-3"
      @submit.prevent="submitComment"
    >
      <Avatar class="mt-0.5 size-9">
        <AvatarImage
          :src="avatarUrl(user.id)"
          alt=""
        />
        <AvatarFallback class="bg-highlight text-xs font-bold text-highlight-foreground">
          {{ initials(user.fullName) }}
        </AvatarFallback>
      </Avatar>
      <div class="flex min-w-0 flex-1 flex-col gap-2">
        <textarea
          v-model="comment"
          rows="2"
          :aria-label="$t('recipe.join-the-conversation')"
          :placeholder="$t('recipe.join-the-conversation')"
          class="field-sizing-content min-h-[4.5rem] w-full resize-none rounded-control border border-input bg-card px-3 py-2 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
          @keydown.meta.enter="submitComment"
          @keydown.ctrl.enter="submitComment"
        />
        <Button
          v-if="comment.trim()"
          type="submit"
          class="self-end"
        >
          {{ $t("general.submit") }}
        </Button>
      </div>
    </form>
    <ul class="m-0 flex list-none flex-col gap-5 p-0">
      <li
        v-for="recipeComment in recipe.comments"
        :key="recipeComment.id"
        class="group flex items-start gap-3"
      >
        <Avatar class="mt-0.5 size-9">
          <AvatarImage
            :src="avatarUrl(recipeComment.userId)"
            alt=""
          />
          <AvatarFallback class="bg-highlight text-xs font-bold text-highlight-foreground">
            {{ initials(recipeComment.user.fullName) }}
          </AvatarFallback>
        </Avatar>
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-baseline gap-x-2 text-sm">
            <span class="font-semibold">{{ recipeComment.user.fullName }}</span>
            <time
              class="text-muted-foreground"
              :datetime="recipeComment.createdAt"
            >{{ $d(Date.parse(recipeComment.createdAt), "medium") }}</time>
            <button
              v-if="user.id == recipeComment.user.id || user.admin"
              type="button"
              class="ms-auto rounded-item px-1.5 text-xs font-semibold text-destructive opacity-70 hover:bg-destructive/10 hover:opacity-100"
              @click="deleteComment(recipeComment.id)"
            >
              {{ $t("general.delete") }}
            </button>
          </div>
          <SafeMarkdown
            class="mt-0.5 text-[15.5px] leading-relaxed [&_p]:m-0 [&_p+p]:mt-2"
            :source="recipeComment.text"
          />
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import type { RecipeOut } from "~/lib/api/types/recipe";
import { Avatar, AvatarFallback, AvatarImage } from "~/components/ui/avatar";
import { Button } from "~/components/ui/button";
import { usePageUser } from "~/composables/recipe-page/shared-state";
import SafeMarkdown from "~/components/global/SafeMarkdown.vue";

const recipe = defineModel<RecipeOut>({ required: true });
const api = useUserApi();
const { user } = usePageUser();
const comment = ref("");

function avatarUrl(id: string) {
  return `/api/media/users/${id}/profile.webp`;
}
function initials(name?: string | null) {
  return (name || "?").split(/\s+/).map(p => p[0]).join("").slice(0, 2).toUpperCase();
}

async function submitComment() {
  const text = comment.value.trim();
  if (!text) {
    return;
  }
  const { data } = await api.recipes.comments.createOne({
    recipeId: recipe.value.id,
    text,
  });

  if (data) {
    recipe.value.comments.push(data);
  }

  comment.value = "";
}

async function deleteComment(id: string) {
  const { response } = await api.recipes.comments.deleteOne(id);

  if (response?.status === 200) {
    recipe.value.comments = recipe.value.comments.filter(comment => comment.id !== id);
  }
}
</script>
