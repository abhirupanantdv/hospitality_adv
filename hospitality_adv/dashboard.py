import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate, now_datetime, nowdate


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


def _records(doctype, fields, filters=None, order_by=None):
    if not _can_read(doctype):
        return []

    return frappe.get_list(
        doctype,
        fields=fields,
        filters=filters or {},
        order_by=order_by or "modified desc",
        limit_page_length=5000,
    )


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


def _live_charts():
    sales_labels, sales_values = _monthly_values(
        "Sales Invoice", "posting_date", "grand_total", {"docstatus": 1}
    )
    purchase_labels, purchase_values = _monthly_values(
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
    outgoing_labels, outgoing_values = _monthly_values(
        "Stock Entry", "posting_date", "total_outgoing_value", {"docstatus": 1}
    )
    receivable_amount = sum(
        flt(record.get("outstanding_amount"))
        for record in _records(
            "Sales Invoice", ["outstanding_amount"], {"docstatus": 1, "outstanding_amount": [">", 0]}
        )
    )
    payable_amount = sum(
        flt(record.get("outstanding_amount"))
        for record in _records(
            "Purchase Invoice", ["outstanding_amount"], {"docstatus": 1, "outstanding_amount": [">", 0]}
        )
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
                [{"values": [receivable_amount, payable_amount]}],
                "bar",
                ["#7653a4"],
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
    sales_invoice_filters = {"docstatus": 1, "outstanding_amount": [">", 0]}
    purchase_invoice_filters = {"docstatus": 1, "outstanding_amount": [">", 0]}

    return {
        "generated_at": now_datetime(),
        "available": available,
        "reports": {report: bool(frappe.db.exists("Report", report)) for report in REPORTS},
        "charts": _live_charts(),
        "metrics": {
            "customers": _count("Customer"),
            "draft_quotations": _count("Quotation", {"docstatus": 0}),
            "draft_sales_invoices": _count("Sales Invoice", {"docstatus": 0}),
            "draft_purchase_invoices": _count("Purchase Invoice", {"docstatus": 0}),
            "receivables": _count("Sales Invoice", sales_invoice_filters),
            "payables": _count("Purchase Invoice", purchase_invoice_filters),
            "open_purchase_orders": _count("Purchase Order", {"docstatus": 1}),
            "stock_items": _count("Item", {"disabled": 0}),
            "active_employees": _count("Employee", {"status": "Active"}),
            "open_leave_requests": _count("Leave Application", {"docstatus": 0}),
            "active_reservations": _count(
                "Hospitality ADV Reservation", {"status": ["in", ["Confirmed", "Checked In"]]}
            ),
            "open_hospitality_tasks": _count("Hospitality ADV Operation Task", {"status": ["not in", ["Done", "Cancelled"]]}),
        },
        "pending": {
            "quotations": _recent("Quotation", {"docstatus": 0}, "customer_name", "grand_total"),
            "sales_invoices": _recent("Sales Invoice", {"docstatus": 0}, "customer_name", "grand_total"),
            "purchase_invoices": _recent("Purchase Invoice", {"docstatus": 0}, "supplier_name", "grand_total"),
            "hospitality_tasks": _recent(
                "Hospitality ADV Operation Task",
                {"status": ["not in", ["Done", "Cancelled"]]},
                "subject",
            ),
        },
    }
