# Administrative user form

Source: [user-form.ts](../frontend/app/composables/use-users/user-form.ts), rendered through [AutoForm](../frontend/app/components/global/AutoForm.vue). Preserve the generic validation/control contract in [shared data management](shared-data-management.md).

## Functions to preserve

- User Details fields: required User Name, Full Name, Email, and Password. The schema applies only required to Email here, not the email-format validator used on invitation forms.
- Password is masked, requires at least eight characters when creating, and is disabled with its rules removed in update mode.
- Authentication Method offers Mealie, LDAP, and OIDC plus explanatory hint. It is disabled in create mode, enabled during update.
- Permissions: Administrator, Invite Others, Manage Group Settings, Organize Group Data, Manage Household, and Advanced Features. Preserve all six labels, individual help tooltips, and boolean field handling.
- Administrator implies all five other permissions. Turning it on sets them true and disables their controls; turning it off resets them false and re-enables controls. These are draft effects until submission.
- Existing non-Mealie users cannot change Administrator in the edit page; preserve this boundary alongside server authorization.
- Admin create initializes Mealie auth, blank strings, and false permissions. `canManageHousehold` is not explicitly in its initial object, though the form renders it; do not confuse this source omission with a deliberate missing control.

## Shadcn Vue replacement checklist

- [ ] Use Input, masked password Input, Select, Checkbox, Tooltip, semantic sections, and validation messages.
- [ ] Preserve create/update disabling, all permission dependencies, hints, required fields, and password length.
- [ ] Verify boolean false handling, form validation, and external-auth administrator restrictions.
