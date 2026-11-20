import * as vuecore from "@vueuse/core";
import { beforeEach, describe, expect, test, vi } from "vitest";
import type { ShoppingListQueue } from "../use-shopping-list-item-actions";
import { useShoppingListItemActions } from "../use-shopping-list-item-actions";
import { MOCK_ITEM, MOCK_SHOPPING_LIST } from "./mocks";

const getOne = vi.fn().mockResolvedValue({ data: MOCK_SHOPPING_LIST });

const deleteMany = vi.fn().mockImplementation(async () => { });
const updateMany = vi.fn().mockImplementation(async () => { });
const createMany = vi.fn().mockImplementation(async () => { });

vi.mock("@vueuse/core", { spy: true });
const isOnline = ref(true);
const storedValue = ref<{ [key: string]: ShoppingListQueue } | undefined>(undefined);
vi.mocked(vuecore.useOnline).mockReturnValue(isOnline);
vi.mocked(vuecore.useStorage).mockReturnValue(storedValue);

vi.mock("~/composables/api", () => ({
  useUserApi: () => ({
    shopping: {
      lists: { getOne },
      items: { deleteMany, updateMany, createMany },
    },
  }),
}));

describe("useShoppingListItemActions", () => {
  const {
    getList,
    createItem,
    deleteItem,
    updateItem,
    process,
    hasFailedWrites,
    hasConflictedWrites,
    discardConflictedChanges,
    __testing__: { queue, clearQueueItems },
  } = useShoppingListItemActions("list_id");

  beforeEach(() => {
    vi.clearAllMocks();
    isOnline.value = true;
    storedValue.value = undefined;
    clearQueueItems("all");
  });

  test("getList returns a shopping list", async () => {
    const list = await getList();
    expect(list).toBe(MOCK_SHOPPING_LIST);
  });
  test("create item creates an item", () => {
    createItem(MOCK_ITEM);
    expect(queue.create).toContainEqual(MOCK_ITEM);
  });
  describe("updateItem", () => {
    test("update item updates an item", () => {
      updateItem(MOCK_ITEM);
      expect(queue.update).toContainEqual(MOCK_ITEM);
    });
    test("ignores a newly created item", () => {
      const updatedItem = { ...MOCK_ITEM, quantity: 2000 };
      createItem(MOCK_ITEM);
      updateItem(updatedItem);
      expect(queue.update).not.toContainEqual(MOCK_ITEM);
      expect(queue.create).not.toContainEqual(MOCK_ITEM);
      expect(queue.create).toContainEqual(updatedItem);
    });
  });
  describe("deleteItem", () => {
    test("delete item deletes an item", () => {
      deleteItem(MOCK_ITEM);
      expect(queue.delete).toContainEqual(MOCK_ITEM);
    });
    test("undoes a newly created item", () => {
      createItem(MOCK_ITEM);
      deleteItem(MOCK_ITEM);
      expect(queue.delete).not.toContainEqual(MOCK_ITEM);
      expect(queue.create).not.toContainEqual(MOCK_ITEM);
    });
  });
  describe("process processes the queue", () => {
    function holdWrite(write: typeof updateMany) {
      const started = Promise.withResolvers<undefined>();
      const completed = Promise.withResolvers<unknown>();
      write.mockImplementationOnce(() => {
        started.resolve(undefined);
        return completed.promise;
      });
      return { started: started.promise, complete: completed.resolve };
    }

    test("preserves a newer same-item edit and coalesces concurrent flushes", async () => {
      const item = { ...MOCK_ITEM, quantity: 1 };
      const pendingWrite = holdWrite(updateMany);
      updateItem(item);
      const firstFlush = process();
      await pendingWrite.started;

      item.quantity = 2;
      updateItem(item);
      expect(process()).toBe(firstFlush);
      expect(updateMany).toHaveBeenCalledExactlyOnceWith([{ ...item, quantity: 1 }]);

      pendingWrite.complete(undefined);
      await firstFlush;
      expect(queue.update).toEqual([item]);
      expect(updateMany).toHaveBeenCalledTimes(1);

      await process();
      expect(updateMany).toHaveBeenLastCalledWith([item]);
      expect(queue.update).toEqual([]);
    });

    test("sends a newer edit to a successfully created item as an update", async () => {
      const item = { ...MOCK_ITEM, quantity: 1 };
      const edit = { ...item, quantity: 2 };
      const pendingWrite = holdWrite(createMany);
      createItem(item);
      const firstFlush = process();
      await pendingWrite.started;

      updateItem(edit);
      pendingWrite.complete(undefined);
      await firstFlush;
      expect(queue.create).toEqual([]);
      expect(queue.update).toEqual([edit]);

      await process();
      expect(createMany).toHaveBeenCalledExactlyOnceWith([item]);
      expect(updateMany).toHaveBeenCalledExactlyOnceWith([edit]);
    });

    test("sends a delete when a create already in flight succeeds", async () => {
      const pendingWrite = holdWrite(createMany);
      createItem(MOCK_ITEM);
      const firstFlush = process();
      await pendingWrite.started;

      deleteItem(MOCK_ITEM);
      pendingWrite.complete(undefined);
      await firstFlush;
      expect(queue.create).toEqual([]);
      expect(queue.delete).toEqual([MOCK_ITEM]);

      await process();
      expect(deleteMany).toHaveBeenCalledExactlyOnceWith([MOCK_ITEM]);
    });

    test("retries a rejected create with the latest edit", async () => {
      const edit = { ...MOCK_ITEM, quantity: 2 };
      const pendingWrite = holdWrite(createMany);
      createItem(MOCK_ITEM);
      const firstFlush = process();
      await pendingWrite.started;

      updateItem(edit);
      pendingWrite.complete({ error: new Error("create failed") });
      await firstFlush;
      expect(queue.create).toEqual([edit]);
      expect(queue.update).toEqual([]);
    });

    test("keeps a newer edit to a merged create until it is explicitly discarded", async () => {
      const edit = { ...MOCK_ITEM, quantity: 2 };
      const mergedItem = { ...MOCK_ITEM, id: "canonical", quantity: 3 };
      const pendingWrite = holdWrite(createMany);
      createItem(MOCK_ITEM);
      const firstFlush = process();
      await pendingWrite.started;

      updateItem(edit);
      pendingWrite.complete({ data: { createdItems: [], updatedItems: [mergedItem], deletedItems: [] } });
      await firstFlush;
      expect(hasConflictedWrites.value).toBe(true);
      expect(queue.update).toEqual([edit]);

      await process();
      expect(createMany).toHaveBeenCalledTimes(1);
      expect(updateMany).not.toHaveBeenCalled();

      discardConflictedChanges();
      expect(queue.update).toEqual([]);
      expect(hasConflictedWrites.value).toBe(false);
    });

    test("does not send a newer delete to an item removed by a merge", async () => {
      const pendingWrite = holdWrite(updateMany);
      updateItem(MOCK_ITEM);
      const firstFlush = process();
      await pendingWrite.started;

      deleteItem(MOCK_ITEM);
      pendingWrite.complete({ data: { createdItems: [], updatedItems: [], deletedItems: [MOCK_ITEM] } });
      await firstFlush;
      expect(hasConflictedWrites.value).toBe(true);
      expect(queue.delete).toEqual([MOCK_ITEM]);

      await process();
      expect(deleteMany).not.toHaveBeenCalled();
    });

    test("normally", async () => {
      const updatedItem = { ...MOCK_ITEM, id: "update" };
      const createdItem = { ...MOCK_ITEM, id: "create" };
      const deletedItem = { ...MOCK_ITEM, id: "delete" };

      updateItem(updatedItem);
      createItem(createdItem);
      deleteItem(deletedItem);

      await process();
      expect(queue.update).not.toContainEqual(updatedItem);
      expect(queue.create).not.toContainEqual(createdItem);
      expect(queue.delete).not.toContainEqual(deletedItem);
    });
    test("clears the queue if there was an error merging", async () => {
      updateMany.mockThrowOnce("💥 Woe, exception be upon ye 💥");
      createMany.mockThrowOnce("💥 Woe, exception be upon ye 💥");
      deleteMany.mockThrowOnce("💥 Woe, exception be upon ye 💥");

      const updatedItem = { ...MOCK_ITEM, id: "update" };
      const createdItem = { ...MOCK_ITEM, id: "create" };
      const deletedItem = { ...MOCK_ITEM, id: "delete" };

      updateItem(updatedItem);
      createItem(createdItem);
      deleteItem(deletedItem);

      await process();
      expect(queue.update).not.toContainEqual(updatedItem);
      expect(queue.create).not.toContainEqual(createdItem);
      expect(queue.delete).not.toContainEqual(deletedItem);
    });
    test("doesn't clear the queue if offline", async () => {
      isOnline.value = false;

      const updatedItem = { ...MOCK_ITEM, id: "update" };
      const createdItem = { ...MOCK_ITEM, id: "create" };
      const deletedItem = { ...MOCK_ITEM, id: "delete" };

      updateItem(updatedItem);
      createItem(createdItem);
      deleteItem(deletedItem);

      await process();
      expect(queue.update).toContainEqual(updatedItem);
      expect(queue.create).toContainEqual(createdItem);
      expect(queue.delete).toContainEqual(deletedItem);
    });
    describe("when a write fails", () => {
      // same shape as request.safe in api-client.ts: failed writes resolve rather than reject
      function failedResponse(status?: number) {
        const error = Object.assign(new Error("request failed"), status ? { response: { status } } : {});
        return { response: null, error, data: null };
      }

      function successfulWrite(status: number) {
        return { response: { status }, error: null, data: { createdItems: [], updatedItems: [], deletedItems: [] } };
      }

      test.each([
        ["a network error", undefined],
        ["a 400", 400],
        ["a 401", 401],
        ["a 404", 404],
        ["a 422", 422],
        ["a 500", 500],
        ["a 503", 503],
      ])("keeps all three queues after %s", async (_, status) => {
        getOne.mockResolvedValue({ data: MOCK_SHOPPING_LIST });
        deleteMany.mockResolvedValueOnce(failedResponse(status));
        updateMany.mockResolvedValueOnce(failedResponse(status));
        createMany.mockResolvedValueOnce(failedResponse(status));

        const updatedItem = { ...MOCK_ITEM, id: "update" };
        const createdItem = { ...MOCK_ITEM, id: "create" };
        const deletedItem = { ...MOCK_ITEM, id: "delete" };

        updateItem(updatedItem);
        createItem(createdItem);
        deleteItem(deletedItem);

        await process();
        expect(queue.update.map(item => item.id)).toEqual(["update"]);
        expect(queue.create.map(item => item.id)).toEqual(["create"]);
        expect(queue.delete.map(item => item.id)).toEqual(["delete"]);
      });

      test("only keeps the queue whose write failed", async () => {
        getOne.mockResolvedValue({ data: MOCK_SHOPPING_LIST });
        updateMany.mockResolvedValueOnce(failedResponse(500));
        createMany.mockResolvedValueOnce(successfulWrite(201));

        updateItem({ ...MOCK_ITEM, id: "update" });
        createItem({ ...MOCK_ITEM, id: "create" });

        await process();
        expect(queue.update.map(item => item.id)).toEqual(["update"]);
        expect(queue.create).toEqual([]);
      });

      test("sends the kept items again on the next run, then clears them", async () => {
        getOne.mockResolvedValue({ data: MOCK_SHOPPING_LIST });
        updateMany.mockResolvedValueOnce(failedResponse(503));
        updateMany.mockResolvedValueOnce(successfulWrite(200));

        updateItem({ ...MOCK_ITEM, id: "update" });

        await process();
        expect(queue.update.map(item => item.id)).toEqual(["update"]);

        await process();
        expect(updateMany).toHaveBeenCalledTimes(2);
        expect(updateMany.mock.calls[1]?.[0].map((item: { id: string }) => item.id)).toEqual(["update"]);
        expect(queue.update).toEqual([]);
      });

      test("treats the queue like an offline one, so its age keeps counting", async () => {
        getOne.mockResolvedValue({ data: MOCK_SHOPPING_LIST });
        updateMany.mockResolvedValueOnce(failedResponse(500));

        updateItem({ ...MOCK_ITEM, id: "update" });
        queue.lastUpdate = 1000;

        await process();
        expect(queue.lastUpdate).toBe(1000);
      });

      test("sends the items one by one after a rejection, so one bad item can't hold back the others", async () => {
        getOne.mockResolvedValue({ data: MOCK_SHOPPING_LIST });
        updateMany.mockResolvedValueOnce(failedResponse(422));
        updateMany.mockResolvedValueOnce(successfulWrite(200));
        updateMany.mockResolvedValueOnce(failedResponse(422));

        updateItem({ ...MOCK_ITEM, id: "good" });
        updateItem({ ...MOCK_ITEM, id: "bad" });

        await process();
        expect(updateMany).toHaveBeenCalledTimes(3);
        expect(queue.update.map(item => item.id)).toEqual(["bad"]);
      });

      test.each([500, 503, 401, 429, undefined])("doesn't split the request after a temporary failure (%s)", async (status) => {
        getOne.mockResolvedValue({ data: MOCK_SHOPPING_LIST });
        updateMany.mockResolvedValueOnce(failedResponse(status));

        updateItem({ ...MOCK_ITEM, id: "a" });
        updateItem({ ...MOCK_ITEM, id: "b" });

        await process();
        expect(updateMany).toHaveBeenCalledTimes(1);
        expect(queue.update).toHaveLength(2);
      });

      test("reports failed writes until a run saves everything", async () => {
        getOne.mockResolvedValue({ data: MOCK_SHOPPING_LIST });
        updateMany.mockResolvedValueOnce(failedResponse(500));
        updateMany.mockResolvedValueOnce(failedResponse(500));

        updateItem({ ...MOCK_ITEM, id: "update" });
        await process();
        expect(hasFailedWrites.value).toBe(true);

        await process();
        expect(hasFailedWrites.value).toBe(true);

        await process();
        expect(hasFailedWrites.value).toBe(false);
      });

      test("keeps the local change visible in getList", async () => {
        const checkedItem = { ...MOCK_ITEM, id: "server-item", checked: true, updatedAt: "200" };
        getOne.mockImplementation(async () => ({
          data: { ...MOCK_SHOPPING_LIST, listItems: [{ ...MOCK_ITEM, id: "server-item", checked: false, updatedAt: "100" }] },
        }));
        updateMany.mockResolvedValueOnce(failedResponse(500));

        updateItem(checkedItem);
        await process();

        const list = await getList();
        expect(list?.listItems?.find(item => item.id === "server-item")?.checked).toBe(true);
        getOne.mockReset();
        getOne.mockResolvedValue({ data: MOCK_SHOPPING_LIST });
      });
    });
    test("doesn't do anything if the queue is empty", async () => {
      await process();
      expect(updateMany).not.toHaveBeenCalled();
      expect(createMany).not.toHaveBeenCalled();
      expect(deleteMany).not.toHaveBeenCalled();
    });
    test("doesn't do anything if we can't find the list", async () => {
      getOne.mockResolvedValue({ data: undefined });
      const updatedItem = { ...MOCK_ITEM, id: "update" };
      const createdItem = { ...MOCK_ITEM, id: "create" };
      const deletedItem = { ...MOCK_ITEM, id: "delete" };

      updateItem(updatedItem);
      createItem(createdItem);
      deleteItem(deletedItem);

      await process();
      expect(updateMany).not.toHaveBeenCalled();
      expect(createMany).not.toHaveBeenCalled();
      expect(deleteMany).not.toHaveBeenCalled();
    });
  });
  describe("getQueue", () => {
    test("fetches from local storage if available", () => {
      const { queue, createEmptyQueue } = useShoppingListItemActions("list_id").__testing__;
      expect(queue).not.toEqual(createEmptyQueue);
    });
  });
});
