import { useLocalStorage, useOnline } from "@vueuse/core";
import { useUserApi } from "~/composables/api";
import type { ShoppingListItemOut, ShoppingListItemsCollectionOut, ShoppingListOut } from "~/lib/api/types/household";

const localStorageKey = "shopping-list-queue";
const queueTimeout = 5 * 60 * 1000; // 5 minutes

type ItemQueueType = "create" | "update" | "delete";
const queueTypes: ItemQueueType[] = ["create", "update", "delete"];

export interface ShoppingListQueue {
  create: ShoppingListItemOut[];
  update: ShoppingListItemOut[];
  delete: ShoppingListItemOut[];
  conflictedIds?: string[];

  lastUpdate: number;
}

interface Storage {
  [key: string]: ShoppingListQueue;
}

export function useShoppingListItemActions(shoppingListId: string) {
  const isOnline = useOnline();
  const api = useUserApi();
  const storage = useLocalStorage(localStorageKey, {} as Storage, { deep: true });
  const queue = reactive(getQueue());
  const createsInFlight = new Set<string>();
  const conflictedIds = computed(() => new Set(queue.conflictedIds));
  const hasConflictedWrites = computed(() => conflictedIds.value.size > 0);
  const queueEmpty = computed(() => !queue.create.length && !queue.update.length && !queue.delete.length);
  if (queueEmpty.value) {
    queue.lastUpdate = Date.now();
  }

  storage.value[shoppingListId] = { ...queue };
  watch(
    () => queue,
    (value) => {
      storage.value[shoppingListId] = { ...value };
    },
    {
      deep: true,
      immediate: true,
    },
  );

  function isValidQueueObject(obj: any): obj is ShoppingListQueue {
    if (typeof obj !== "object" || obj === null) {
      return false;
    }

    const hasRequiredProps = "create" in obj && "update" in obj && "delete" in obj && "lastUpdate" in obj;
    if (!hasRequiredProps) {
      return false;
    }

    const arraysValid = Array.isArray(obj.create) && Array.isArray(obj.update) && Array.isArray(obj.delete);

    const lastUpdateValid = typeof obj.lastUpdate === "number" && !isNaN(new Date(obj.lastUpdate).getTime());

    const conflictsValid = obj.conflictedIds === undefined
      || (Array.isArray(obj.conflictedIds) && obj.conflictedIds.every(id => typeof id === "string"));

    return arraysValid && lastUpdateValid && conflictsValid;
  }

  function createEmptyQueue(): ShoppingListQueue {
    const newQueue = { create: [], update: [], delete: [], lastUpdate: Date.now() };
    return newQueue;
  }

  function getQueue(): ShoppingListQueue {
    try {
      const fetchedQueue = storage.value[shoppingListId];
      if (!isValidQueueObject(fetchedQueue)) {
        console.log("Invalid queue object in local storage; resetting queue.");
        return createEmptyQueue();
      }
      else {
        return fetchedQueue;
      }
    }
    catch (error) {
      console.log("Error validating queue object in local storage; resetting queue.", error);
      return createEmptyQueue();
    }
  }

  function removeFromQueue(itemQueue: ShoppingListItemOut[], item: ShoppingListItemOut): boolean {
    const index = itemQueue.findIndex(i => i.id === item.id);
    if (index === -1) {
      return false;
    }

    itemQueue.splice(index, 1);
    return true;
  }

  function mergeListItemsByLatest(
    list1: ShoppingListItemOut[],
    list2: ShoppingListItemOut[],
  ) {
    const mergedList = [...list1];
    list2.forEach((list2Item) => {
      const conflictingItem = mergedList.find(item => item.id === list2Item.id);
      if (conflictingItem
        && list2Item.updatedAt && conflictingItem.updatedAt
        && list2Item.updatedAt > conflictingItem.updatedAt) {
        mergedList.splice(mergedList.indexOf(conflictingItem), 1, list2Item);
      }
      else if (!conflictingItem) {
        mergedList.push(list2Item);
      }
    });
    return mergedList;
  }

  async function getList() {
    const response = await api.shopping.lists.getOne(shoppingListId);
    if (response.data) {
      // Merge pending local changes (both online and offline)
      const createAndUpdateQueues = mergeListItemsByLatest(queue.update, queue.create);
      const deleteQueueIds = new Set(queue.delete.map(item => item.id));

      const filteredLocalChanges = createAndUpdateQueues
        .filter(item => !deleteQueueIds.has(item.id))
        .map(copyItem);
      let mergedItems = mergeListItemsByLatest(response.data.listItems ?? [], filteredLocalChanges);
      mergedItems = mergedItems.filter(item => !deleteQueueIds.has(item.id));

      response.data.listItems = mergedItems;
    }
    return response.data;
  }

  function createItem(item: ShoppingListItemOut) {
    removeFromQueue(queue.create, item);
    removeFromQueue(queue.update, item);
    removeFromQueue(queue.delete, item);

    queue.create.push(copyItem(item));
  }

  function copyItem(item: ShoppingListItemOut): ShoppingListItemOut {
    // Queue entries contain API JSON. Keep them independent from mutable UI objects.
    return JSON.parse(JSON.stringify(item));
  }

  function updateItem(item: ShoppingListItemOut) {
    const shouldCreate = !createsInFlight.has(item.id) && removeFromQueue(queue.create, item);
    removeFromQueue(queue.update, item);
    removeFromQueue(queue.delete, item);

    if (shouldCreate) {
      // This item hasn't been created yet, so keep it in create queue with updated data
      queue.create.push(copyItem(item));
    }
    else {
      queue.update.push(copyItem(item));
    }
  }

  function deleteItem(item: ShoppingListItemOut) {
    const canceledCreate = !createsInFlight.has(item.id) && removeFromQueue(queue.create, item);
    if (canceledCreate) {
      // This item hasn't been created yet, so we don't need to delete it
      return;
    }

    removeFromQueue(queue.update, item);
    removeFromQueue(queue.delete, item);
    queue.delete.push(copyItem(item));
  }

  function getQueueItems(itemQueueType: ItemQueueType) {
    return queue[itemQueueType].filter(item => !conflictedIds.value.has(item.id));
  }

  function clearQueueItems(itemQueueType: ItemQueueType | "all", sentItems?: ShoppingListItemOut[]) {
    const types = itemQueueType === "all" ? queueTypes : [itemQueueType];
    const acknowledged = new Set(sentItems);
    for (const type of types) {
      // Each enqueue replaces the object. An acknowledgment for one revision must
      // never remove a different revision that happened to reuse the same ID.
      queue[type] = sentItems ? queue[type].filter(item => !acknowledged.has(item)) : [];
    }
    if (itemQueueType === "all" && !sentItems) queue.conflictedIds = [];
    if (queueEmpty.value) {
      queue.lastUpdate = Date.now();
    }
  }

  function discardConflictedChanges() {
    const conflictedItems = queueTypes.flatMap(type => queue[type].filter(item => conflictedIds.value.has(item.id)));
    clearQueueItems("all", conflictedItems);
    queue.conflictedIds = [];
  }

  function checkUpdateState(list: ShoppingListOut) {
    const cutoffDate = new Date(queue.lastUpdate + queueTimeout).toISOString();
    if (list.updatedAt && list.updatedAt > cutoffDate) {
      // If the queue is too far behind the shopping list to reliably do updates, we clear the queue
      console.log("Out of sync with server; clearing queue");
      clearQueueItems("all", queueTypes.flatMap(getQueueItems));
    }
  }

  // Whether a write failed during the current process run, leaving its items queued
  let failedWriteInRun = false;

  // Whether the last completed run couldn't save everything, so the page can tell the user
  const hasFailedWrites = ref(false);

  /**
   * Whether the server answered that it won't take this request, as opposed to a failure that may pass by itself.
   */
  function isRejection(error: any): boolean {
    const status: number | undefined = error?.response?.status;
    return !!status && status >= 400 && status < 500 && ![401, 408, 429].includes(status);
  }

  function settleCreate(item: ShoppingListItemOut, succeeded: boolean) {
    createsInFlight.delete(item.id);
    if (succeeded) return;

    const edited = queue.update.find(pending => pending.id === item.id);
    const deleted = queue.delete.find(pending => pending.id === item.id);
    if (edited) createItem(edited);
    if (deleted) {
      removeFromQueue(queue.create, item);
      removeFromQueue(queue.delete, deleted);
    }
  }

  /**
   * Processes the queue items and returns false if there was an unexpected error, which resets the queue.
   * A failed write isn't unexpected; its items stay queued and are sent again on the next run.
   */
  async function processQueueItems(
    action: (items: ShoppingListItemOut[]) => Promise<{
      data: ShoppingListItemsCollectionOut | null;
      error: unknown;
      response: unknown;
    }>,
    itemQueueType: ItemQueueType,
  ): Promise<boolean> {
    let itemsToProcess: ShoppingListItemOut[];
    function acknowledge(items: ShoppingListItemOut[], changes?: ShoppingListItemsCollectionOut | null) {
      if (itemQueueType === "create") {
        for (const item of items) settleCreate(item, true);
      }
      clearQueueItems(itemQueueType, items);

      if (!changes || itemQueueType === "delete") return;
      const missingIds = itemQueueType === "create"
        ? items.filter(item => !changes.createdItems.some(created => created.id === item.id)).map(item => item.id)
        : changes.deletedItems.map(item => item.id);
      if (!missingIds.length) return;
      // A merge can remove the submitted ID. Replaying its newer revision could
      // merge a second time, so keep the user's changes for explicit resolution.
      const pendingIds = new Set(queueTypes.flatMap(type => queue[type].map(item => item.id)));
      const conflicts = missingIds.filter(id => pendingIds.has(id));
      if (conflicts.length) {
        queue.conflictedIds = [...new Set([...conflictedIds.value, ...conflicts])];
      }
    }

    try {
      itemsToProcess = [...getQueueItems(itemQueueType)];
      if (!itemsToProcess.length) {
        return true;
      }
    }
    catch (error) {
      console.log(`Error fetching queue items of type ${itemQueueType}:`, error);
      clearQueueItems(itemQueueType);
      return false;
    }

    if (itemQueueType === "create") {
      for (const item of itemsToProcess) createsInFlight.add(item.id);
    }

    try {
      // the API client resolves failed writes (network errors and 4xx/5xx alike) instead of rejecting,
      // so the items stay queued unless the response says they made it
      const result = await action(itemsToProcess);
      if (!result?.error) {
        if (result?.response || isOnline.value) {
          acknowledge(itemsToProcess, result?.data);
        }
        return true;
      }

      console.log(`Failed to write queue items of type ${itemQueueType}; keeping them queued`);
      failedWriteInRun = true;

      // a rejected request says nothing about which item caused it, so send them one by one;
      // otherwise a single item the server will never accept would hold back all the others
      if (itemsToProcess.length > 1 && isRejection(result.error)) {
        for (const item of itemsToProcess) {
          const itemResult = await action([item]);
          if (!itemResult?.error && (itemResult?.response || isOnline.value)) {
            acknowledge([item], itemResult?.data);
          }
        }
      }
    }
    catch (error) {
      console.log(`Error processing queue items of type ${itemQueueType}:`, error);
      clearQueueItems(itemQueueType, itemsToProcess);
      return false;
    }
    finally {
      if (itemQueueType === "create") {
        for (const item of itemsToProcess) {
          if (createsInFlight.has(item.id)) settleCreate(item, false);
        }
      }
    }

    return true;
  }

  async function processPending() {
    if (!queueTypes.some(type => getQueueItems(type).length)) {
      if (queueEmpty.value) queue.lastUpdate = Date.now();
      hasFailedWrites.value = false;
      return;
    }

    const data = await getList();
    if (!data) {
      return;
    }
    checkUpdateState(data);
    failedWriteInRun = false;

    // We send each bulk request one at a time, since the backend may merge items
    // "failures" here refers to an actual error, rather than failing to reach the backend
    let failures = 0;
    if (!(await processQueueItems(async (items) => {
      const result = await api.shopping.items.deleteMany(items);
      return { ...result, data: null };
    }, "delete"))) failures++;
    if (!(await processQueueItems(items => api.shopping.items.updateMany(items), "update"))) failures++;
    if (!(await processQueueItems(items => api.shopping.items.createMany(items), "create"))) failures++;

    // If we're online with no failed writes, or the queue is empty, the queue is fully processed, so we're up to date
    // Otherwise, if all three queue processes failed, we've already reset the queue, so we need to reset the date
    hasFailedWrites.value = failedWriteInRun;
    if ((isOnline.value && !failedWriteInRun) || queueEmpty.value || failures === 3) {
      queue.lastUpdate = Date.now();
    }
  }

  let inFlight: Promise<void> | undefined;

  function process(): Promise<void> {
    inFlight ??= processPending().finally(() => {
      inFlight = undefined;
    });
    return inFlight;
  }

  return {
    getList,
    createItem,
    updateItem,
    deleteItem,
    process,
    hasFailedWrites,
    hasConflictedWrites,
    discardConflictedChanges,

    __testing__: {
      queue,
      clearQueueItems,
      createEmptyQueue,
    },
  };
}
