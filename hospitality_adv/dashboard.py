import frappe
from frappe import _
from frappe.utils import add_months, date_diff, flt, getdate, now_datetime, nowdate


HOSPITALITY_DOCTYPES = [
    "Hospitality ADV Property",
    "Hospitality ADV Room Type",
    "Hospitality ADV Room",
    "Hospitality ADV Guest",
    "Hospitality ADV Reservation",
    "Hospitality ADV Guest Stay",
    "Hospitality ADV Guest Message",
    "Hospitality ADV Operation Task",
    "Hospitality ADV Housekeeping Inspection",
    "Hospitality ADV Maintenance Event",
    "Hospitality ADV Hotspot Session",
    "Hospitality ADV Network Flow",
    "Hospitality ADV Access Event",
    "Hospitality ADV Guest Credential",
    "Hospitality ADV Lift Permission",
    "Hospitality ADV POS Outlet",
    "Hospitality ADV POS Order",
    "Hospitality ADV Staff Roster",
    "Hospitality ADV OTA Channel",
    "Hospitality ADV Integration Event",
]


CORE_DOCTYPES = [
    "Customer",
    "Supplier",
    "Item",
    "Item Group",
    "Quotation",
    "Sales Order",
    "Sales Invoice",
    "Delivery Note",
    "Material Request",
    "Request for Quotation",
    "Supplier Quotation",
    "Purchase Order",
    "Purchase Invoice",
    "Payment Entry",
    "Journal Entry",
    "Stock Entry",
    "Warehouse",
    "Employee",
    "Attendance",
    "Leave Application",
    "Salary Slip",
    "Payroll Entry",
]


REPORTS = [
    "Accounts Receivable",
    "Accounts Payable",
    "Balance Sheet",
    "Profit and Loss Statement",
    "General Ledger",
    "Sales Analytics",
    "Stock Balance",
    "Stock Ledger",
]


def _can_read(doctype):
    return bool(frappe.db.exists("DocType", doctype) and frappe.has_permission(doctype, "read"))


def _count(doctype, filters=None):
    if not _can_read(doctype):
        return None
    return frappe.db.count(doctype, filters or {})


def _recent(doctype, filters, title_field, amount_field=None):
    if not _can_read(doctype):
        return []

    fields = ["name", "status", "modified", title_field]
    if amount_field:
        fields.append(amount_field)

    records = frappe.get_list(
        doctype,
        filters=filters,
        fields=fields,
        order_by="modified desc",
        limit_page_length=5,
    )
    return [
        {
            "doctype": doctype,
            "name": record.name,
            "title": record.get(title_field) or record.name,
            "status": record.get("status") or "",
            "amount": record.get(amount_field) if amount_field else None,
        }
        for record in records
    ]


def _has_field(doctype, fieldname):
    return bool(_can_read(doctype) and frappe.get_meta(doctype).has_field(fieldname))


def _month_window(months=6):
    current_month = getdate(nowdate()).replace(day=1)
    month_starts = [add_months(current_month, offset) for offset in range(-(months - 1), 1)]
    return {
        "labels": [month.strftime("%b") for month in month_starts],
        "keys": [month.strftime("%Y-%m") for month in month_starts],
        "start": month_starts[0],
    }


def _records(doctype, fields, filters=None, order_by=None, limit_page_length=5000):
    if not _can_read(doctype):
        return []

    return frappe.get_list(
        doctype,
        fields=fields,
        filters=filters or {},
        order_by=order_by or "modified desc",
        limit_page_length=limit_page_length,
    )


def _invoice_health(doctype):
    health = {
        "paid_count": 0,
        "paid_amount": 0,
        "outstanding_count": 0,
        "outstanding_amount": 0,
        "overdue_count": 0,
        "overdue_amount": 0,
        "age_1_30_count": 0,
        "age_1_30_amount": 0,
        "age_31_60_count": 0,
        "age_31_60_amount": 0,
        "age_61_plus_count": 0,
        "age_61_plus_amount": 0,
    }
    required_fields = ["grand_total", "outstanding_amount", "due_date"]
    if not all(_has_field(doctype, fieldname) for fieldname in required_fields):
        return health

    today = getdate(nowdate())
    records = _records(doctype, required_fields, {"docstatus": 1})
    for record in records:
        outstanding_amount = flt(record.get("outstanding_amount"))
        grand_total = flt(record.get("grand_total"))
        if outstanding_amount <= 0:
            health["paid_count"] += 1
            health["paid_amount"] += grand_total
            continue

        health["outstanding_count"] += 1
        health["outstanding_amount"] += outstanding_amount
        due_date = record.get("due_date")
        if not due_date or getdate(due_date) >= today:
            continue

        days_overdue = date_diff(today, getdate(due_date))
        health["overdue_count"] += 1
        health["overdue_amount"] += outstanding_amount
        if days_overdue <= 30:
            bucket = "age_1_30"
        elif days_overdue <= 60:
            bucket = "age_31_60"
        else:
            bucket = "age_61_plus"
        health[f"{bucket}_count"] += 1
        health[f"{bucket}_amount"] += outstanding_amount

    return health


def _invoice_due_detail(due_date, days_overdue):
    if days_overdue:
        return _("Overdue by {0} day(s)", [days_overdue])
    if due_date:
        return _("Due {0}", [frappe.format(due_date, {"fieldtype": "Date"})])
    return _("No due date")


def _outstanding_invoices(doctype, title_field, limit=5):
    required_fields = [title_field, "grand_total", "outstanding_amount", "due_date"]
    if not all(_has_field(doctype, fieldname) for fieldname in required_fields):
        return []

    today = getdate(nowdate())
    records = _records(
        doctype,
        ["name", title_field, "outstanding_amount", "due_date"],
        {"docstatus": 1, "outstanding_amount": [">", 0]},
        "due_date asc",
        limit_page_length=20,
    )
    results = []
    for record in records:
        due_date = record.get("due_date")
        days_overdue = date_diff(today, getdate(due_date)) if due_date and getdate(due_date) < today else 0
        results.append(
            {
                "doctype": doctype,
                "name": record.name,
                "title": record.get(title_field) or record.name,
                "amount": flt(record.get("outstanding_amount")),
                "status": _("Overdue") if days_overdue else _("Outstanding"),
                "detail": _invoice_due_detail(due_date, days_overdue),
                "days_overdue": days_overdue,
            }
        )

    return sorted(results, key=lambda record: (-record["days_overdue"], record["name"]))[:limit]


def _task_due_summary():
    summary = {
        "open_count": 0,
        "overdue_count": 0,
        "due_today_count": 0,
        "due_next_7_count": 0,
        "without_due_date_count": 0,
    }
    if not _has_field("Hospitality ADV Operation Task", "due_datetime"):
        return summary

    today = getdate(nowdate())
    records = _records(
        "Hospitality ADV Operation Task",
        ["due_datetime"],
        {"status": ["not in", ["Done", "Cancelled"]]},
    )
    for record in records:
        summary["open_count"] += 1
        due_datetime = record.get("due_datetime")
        if not due_datetime:
            summary["without_due_date_count"] += 1
            continue

        due_date = getdate(due_datetime)
        if due_date < today:
            summary["overdue_count"] += 1
        elif due_date == today:
            summary["due_today_count"] += 1
        elif date_diff(due_date, today) <= 7:
            summary["due_next_7_count"] += 1

    return summary


def _task_due_detail(due_date, days_overdue, today):
    if days_overdue:
        return _("Overdue by {0} day(s)", [days_overdue])
    if due_date == today:
        return _("Due today")
    if not due_date:
        return _("No due date")
    return _("Due later")


def _pending_tasks(limit=5):
    required_fields = ["subject", "due_datetime"]
    if not all(_has_field("Hospitality ADV Operation Task", fieldname) for fieldname in required_fields):
        return []

    today = getdate(nowdate())
    records = _records(
        "Hospitality ADV Operation Task",
        ["name", "subject", "status", "due_datetime"],
        {"status": ["not in", ["Done", "Cancelled"]]},
        "due_datetime asc",
        limit_page_length=20,
    )
    results = []
    for record in records:
        due_datetime = record.get("due_datetime")
        due_date = getdate(due_datetime) if due_datetime else None
        days_overdue = date_diff(today, due_date) if due_date and due_date < today else 0
        results.append(
            {
                "doctype": "Hospitality ADV Operation Task",
                "name": record.name,
                "title": record.get("subject") or record.name,
                "status": _("Overdue") if days_overdue else record.get("status") or _("Open"),
                "detail": _task_due_detail(due_date, days_overdue, today),
                "amount": None,
                "days_overdue": days_overdue,
            }
        )

    return sorted(results, key=lambda record: (-record["days_overdue"], record["name"]))[:limit]


def _monthly_values(doctype, date_field, value_field=None, filters=None, months=6):
    window = _month_window(months)
    if not _has_field(doctype, date_field) or (value_field and not _has_field(doctype, value_field)):
        return window["labels"], [0] * months

    query_filters = dict(filters or {})
    query_filters[date_field] = [">=", window["start"]]
    fields = [date_field] + ([value_field] if value_field else [])
    values = {key: 0 for key in window["keys"]}

    for record in _records(doctype, fields, query_filters, f"{date_field} asc"):
        date_value = record.get(date_field)
        if not date_value:
            continue
        key = getdate(date_value).strftime("%Y-%m")
        if key in values:
            values[key] += flt(record.get(value_field)) if value_field else 1

    return window["labels"], [values[key] for key in window["keys"]]


def _status_values(doctype, status_field="status", filters=None, limit=6):
    if not _has_field(doctype, status_field):
        return [], []

    totals = {}
    for record in _records(doctype, [status_field], filters):
        status = record.get(status_field) or _("Not Set")
        totals[status] = totals.get(status, 0) + 1

    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [item[0] for item in ordered], [item[1] for item in ordered]


def _chart(title, labels, datasets, chart_type="bar", colors=None, empty_message=None, value_format="Int"):
    return {
        "title": title,
        "type": chart_type,
        "data": {"labels": labels, "datasets": datasets},
        "colors": colors or ["#257d7c", "#7653a4"],
        "empty_message": empty_message or _("No accessible records in this period."),
        "value_format": value_format,
    }


def _single_series_chart(
    title, doctype, date_field, dataset_name, value_field=None, filters=None, colors=None, value_format="Int"
):
    labels, values = _monthly_values(doctype, date_field, value_field, filters)
    return _chart(
        title,
        labels,
        [{"name": dataset_name, "values": values}],
        "line",
        colors or ["#257d7c"],
        value_format=value_format,
    )


def _status_chart(title, doctype, status_field="status", filters=None, colors=None):
    labels, values = _status_values(doctype, status_field, filters)
    return _chart(
        title,
        labels,
        [{"values": values}],
        "percentage",
        colors or ["#257d7c", "#7653a4", "#bc7a28", "#d24b61", "#6f829d", "#5e9bbf"],
    )


def _live_charts(invoice_health, task_summary):
    sales_labels, sales_values = _monthly_values(
        "Sales Invoice", "posting_date", "grand_total", {"docstatus": 1}
    )
    _purchase_labels, purchase_values = _monthly_values(
        "Purchase Invoice", "posting_date", "grand_total", {"docstatus": 1}
    )
    quote_labels, quote_values = _monthly_values(
        "Quotation", "transaction_date", "grand_total", {"docstatus": ["<", 2]}
    )
    buying_labels, purchase_order_values = _monthly_values(
        "Purchase Order", "transaction_date", "grand_total", {"docstatus": 1}
    )
    stock_labels, incoming_values = _monthly_values(
        "Stock Entry", "posting_date", "total_incoming_value", {"docstatus": 1}
    )
    _outgoing_labels, outgoing_values = _monthly_values(
        "Stock Entry", "posting_date", "total_outgoing_value", {"docstatus": 1}
    )
    return {
        "operations": [
            _single_series_chart(
                _("Reservations by Arrival Month"),
                "Hospitality ADV Reservation",
                "arrival_date",
                _("Reservations"),
                filters={"status": ["not in", ["Cancelled", "No Show"]]},
                colors=["#257d7c"],
            ),
            _status_chart(
                _("Operations Task Status"),
                "Hospitality ADV Operation Task",
                colors=["#257d7c", "#7653a4", "#bc7a28", "#d24b61", "#6f829d", "#5e9bbf"],
            ),
            _chart(
                _("Open Task Due Dates"),
                [_("Overdue"), _("Due Today"), _("Next 7 Days"), _("No Due Date")],
                [
                    {
                        "values": [
                            task_summary["overdue_count"],
                            task_summary["due_today_count"],
                            task_summary["due_next_7_count"],
                            task_summary["without_due_date_count"],
                        ]
                    }
                ],
                "bar",
                ["#d24b61"],
            ),
        ],
        "finance": [
            _chart(
                _("Submitted Sales and Purchase Invoices"),
                sales_labels,
                [
                    {"name": _("Sales Invoices"), "values": sales_values},
                    {"name": _("Purchase Invoices"), "values": purchase_values},
                ],
                "line",
                ["#257d7c", "#bc7a28"],
                value_format="Currency",
            ),
            _chart(
                _("Outstanding Exposure"),
                [_("Receivables"), _("Payables")],
                [
                    {
                        "values": [
                            invoice_health["sales"]["outstanding_amount"],
                            invoice_health["purchase"]["outstanding_amount"],
                        ]
                    }
                ],
                "bar",
                ["#7653a4"],
                value_format="Currency",
            ),
            _chart(
                _("Overdue Invoice Aging"),
                [_("1-30 Days"), _("31-60 Days"), _("61+ Days")],
                [
                    {
                        "name": _("Sales Invoices"),
                        "values": [
                            invoice_health["sales"]["age_1_30_amount"],
                            invoice_health["sales"]["age_31_60_amount"],
                            invoice_health["sales"]["age_61_plus_amount"],
                        ],
                    },
                    {
                        "name": _("Purchase Invoices"),
                        "values": [
                            invoice_health["purchase"]["age_1_30_amount"],
                            invoice_health["purchase"]["age_31_60_amount"],
                            invoice_health["purchase"]["age_61_plus_amount"],
                        ],
                    },
                ],
                "bar",
                ["#d24b61", "#bc7a28"],
                value_format="Currency",
            ),
        ],
        "selling": [
            _chart(
                _("Quotation and Sales Invoice Value"),
                quote_labels,
                [
                    {"name": _("Quotations"), "values": quote_values},
                    {"name": _("Sales Invoices"), "values": sales_values},
                ],
                "line",
                ["#257d7c", "#7653a4"],
                value_format="Currency",
            ),
            _status_chart(
                _("Quotation Status"), "Quotation", colors=["#257d7c", "#7653a4", "#bc7a28", "#d24b61"]
            ),
        ],
        "buying": [
            _chart(
                _("Purchase Order and Invoice Value"),
                buying_labels,
                [
                    {"name": _("Purchase Orders"), "values": purchase_order_values},
                    {"name": _("Purchase Invoices"), "values": purchase_values},
                ],
                "line",
                ["#bc7a28", "#257d7c"],
                value_format="Currency",
            ),
            _status_chart(
                _("Purchase Invoice Status"),
                "Purchase Invoice",
                colors=["#bc7a28", "#257d7c", "#7653a4", "#d24b61"],
            ),
        ],
        "stock": [
            _chart(
                _("Stock Movement Value"),
                stock_labels,
                [
                    {"name": _("Incoming Value"), "values": incoming_values},
                    {"name": _("Outgoing Value"), "values": outgoing_values},
                ],
                "bar",
                ["#257d7c", "#d24b61"],
                value_format="Currency",
            ),
            _status_chart(
                _("Stock Entry Purpose"),
                "Stock Entry",
                "stock_entry_type",
                {"docstatus": 1},
                ["#257d7c", "#7653a4", "#bc7a28", "#5e9bbf", "#d24b61"],
            ),
        ],
        "hrms": [
            _status_chart(
                _("Attendance Status"),
                "Attendance",
                colors=["#257d7c", "#d24b61", "#bc7a28", "#7653a4"],
            ),
            _status_chart(
                _("Leave Application Status"),
                "Leave Application",
                colors=["#7653a4", "#257d7c", "#bc7a28", "#d24b61"],
            ),
        ],
        "hospitality": [
            _single_series_chart(
                _("Hospitality POS Revenue"),
                "Hospitality ADV POS Order",
                "posting_datetime",
                _("Revenue"),
                "grand_total",
                {"status": ["not in", ["Draft", "Cancelled"]]},
                ["#bc7a28"],
                "Currency",
            ),
            _status_chart(
                _("Reservation Status"),
                "Hospitality ADV Reservation",
                colors=["#257d7c", "#7653a4", "#bc7a28", "#d24b61", "#6f829d", "#5e9bbf"],
            ),
        ],
    }


@frappe.whitelist()
def get_dashboard_data():
    if frappe.session.user == "Guest":
        frappe.throw(_("Login is required."), frappe.PermissionError)

    available = {doctype: _can_read(doctype) for doctype in CORE_DOCTYPES + HOSPITALITY_DOCTYPES}
    invoice_health = {
        "sales": _invoice_health("Sales Invoice"),
        "purchase": _invoice_health("Purchase Invoice"),
    }
    task_summary = _task_due_summary()

    return {
        "generated_at": now_datetime(),
        "available": available,
        "reports": {report: bool(frappe.db.exists("Report", report)) for report in REPORTS},
        "charts": _live_charts(invoice_health, task_summary),
        "financials": invoice_health,
        "task_summary": task_summary,
        "metrics": {
            "customers": _count("Customer"),
            "draft_quotations": _count("Quotation", {"docstatus": 0}),
            "draft_sales_invoices": _count("Sales Invoice", {"docstatus": 0}),
            "draft_purchase_invoices": _count("Purchase Invoice", {"docstatus": 0}),
            "receivables": invoice_health["sales"]["outstanding_count"],
            "receivable_amount": invoice_health["sales"]["outstanding_amount"],
            "paid_sales_invoices": invoice_health["sales"]["paid_count"],
            "paid_sales_amount": invoice_health["sales"]["paid_amount"],
            "overdue_sales_invoices": invoice_health["sales"]["overdue_count"],
            "overdue_sales_amount": invoice_health["sales"]["overdue_amount"],
            "sales_overdue_1_30": invoice_health["sales"]["age_1_30_count"],
            "sales_overdue_31_60": invoice_health["sales"]["age_31_60_count"],
            "sales_overdue_61_plus": invoice_health["sales"]["age_61_plus_count"],
            "payables": invoice_health["purchase"]["outstanding_count"],
            "payable_amount": invoice_health["purchase"]["outstanding_amount"],
            "paid_purchase_invoices": invoice_health["purchase"]["paid_count"],
            "overdue_purchase_invoices": invoice_health["purchase"]["overdue_count"],
            "overdue_purchase_amount": invoice_health["purchase"]["overdue_amount"],
            "open_purchase_orders": _count("Purchase Order", {"docstatus": 1}),
            "stock_items": _count("Item", {"disabled": 0}),
            "active_employees": _count("Employee", {"status": "Active"}),
            "open_leave_requests": _count("Leave Application", {"docstatus": 0}),
            "active_reservations": _count(
                "Hospitality ADV Reservation", {"status": ["in", ["Confirmed", "Checked In"]]}
            ),
            "open_hospitality_tasks": task_summary["open_count"],
            "overdue_hospitality_tasks": task_summary["overdue_count"],
            "hospitality_tasks_due_today": task_summary["due_today_count"],
        },
        "pending": {
            "quotations": _recent("Quotation", {"docstatus": 0}, "customer_name", "grand_total"),
            "sales_invoices": _outstanding_invoices("Sales Invoice", "customer_name"),
            "purchase_invoices": _outstanding_invoices("Purchase Invoice", "supplier_name"),
            "hospitality_tasks": _pending_tasks(),
        },
    }
