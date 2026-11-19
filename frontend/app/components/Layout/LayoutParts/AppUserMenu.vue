<script setup lang="ts">
import { ChevronsUpDownIcon, LogInIcon } from "@lucide/vue";
import { useDark } from "@vueuse/core";
import { Avatar, AvatarFallback, AvatarImage } from "~/components/ui/avatar";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useLoggedInState } from "~/composables/use-logged-in-state";

const emit = defineEmits<{ "open-language": [] }>();

const auth = useMealieAuth();
const { $globals } = useNuxtApp();
const { loggedIn, isOwnGroup } = useLoggedInState();
const user = computed(() => auth.user.value);
const isDark = useDark();

const initials = computed(() => (user.value?.fullName || user.value?.username || "?")
  .split(/\s+/)
  .map(part => part[0])
  .join("")
  .slice(0, 2)
  .toUpperCase());
const avatarUrl = computed(() => (user.value ? `/api/media/users/${user.value.id}/profile.webp?cacheKey=${user.value.cacheKey ?? ""}` : ""));

async function logout() {
  try {
    await auth.signOut("/login?direct=1");
  }
  catch (e) {
    console.error(e);
  }
}
</script>

<template>
  <DropdownMenu :modal="false">
    <DropdownMenuTrigger as-child>
      <button
        v-if="loggedIn && user"
        type="button"
        class="flex w-full items-center gap-2.5 rounded-item p-1.5 text-start transition-colors hover:bg-sidebar-highlight/70 focus-visible:outline-2 focus-visible:outline-sidebar-ring"
      >
        <Avatar class="size-9">
          <AvatarImage
            :src="avatarUrl"
            alt=""
          />
          <AvatarFallback class="bg-highlight text-[13px] font-bold text-highlight-foreground">
            {{ initials }}
          </AvatarFallback>
        </Avatar>
        <span class="flex min-w-0 flex-1 flex-col leading-tight">
          <span class="truncate text-sm font-semibold text-foreground">{{ user.fullName }}</span>
          <span class="truncate text-xs text-muted-foreground">{{ user.household }}</span>
        </span>
        <ChevronsUpDownIcon class="size-4 text-muted-foreground" />
      </button>
      <Button
        v-else
        variant="outline"
        class="w-full justify-start"
      >
        <MdiIcon
          :path="$globals.icons.cog"
          class="size-[18px]"
        />
        {{ $t("general.settings") }}
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent
      side="top"
      align="start"
      class="w-[var(--reka-dropdown-menu-trigger-width)] min-w-60"
    >
      <template v-if="loggedIn && user">
        <DropdownMenuLabel class="font-normal">
          <span class="block truncate text-sm font-semibold">{{ user.fullName }}</span>
          <span class="block truncate text-xs text-muted-foreground">{{ user.email }}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem as-child>
          <NuxtLink to="/user/profile">
            <MdiIcon :path="$globals.icons.user" />
            {{ $t("profile.user-settings") }}
          </NuxtLink>
        </DropdownMenuItem>
        <DropdownMenuItem
          v-if="isOwnGroup"
          as-child
        >
          <NuxtLink :to="`/user/${user.id}/favorites`">
            <MdiIcon :path="$globals.icons.heart" />
            {{ $t("user.favorite-recipes") }}
          </NuxtLink>
        </DropdownMenuItem>
        <DropdownMenuItem
          v-if="user.canOrganize"
          as-child
        >
          <NuxtLink to="/group/data">
            <MdiIcon :path="$globals.icons.manageData" />
            {{ $t("data-pages.data-management") }}
          </NuxtLink>
        </DropdownMenuItem>
        <DropdownMenuItem
          v-if="user.admin"
          as-child
        >
          <NuxtLink to="/admin/site-settings">
            <MdiIcon :path="$globals.icons.wrench" />
            {{ $t("settings.admin-settings") }}
          </NuxtLink>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
      </template>
      <DropdownMenuItem @select="emit('open-language')">
        <MdiIcon :path="$globals.icons.translate" />
        {{ $t("sidebar.language") }}
      </DropdownMenuItem>
      <DropdownMenuItem @select="isDark = !isDark">
        <MdiIcon :path="isDark ? $globals.icons.weatherSunny : $globals.icons.weatherNight" />
        {{ isDark ? $t("settings.theme.light-mode") : $t("settings.theme.dark-mode") }}
      </DropdownMenuItem>
      <DropdownMenuSeparator />
      <DropdownMenuItem
        v-if="loggedIn"
        @select="logout"
      >
        <MdiIcon :path="$globals.icons.logout" />
        {{ $t("user.logout") }}
      </DropdownMenuItem>
      <DropdownMenuItem
        v-else
        as-child
      >
        <NuxtLink to="/login">
          <LogInIcon />
          {{ $t("user.login") }}
        </NuxtLink>
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
