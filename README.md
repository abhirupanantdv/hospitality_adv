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

New Hospitality ADV documents use the yearly ID format
`HADV-<TYPE>-YYYY-00001`. Existing document IDs are preserved when the app is
updated; only records created after migration use the standardized series.

## Desk Dashboard

`hospitality-adv-dashboard` provides a single-page command center for accounting,
buying, selling, stock, HRMS, and Hospitality ADV DocTypes. Cards are shown only
when the logged-in user has access to the related DocType; ERPNext and HRMS content
is therefore available when those apps are installed. The app does not change the
site's global Desk home page automatically.

`hospitality-adv-insights` is a second Desk page containing tab-aligned charts for
finance, selling, buying, stock, HRMS, hotel operations, and Hospitality ADV POS.
Both pages read the site's existing documents at request time. They do not insert
or depend on sample records.

Finance metrics use submitted invoices only. Paid counts require an outstanding
amount of zero; overdue items require an outstanding amount and a due date before
today. Aging charts group outstanding balances into 1-30, 31-60, and 61+ days.

After installing or updating the app, build its Desk assets before signing in:

```bash
bench build --app hospitality_adv
bench --site your-site.local clear-cache
```

Open the command center at `/app/hospitality-adv-dashboard` and Insights at
`/app/hospitality-adv-insights` after migration.

## Demo Data

Create idempotent Hospitality ADV demo data, plus safe ERPNext and HRMS draft
records when those apps are installed:

```bash
bench --site your-site.local execute hospitality_adv.demo.seed_demo_data
```

The demo command does not submit invoices, purchase orders, stock entries, or
payroll documents. Submit those documents through ERPNext only after the company,
accounts, warehouses, and taxes are configured.
