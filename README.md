# ADV Hospitality Backend

Backend-only Frappe/ERPNext app for hotel operations. This workspace intentionally
contains no React/Vite frontend or other UI application.

Extracted from `anantdv/adv-hospitality-suite-app` at commit
`1d0757b0978ef4d7f847407ad3330886ca9415c3`.

## Install in a bench

```bash
bench get-app /path/to/adv_hospitality_backend
bench --site your-site.local install-app adv_hospitality_backend
bench --site your-site.local migrate
```

Frappe synchronizes the DocTypes from the versioned JSON files under
`adv_hospitality_backend/adv_hospitality_backend/doctype`. Installing this app
does not create demo hotel, guest, room, OTA, POS, or access-control records.

## Main DocTypes

- `ADV Property`, `ADV Room Type`, `ADV Room`
- `ADV Guest`, `ADV Reservation`, `ADV Guest Stay`, `ADV Guest Message`
- `ADV Operation Task`, `ADV Housekeeping Inspection`, `ADV Maintenance Event`
- `ADV Hotspot Session`, `ADV Network Flow`
- `ADV Access Event`, `ADV Guest Credential`, `ADV Lift Permission`
- `ADV POS Outlet`, `ADV POS Order`
- `ADV Staff Roster`, `ADV OTA Channel`, `ADV Integration Event`

## API methods

Whitelisted methods live in `adv_hospitality_backend.api` and expose dashboard, reservation calendar, room board, task, lift permission and module summary endpoints for the React app.

Frappe Desk provides the administrative UI for the installed DocTypes. The optional
API methods are retained for integrations but no separate frontend is included.

