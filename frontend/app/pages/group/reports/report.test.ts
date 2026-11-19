import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, expect, test, vi } from "vitest";
import ReportPage from "./[id].vue";
import { makeReportEntry } from "~/tests/factories";
import { i18n } from "~/tests/setup";
import type { ReportOut } from "~/lib/api/types/reports";

const { getOne } = vi.hoisted(() => ({ getOne: vi.fn() }));

vi.mock("~/composables/api", () => ({
  useUserApi: () => ({ groupReports: { getOne } }),
}));

afterEach(() => vi.unstubAllGlobals());

test("only entries with an exception get a collapsed detail showing it", async () => {
  vi.stubGlobal("definePageMeta", vi.fn());
  vi.stubGlobal("useRoute", () => ({ params: { id: "report-1" } }));
  vi.stubGlobal("ResizeObserver", class {
    observe() {}
    unobserve() {}
    disconnect() {}
  });
  i18n.global.setDateTimeFormat("en-US", { short: { year: "numeric", month: "short", day: "numeric" } });
  const report: ReportOut = {
    id: "report-1",
    groupId: "group-1",
    name: "Migration report",
    category: "migration",
    timestamp: "2026-09-25T12:00:00Z",
    status: "success",
    entries: [
      makeReportEntry({ id: "failed", reportId: "report-1", message: "Failed recipe", success: false, exception: "Invalid recipe data" }),
      makeReportEntry({ id: "success", reportId: "report-1", message: "Imported recipe", success: true, exception: "" }),
      makeReportEntry({ id: "no-details", reportId: "report-1", message: "No details", success: false }),
    ],
  };
  getOne.mockResolvedValue({ data: report });
  const wrapper = mount(ReportPage, {
    global: {
      stubs: { NuxtLink: { template: "<a><slot /></a>" }, MdiIcon: true },
      mocks: {
        $globals: { icons: { checkboxMarkedCircle: "success", close: "error" } },
      },
    },
  });

  try {
    await flushPromises();
    expect(getOne).toHaveBeenCalledWith("report-1");
    const rows = wrapper.findAll("li");
    expect(rows).toHaveLength(3);
    expect(wrapper.text()).toContain("1 succeeded");
    expect(wrapper.text()).toContain("2 failed");

    const details = wrapper.findAll("details");
    expect(details).toHaveLength(1);
    expect(rows[0]!.find("details").exists()).toBe(true);
    expect((details[0]!.element as HTMLDetailsElement).open).toBe(false);
    expect(details[0]!.get("pre").text()).toBe("Invalid recipe data");
    expect(rows[1]!.find("details").exists()).toBe(false);
    expect(rows[2]!.find("details").exists()).toBe(false);
  }
  finally {
    wrapper.unmount();
  }
});
