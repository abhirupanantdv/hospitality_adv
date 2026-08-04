import frappe
from frappe import _
from frappe.utils import now_datetime


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
            "open_hospitality_tasks": _count(
                "Hospitality ADV Operation Task", {"status": ["not in", ["Done", "Cancelled"]]}
            ),
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
