# Hospitality ADV

Backend-only Frappe/ERPNext app for hotel operations. This workspace intentionally
contains no React/Vite frontend or other UI application.


## Install in a bench

```bash
bench get-app /path/to/hospitality_adv
bench --site your-site.local install-app hospitality_adv
bench --site your-site.local migrate
```

Frappe synchronizes the DocTypes from the versioned JSON files under
`hospitality_adv/hospitality_adv/doctype`. Installing this app
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

Whitelisted methods live in `hospitality_adv.api` and expose dashboard, reservation calendar, room board, task, lift permission and module summary endpoints for the React app.

Frappe Desk provides the administrative UI for the installed DocTypes. The optional
API methods are retained for integrations but no separate frontend is included.

