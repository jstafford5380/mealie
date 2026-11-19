# UI foundation: Tailwind, Shadcn Vue and Vuetify side by side

The new UI is built with Tailwind CSS v4 and Shadcn Vue (Reka UI) while Vuetify keeps rendering every page that has not been replaced yet. This document records how the two coexist and what changed on purpose.

Visual direction: [design canvas](https://claude.ai/artifact/XWeEjRbrLRHd3gkb3Cx7LU) (recipes, recipe page, meal plan, Cook mode, phone recipes and shopping list).

## Files

| File | Purpose |
| --- | --- |
| `frontend/app/assets/tailwind.css` | Design tokens (light/dark), Tailwind theme mapping, minimal base reset, coexistence exclusions. |
| `frontend/app/components/ui/` | Shadcn Vue primitives from the `new-york-v4` registry, adapted to the rules below. Not auto-registered; import from `~/components/ui/<name>`. |
| `frontend/app/lib/utils.ts` | `cn()` with tailwind-merge taught the project's radius names. |
| `frontend/components.json` | Shadcn Vue CLI configuration for adding more primitives. |
| `frontend/nuxt.config.ts` | Tailwind Vite plugin, cascade-layer order, `ui/**` excluded from component auto-import. |

## Coexistence rules

1. **Layer order.** `nuxt.config.ts` puts `@layer theme, base, vuetify-core, vuetify-components, vuetify-overrides, components, vuetify-utilities, utilities, vuetify-final;` first in `<head>`. Tailwind's base sits below Vuetify; Tailwind utilities beat Vuetify components and utilities.
2. **No Tailwind preflight.** Vuetify 4's reset is minimal, so preflight would restyle headings, lists and images on old pages. `tailwind.css` has a small base instead: border-box, zero-width solid borders using the border token, an `hr` rule and transparent form-control backgrounds.
3. **Clashing utility names are never generated.** Vuetify defines `w-25…w-100`, `h-25…h-100`, `rounded-sm/-md/-xl` (and side variants) with different values, and `main.css` defines `.hidden` as `visibility: hidden`. `@source not inline(...)` stops Tailwind emitting them. In new code use `w-full`, `h-full`, `w-1/2`, `rounded-item` (6px), `rounded-control` (10px), `rounded-card` (16px), `rounded-panel` (18px), `rounded-lg`, `rounded-full`, and `display-none` / `v-show` / `max-md:display-none`-style variants instead of plain `hidden`. Spacing names (`mb-4`, `px-2`, …) also exist in Vuetify but have identical values.
4. **Theme colour names.** Vuetify generates `bg-*`, `text-*` and `border-*` classes for its theme colours at runtime. Tokens that share a name must mean the same thing:
   - `primary` and `background` are shared and aligned with Vuetify's theme in `plugins/theme.ts`.
   - Shadcn's `secondary` and `accent` tokens are renamed `subtle` and `highlight` (`bg-subtle`, `hover:bg-highlight`). Button and Badge keep their `secondary` variant name.
   - `success`, `info`, `warning`, `error`, `surface` are not defined as Tailwind colours. Use `destructive` for errors and `brand` (marigold) for highlights.
5. **Dark mode.** `useDark` now applies `.dark` to `<html>` (the head script does it before first paint) in addition to switching the Vuetify theme.
6. **Server theme settings still apply.** `THEME_LIGHT_PRIMARY` / `THEME_DARK_PRIMARY` feed both Vuetify and the Tailwind `--primary` token; the readable foreground colour is computed in `plugins/theme.ts`.

7. **Stacking.** Mealie's app bar sits at z-index 2010. Reka dialogs and sheets use 2050/2051; Reka popovers, menus, selects and tooltips use 2400; Vuetify menus and tooltips are raised to 2400 (`plugins/theme.ts`) so they open above a Reka dialog. Toasts sit above everything.
8. **Vuetify controls inside Reka dialogs.** `lib/vuetify-coexistence.ts` keeps a Reka dialog open when the user clicks or focuses inside a Vuetify menu (rendered in `.v-overlay-container`), and lets Escape close an open Vuetify menu before the dialog. BaseDialog replaces Reka's focus trap with one that allows focus inside Vuetify menus.

9. **Form fields and legacy forms.** The new fields (`components/ui/field/*Field.vue`) validate with the same `rules` arrays as Vuetify and register with the nearest `<v-form>` through Vuetify's injection key (`composables/forms/use-field-validation.ts`), so `validate()`, `reset()` and form `v-model` validity include them. `provideFieldGroup()` stands in for a nested form (AutoForm) and registers with an outer form as one item.

Remove rules 1–4, 7 and 8 when Vuetify is removed: import Tailwind's preflight, delete the exclusions and the layer statement, and rename the radius utilities back if wanted.

## Adapting Shadcn Vue primitives

When adding a primitive from the registry (or with the CLI): replace `rounded-md` → `rounded-control`, `rounded-sm` → `rounded-item`, `rounded-xl` → `rounded-card`, bare `hidden` → `display-none`, and `secondary`/`accent` colour utilities → `subtle`/`highlight`; then run ESLint with `--fix`. Controls are 40px tall by default (`h-10`), 44px at `lg`, to keep touch targets usable.

## Deliberate behaviour and visual changes

| Change | Reason |
| --- | --- |
| Default primary colour is basil `#2E6A4F` (light) / `#5FAE87` (dark) instead of `#E58325`, in backend settings, API schema defaults, Nuxt runtime config and docs. | New palette; marigold stays as the brand highlight. Instances that set `THEME_*_PRIMARY` keep their colour. |
| Enter in a BaseDialog no longer submits when focus is in a textarea or rich-text field, or on a button or link. | Enter there inserts a new line or activates the control; previously it did that *and* submitted (a focused button ran twice). |
| BaseDialog has a close (×) button in the header. | Visible way to dismiss; it emits `cancel` exactly like Escape. |
| A page-level `<v-form>` now validates the fields of an AutoForm inside it (admin create/edit user, household, group, setup). | Vuetify ignored fields of a nested form, so those pages could submit with empty required AutoForm fields and rely on server errors. |
| AutoForm column widths apply from the `sm` breakpoint; on phones every field is full width. | Two fields side by side were too narrow on phones. |
| Password fields have a show/hide toggle. | Accessibility and fewer typos; new `user.show-password`/`user.hide-password` strings. |
| Vuetify background/surface use the new palette (`#F5F7F3`/`#FFFFFF` light, `#141816`/`#1C211E` dark). | Old and new pages share one background during the migration. |
