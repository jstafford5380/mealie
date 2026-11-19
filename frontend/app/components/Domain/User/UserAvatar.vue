<template>
  <Avatar
    v-if="userId"
    v-bind="$attrs"
    :style="{ width: `${px}px`, height: `${px}px` }"
    :title="tooltip && user ? user.fullName : undefined"
  >
    <AvatarImage
      :src="imageURL"
      :alt="user?.fullName || ''"
    />
    <AvatarFallback
      class="bg-highlight font-bold text-highlight-foreground"
      :style="{ fontSize: `${Math.max(10, Math.round(px * 0.36))}px` }"
    >
      {{ initials }}
    </AvatarFallback>
  </Avatar>
</template>

<script setup lang="ts">
import { Avatar, AvatarFallback, AvatarImage } from "~/components/ui/avatar";
import { useUserStore } from "~/composables/store/use-user-store";

defineOptions({ inheritAttrs: false });

const props = defineProps({
  userId: {
    type: String,
    required: true,
  },
  list: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: "42",
  },
  tooltip: {
    type: Boolean,
    default: true,
  },
});

// `list` avatars keep the old 40px list-item size
const px = computed(() => (props.list ? 40 : Number(props.size) || 42));

const auth = useMealieAuth();
const { store: users } = useUserStore();
const user = computed(() => {
  return users.value.find(user => user.id === props.userId);
});

const initials = computed(() => (user.value?.fullName || user.value?.username || "?")
  .split(/\s+/)
  .filter(Boolean)
  .slice(0, 2)
  .map(part => part[0]!.toUpperCase())
  .join(""));

const imageURL = computed(() => {
  // Note: auth.user is a ref now
  const authUser = auth.user.value;
  const key = authUser?.cacheKey ?? "";
  return `/api/media/users/${props.userId}/profile.webp?cacheKey=${key}`;
});
</script>
