import { BaseCRUDAPI } from "../base/base-clients";
import type { PlanEntryCreate, RandomPlanEntryCreate, MealPlanICalTokenOut, PlanEntryOut, PlanEntryUpdate, SavedMealPlanCreate, SavedMealPlanImport, SavedMealPlanOut, SavedMealPlanSummary } from "~/lib/api/types/meal-plan";

const prefix = "/api";

const routes = {
  mealplan: `${prefix}/households/mealplans`,
  saved: `${prefix}/households/mealplans/saved`,
  random: `${prefix}/households/mealplans/random`,
  ical: `${prefix}/households/mealplans/ical`,
  mealplanId: (id: string | number) => `${prefix}/households/mealplans/${id}`,
};

export class MealPlanAPI extends BaseCRUDAPI<PlanEntryCreate, PlanEntryOut, PlanEntryUpdate> {
  override baseRoute = routes.mealplan;
  override itemRoute = routes.mealplanId;

  getSavedPlans() {
    return this.requests.get<SavedMealPlanSummary[]>(routes.saved);
  }

  getSavedPlan(id: string) {
    return this.requests.get<SavedMealPlanOut>(`${routes.saved}/${id}`);
  }

  createSavedPlan(payload: SavedMealPlanCreate) {
    return this.requests.post<SavedMealPlanOut>(routes.saved, payload);
  }

  updateSavedPlan(id: string, payload: SavedMealPlanCreate) {
    return this.requests.put<SavedMealPlanOut, SavedMealPlanCreate>(`${routes.saved}/${id}`, payload);
  }

  deleteSavedPlan(id: string) {
    return this.requests.delete<SavedMealPlanSummary>(`${routes.saved}/${id}`);
  }

  importSavedPlan(id: string, payload: SavedMealPlanImport) {
    return this.requests.post<PlanEntryOut[]>(`${routes.saved}/${id}/import`, payload);
  }

  async setRandom(payload: RandomPlanEntryCreate) {
    return await this.requests.post<PlanEntryOut>(routes.random, payload);
  }

  async getICalToken() {
    return await this.requests.get<MealPlanICalTokenOut>(routes.ical);
  }

  async createICalToken() {
    return await this.requests.post<MealPlanICalTokenOut>(routes.ical, {});
  }

  async deleteICalToken() {
    return await this.requests.delete<MealPlanICalTokenOut>(routes.ical);
  }
}
