<template>
  <form
    class="rounded-panel border bg-card p-5 font-sans sm:p-6"
    @submit.prevent="createByName(newRecipeName)"
  >
    <h2 class="m-0 text-xl font-bold tracking-tight">
      {{ $t('recipe.create-recipe') }}
    </h2>
    <p class="m-0 mt-1 text-[15px] text-muted-foreground">
      {{ $t('recipe.create-a-recipe-by-providing-the-name-all-recipes-must-have-unique-names') }}
    </p>
    <div class="mt-4">
      <TextField
        v-model="newRecipeName"
        autofocus
        validate-on="blur"
        :label="$t('recipe.recipe-name')"
        :rules="[validators.required]"
        :hint="$t('recipe.new-recipe-names-must-be-unique')"
      />
    </div>
    <div class="mt-5 flex flex-wrap items-center justify-end gap-3 border-t pt-4">
      <Button
        type="submit"
        :disabled="newRecipeName.trim() === '' || state.loading"
      >
        <LoaderCircleIcon
          v-if="state.loading"
          class="size-4 animate-spin"
        />
        {{ $t('recipe.create-recipe') }}
      </Button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import TextField from "~/components/ui/field/TextField.vue";
import type { AxiosResponse } from "axios";
import { useUserApi } from "~/composables/api";
import { validators } from "~/composables/use-validators";

const state = reactive({
  error: false,
  loading: false,
});
const auth = useMealieAuth();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

const api = useUserApi();
const router = useRouter();

function handleResponse(response: AxiosResponse<string> | null, edit = false) {
  if (response?.status !== 201) {
    state.error = true;
    state.loading = false;
    return;
  }
  router.push(`/g/${groupSlug.value}/r/${response.data}?edit=${edit.toString()}`);
}

const newRecipeName = ref("");

async function createByName(name: string) {
  if (name.trim() === "") {
    return;
  }
  const { response } = await api.recipes.createOne({ name });
  handleResponse(response as any, true);
}
</script>
