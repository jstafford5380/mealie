# Component replacement plan

The [component inventory](component-inventory.md) contains one task row for each of the 169 existing Vue components.
The [page index](PAGES.md) contains the page consumers and their function contracts.
Use both inventories. A direct Vuetify-tag scan does not cover programmatic UI, layouts, or delegated controls.

## Replacement decisions

The mappings below are proposed compositions, not official one-for-one replacements.
The [Shadcn Vue component catalog](https://www.shadcn-vue.com/docs/components) supplies the available primitives.
Use the [Data Table guide](https://www.shadcn-vue.com/docs/components/data-table) for table composition and
the [Combobox guide](https://www.shadcn-vue.com/docs/components/combobox) for searchable selection.
Read the page contracts before implementation; visual similarity does not prove behavior parity.

| Current UI family | Proposed replacement | Required behavior |
| --- | --- | --- |
| App, AppBar, Main, NavigationDrawer, Footer, Toolbar | Semantic layout, Sidebar, Sheet, Button, Separator | Responsive drawers, fixed header, navigation context, print rules, branding. |
| Container, Row, Col, Spacer, Responsive, Sheet | CSS grid/flex, spacing tokens, semantic sections, AspectRatio where useful | Breakpoints, content order, long text, independent scroll regions. |
| Card, CardTitle, CardSubtitle, CardText, CardActions | Card composition and semantic headings | Titles, descriptions, action placement, disabled/loading state, link semantics. |
| Button, FAB, button toggles, item groups | Button, ButtonGroup, ToggleGroup | Icon-only labels, selected state, floating-save visibility, keyboard operation. |
| TextField, Textarea, NumberInput | Input, Textarea, NumberField, Label/Field | Validation, clear actions, suffixes, min/max/precision, password visibility, autocomplete. |
| Form and AutoForm | Shared form adapter over Shadcn Vue fields | Existing models, async validation, create/update restrictions, error focus, submit guards. |
| Checkbox, CheckboxButton, Switch, RadioGroup/Radio | Checkbox, Switch, RadioGroup | Partial selection, labels, checked values, auto-save semantics, keyboard behavior. |
| Select, Autocomplete, Combobox | Select or Combobox with explicit multi-select composition | Normalized search, custom filtering, object values, free text, chips, remote options. |
| Menu, List, nested ListGroup, ListItem and item sections | DropdownMenu, NavigationMenu, Collapsible, Item, semantic lists | Nested groups, route links, menu actions, selection, disabled states. |
| Dialog and BottomSheet | Dialog, Sheet or Drawer; AlertDialog for destructive review | Mobile modes, focus trap, Enter/Escape, cancel/close events, async close behavior. |
| Alert, Banner, EmptyState | Alert, Empty, semantic status regions | Contextual warnings, recovery links, error detail, empty-state actions. |
| Snackbar | Shared Sonner/toast adapter | Action callbacks, timeout, independent progress notice, live announcements. |
| Divider, Chip, Badge, Avatar, Icon | Separator, Badge, Avatar, selected icon system | Chip actions, counts, tooltips, truncation, fallback images, accessible names. |
| Tooltip, Hover | Tooltip, HoverCard or CSS hover state | Keyboard/focus access, touch alternatives, tooltip content. |
| DataTable | Table/Data Table plus selection, sorting, filtering, and pagination state | Every custom cell, bulk action, export scope, server/client pagination choice. |
| DatePicker | Calendar, RangeCalendar, DatePicker composition | Locale, week start, date ranges, invalid dates, day/week meal-planner modes. |
| ColorPicker | Input, Popover, Slider/swatches, browser color support | Color text, random color, alpha, hue, preview, eyedropper where supported. |
| Rating | Accessible rating control composed with buttons or radio semantics | Clear rating, keyboard selection, half-step behavior where used, per-user value. |
| ExpansionPanels and panel sections | Accordion or Collapsible | Single/multiple expansion, selected state, conditional content, scroll position. |
| Stepper and stepper sections/actions | Stepper composition or explicit wizard state with accessible navigation | Validation gates, history, summary, submit progress, completed/current states. |
| Timeline and TimelineItem | Semantic event list with Card/Separator composition | Event order, filters, images, notes, add/edit/delete, localized dates. |
| Treeview | Accessible hierarchical selector with supported primitives or a dedicated tree implementation | Nested selection, expansion, keyboard navigation, filtering. |
| ProgressCircular, ProgressLinear, SkeletonLoader | Spinner, Progress, Skeleton | Determinate values, indeterminate state, labels, loading boundaries. |
| FileInput, Img | Native file input with Button/Input composition; native image/AspectRatio/Skeleton | Acceptance, multiple files, clearing, drag/drop, upload errors, lazy images. |
| VirtualScroll, Lazy | ScrollArea plus a virtualization/intersection adapter where required | Large-list performance, item identity, lazy assets, scroll restoration. |
| Expand/Fade/ScrollX/SlideX transitions | Vue Transition and CSS motion tokens | Presence, focus, reduced motion, mobile behavior. |

Specialized domains remain composed application components after replacement.
Shadcn Vue primitives do not replace recipe parsing, drag and drop, image crop, JSON editing, Markdown, wake locks, timers, or print rendering.
Keep their behavior and replace the surrounding Vuetify controls.

## Work order

1. Establish theme tokens, dark mode, RTL support, typography, focus states, and the icon adapter.
2. Replace BaseButton, BaseDivider, title/card sections, loaders, and status feedback.
3. Replace BaseDialog/BaseDialogContent and all menu/button-group adapters.
4. Replace AutoForm, field wrappers, searchable selectors, file controls, and date/color controls.
5. Replace CrudTable, GroupDataPage, report tables, recipe tables, and pagination.
6. Replace default/admin/basic/blank layouts and shared navigation/search/announcements.
7. Replace each domain component and page against its function contract and state captures.
8. Verify cross-page flows and all permission variants.
9. Remove the Vuetify module and dependencies only after the source and runtime audit passes.

## Non-component cleanup

- [x] Replace `useDisplay` and all `$vuetify.display` consumers with a consistent breakpoint adapter.
- [x] Replace injected theme APIs, `$vuetify.theme`, Vuetify hooks, and the dark-mode plugin integration.
- [x] Preserve server-provided theme values and branding overrides in the new token system.
- [x] Replace Vuetify directives and CSS selectors, including deep selectors and responsive utility classes.
- [x] Replace Vuetify-specific form types and component imports in tests.
- [ ] Preserve Nuxt auto-import names or update every consumer deliberately.
- [ ] Preserve API clients, generated schemas, composable state, data scoping, and route middleware.
- [ ] Verify app plugins, PWA share redirects, auth refresh, cookies, and error toasts after layout changes.
- [ ] Verify print styles and specialized no-print controls.
- [x] Keep every locale intact. Add new strings only to `en-US`.

## Completion gates

- [ ] All page and component task rows have reviewed evidence.
- [ ] Every page's function checklist passes, including child components and hidden controls.
- [ ] Screenshots cover the full page and the distinct interaction states needed to explain it.
- [ ] Public and permission-limited users retain the correct functions and restrictions.
- [ ] Desktop, narrow screens, touch input, keyboard access, dark mode, and RTL all pass review.
- [x] No runtime or source dependency on Vuetify remains in the application UI.
- [ ] Repository frontend checks and relevant end-to-end workflows pass.

An empty grep result alone does not prove replacement. A passing screenshot comparison alone does not prove function parity.
