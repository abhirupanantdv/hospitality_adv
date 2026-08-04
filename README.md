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

## Desk Dashboard

The default Desk route is `hospitality-adv-dashboard`. It provides a single-page
command center for accounting, buying, selling, stock, HRMS, and Hospitality ADV
DocTypes. Cards are shown only when the logged-in user has access to the related
DocType; ERPNext and HRMS content is therefore available when those apps are installed.

After installing or updating the app, build its Desk assets before signing in:

```bash
bench build --app hospitality_adv
bench --site your-site.local clear-cache
```

For an existing site, `bench --site your-site.local migrate` also applies the
dashboard as the global Desk home page.

## Demo Data

Create idempotent Hospitality ADV demo data, plus safe ERPNext and HRMS draft
records when those apps are installed:

```bash
bench --site your-site.local execute hospitality_adv.demo.seed_demo_data
```

The demo command does not submit invoices, purchase orders, stock entries, or
payroll documents. Submit those documents through ERPNext only after the company,
accounts, warehouses, and taxes are configured.
