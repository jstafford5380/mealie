import { describe, expect, expectTypeOf, test, vi } from "vitest";
import { ref } from "vue";
import { useStoreActions } from "../use-actions-factory";
import type { BaseCRUDAPI } from "~/lib/api/base/base-clients";

describe("useStoreActions", () => {
  type CreateInput = { name: string };
  type UpdateInput = { displayName: string };
  type Item = { id: string; name: string };

  const mockApi = {
    getAll: vi.fn(),
    createOne: vi.fn(),
    updateOne: vi.fn(),
    deleteOne: vi.fn(),
  } as unknown as BaseCRUDAPI<CreateInput, Item, UpdateInput>;

  const mockStore = ref([]);
  const mockLoading = ref(false);
  const mockInitialized = ref(false);

  test("keeps create and update payloads distinct from the read model", () => {
    const actions = useStoreActions("test-store", mockApi, mockStore, mockLoading, mockInitialized);

    expectTypeOf(actions.createOne).parameter(0).toEqualTypeOf<CreateInput>();
    expectTypeOf(actions.updateOne).parameter(0).toEqualTypeOf<UpdateInput & { id: string | number }>();
    expectTypeOf(actions.createOne).returns.resolves.toEqualTypeOf<Item | null>();
  });

  test("deleteMany calls deleteOne for each ID and refreshes once", async () => {
    const actions = useStoreActions("test-store", mockApi, mockStore, mockLoading, mockInitialized);

    mockApi.deleteOne = vi.fn().mockResolvedValue({ response: { data: {} } });
    mockApi.getAll = vi.fn().mockResolvedValue({ data: { items: [] } });

    const ids = ["1", "2", "3"];
    await actions.deleteMany(ids);

    expect(mockApi.deleteOne).toHaveBeenCalledTimes(3);
    expect(mockApi.deleteOne).toHaveBeenCalledWith("1");
    expect(mockApi.deleteOne).toHaveBeenCalledWith("2");
    expect(mockApi.deleteOne).toHaveBeenCalledWith("3");

    expect(mockApi.getAll).toHaveBeenCalledTimes(1);
  });

  test("deleteMany handles empty array", async () => {
    const actions = useStoreActions("test-store", mockApi, mockStore, mockLoading, mockInitialized);

    mockApi.deleteOne = vi.fn();
    mockApi.getAll = vi.fn().mockResolvedValue({ data: { items: [] } });

    await actions.deleteMany([]);

    expect(mockApi.deleteOne).not.toHaveBeenCalled();
    expect(mockApi.getAll).toHaveBeenCalledTimes(1);
  });

  test("deleteMany sets loading state", async () => {
    const actions = useStoreActions("test-store", mockApi, mockStore, mockLoading, mockInitialized);

    mockApi.deleteOne = vi.fn().mockResolvedValue({});
    mockApi.getAll = vi.fn().mockResolvedValue({ data: { items: [] } });

    const promise = actions.deleteMany(["1"]);
    expect(mockLoading.value).toBe(true);

    await promise;
    expect(mockLoading.value).toBe(false);
  });

  test("refresh sets initialized to true even when store returns empty results", async () => {
    const localInitialized = ref(false);
    const actions = useStoreActions("test-store", mockApi, mockStore, mockLoading, localInitialized);

    mockApi.getAll = vi.fn().mockResolvedValue({ data: { items: [] } });

    expect(localInitialized.value).toBe(false);
    await actions.refresh();
    expect(localInitialized.value).toBe(true);
  });

  test("refresh sets initialized to true when store returns items", async () => {
    const localInitialized = ref(false);
    const actions = useStoreActions("test-store", mockApi, mockStore, mockLoading, localInitialized);

    mockApi.getAll = vi.fn().mockResolvedValue({ data: { items: [{ id: "1", name: "item" }] } });

    await actions.refresh();
    expect(localInitialized.value).toBe(true);
  });
});
