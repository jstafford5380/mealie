import type { BoundT } from "./types";
import type { BaseCRUDAPI, BaseCRUDAPIReadOnly } from "~/lib/api/base/base-clients";
import type { QueryValue } from "~/lib/api/base/route";

export type StoreApi<Create, Item, Update> = Pick<
  BaseCRUDAPI<Create, Item, Update>,
  "getAll" | "createOne" | "updateOne" | "deleteOne"
>;

/**
 * useReadOnlyActions is a factory function that returns a set of methods
 * that can be reused to manage the state of a data store without using
 * Vuex. This is primarily used for basic GET/GETALL operations that required
 * a lot of refreshing hooks to be called on operations
 */
export function useReadOnlyActions<T extends BoundT>(
  storeKey: string,
  api: Pick<BaseCRUDAPIReadOnly<T>, "getAll">,
  allRef: Ref<T[] | null> | null,
  loading: Ref<boolean>,
  initialized: Ref<boolean>,
  defaultQueryParams: Record<string, QueryValue> = {},
) {
  function getAll(page = 1, perPage = -1, params = {} as Record<string, QueryValue>) {
    params = { ...defaultQueryParams, ...params };
    params.orderBy ??= "name";
    params.orderDirection ??= "asc";

    const allItems = useAsyncData(storeKey, async () => {
      loading.value = true;
      try {
        const { data } = await api.getAll(page, perPage, params);

        if (data && allRef) {
          allRef.value = data.items;
        }

        if (data) {
          return data.items ?? [];
        }
        else {
          return [];
        }
      }
      finally {
        loading.value = false;
      }
    });

    return allItems;
  }

  async function refresh(page = 1, perPage = -1, params = {} as Record<string, QueryValue>) {
    params = { ...defaultQueryParams, ...params };
    params.orderBy ??= "name";
    params.orderDirection ??= "asc";

    loading.value = true;
    const { data } = await api.getAll(page, perPage, params);

    if (data && data.items && allRef) {
      allRef.value = data.items;
    }

    initialized.value = true;
    loading.value = false;
  }

  return {
    getAll,
    refresh,
  };
}

/**
 * useStoreActions is a factory function that returns a set of methods
 * that can be reused to manage the state of a data store without using
 * Vuex. This is primarily used for basic CRUD operations that required
 * a lot of refreshing hooks to be called on operations
 */
export function useStoreActions<T extends BoundT, Create, Update>(
  storeKey: string,
  api: StoreApi<Create, T, Update>,
  allRef: Ref<T[] | null> | null,
  loading: Ref<boolean>,
  initialized: Ref<boolean>,
  defaultQueryParams: Record<string, QueryValue> = {},
) {
  const { getAll, refresh } = useReadOnlyActions(storeKey, api, allRef, loading, initialized, defaultQueryParams);

  async function createOne(createData: Create) {
    loading.value = true;
    const { data } = await api.createOne(createData);
    if (data && allRef?.value) {
      allRef.value.push(data);
    }
    else {
      await refresh();
    }
    loading.value = false;
    return data;
  }

  async function updateOne(updateData: Update & { id: string | number }) {
    if (!updateData.id) {
      return null;
    }

    loading.value = true;
    const { data } = await api.updateOne(updateData.id, updateData);
    if (data && allRef?.value) {
      await refresh();
    }
    loading.value = false;
    return data;
  }

  async function deleteOne(id: string | number) {
    loading.value = true;
    const { response } = await api.deleteOne(id);
    if (response && allRef?.value) {
      await refresh();
    }
    loading.value = false;
    return response?.data || null;
  }

  async function deleteMany(ids: (string | number)[]) {
    loading.value = true;
    for (const id of ids) {
      await api.deleteOne(id);
    }
    if (allRef?.value) {
      await refresh();
    }
    loading.value = false;
  }

  return {
    getAll,
    refresh,
    createOne,
    updateOne,
    deleteOne,
    deleteMany,
  };
}
