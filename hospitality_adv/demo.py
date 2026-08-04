from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, nowdate


DEMO_PROPERTY = "Hospitality ADV Demo Hotel"
DEMO_CUSTOMER = "Hospitality ADV Demo Customer"
DEMO_SUPPLIER = "Hospitality ADV Demo Supplier"
DEMO_ITEM = "HADV-DEMO-MINIBAR"


def _has_doctype(doctype):
    return bool(frappe.db.exists("DocType", doctype))


def _first_name(doctype, filters=None):
    if not _has_doctype(doctype):
        return None
    return frappe.db.get_value(doctype, filters or {}, "name", order_by="creation asc")


def _ensure(doctype, lookup, values, result):
    if not _has_doctype(doctype):
        result["skipped"].append(f"{doctype}: DocType is not installed")
        return None

    existing = frappe.db.get_value(doctype, lookup, "name")
    if existing:
        result["existing"].append(f"{doctype}: {existing}")
        return existing

    try:
        doc = frappe.get_doc({"doctype": doctype, **values})
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
        result["created"].append(f"{doctype}: {doc.name}")
        return doc.name
    except Exception as error:
        result["skipped"].append(f"{doctype}: {error}")
        return None


def _require_system_manager():
    if frappe.session.user != "Administrator" and "System Manager" not in frappe.get_roles():
        frappe.throw(_("Only a System Manager can create demo data."), frappe.PermissionError)


def _seed_hospitality(result):
    property_name = _ensure(
        "Hospitality ADV Property",
        {"property_name": DEMO_PROPERTY},
        {
            "property_name": DEMO_PROPERTY,
            "hotel_code": "HADV-DEMO",
            "timezone": "Asia/Kolkata",
            "address": "42 Harbour Road, Demo City",
            "phone": "+91 90000 00001",
            "email": "demo@hospitality-adv.local",
        },
        result,
    )
    room_types = {}
    for room_type, rate, capacity in [("Demo Deluxe", 6500, 2), ("Demo Suite", 9800, 3)]:
        room_types[room_type] = _ensure(
            "Hospitality ADV Room Type",
            {"room_type_name": room_type},
            {"room_type_name": room_type, "base_rate": rate, "capacity": capacity},
            result,
        )

    rooms = {}
    for room_number, room_type, status in [
        ("D101", "Demo Deluxe", "Occupied"),
        ("D102", "Demo Deluxe", "Vacant Dirty"),
        ("D201", "Demo Suite", "Reserved / VIP"),
    ]:
        rooms[room_number] = _ensure(
            "Hospitality ADV Room",
            {"room_number": room_number},
            {
                "room_number": room_number,
                "property": property_name,
                "room_type": room_types.get(room_type),
                "floor": room_number[1],
                "status": status,
                "housekeeping_status": "Pending" if status == "Vacant Dirty" else "Passed",
                "internet_available": 1,
                "door_lock_working": 1,
                "folio_balance": 2450 if status == "Occupied" else 0,
            },
            result,
        )

    guest_name = _ensure(
        "Hospitality ADV Guest",
        {"guest_name": "Demo Guest Ava Reid"},
        {
            "guest_name": "Demo Guest Ava Reid",
            "email": "ava.reid@example.com",
            "phone": "+91 90000 00002",
            "nationality": "Indian",
            "loyalty_tier": "Gold",
            "vip": 1,
            "preferences": "Late checkout and a quiet room.",
        },
        result,
    )
    reservation_name = _ensure(
        "Hospitality ADV Reservation",
        {"guest": guest_name, "room": rooms.get("D201"), "arrival_date": nowdate()},
        {
            "property": property_name,
            "guest": guest_name,
            "arrival_date": nowdate(),
            "departure_date": add_days(nowdate(), 3),
            "room_type": room_types.get("Demo Suite"),
            "room": rooms.get("D201"),
            "status": "Confirmed",
            "source": "Direct",
            "adults": 2,
            "rate": 9800,
            "channel_reference": "HADV-DEMO-RES",
        },
        result,
    )
    task_name = _ensure(
        "Hospitality ADV Operation Task",
        {"subject": "Prepare welcome amenities for D201"},
        {
            "task_type": "Guest Request",
            "property": property_name,
            "room": rooms.get("D201"),
            "guest": guest_name,
            "reservation": reservation_name,
            "subject": "Prepare welcome amenities for D201",
            "description": "Demo task for the command center.",
            "priority": "High",
            "status": "Open",
        },
        result,
    )
    _ensure(
        "Hospitality ADV Housekeeping Inspection",
        {"room": rooms.get("D102")},
        {
            "room": rooms.get("D102"),
            "clean_status": "Pending",
            "linen": "Passed",
            "minibar": "Pending",
            "amenities": "Passed",
            "issues": "Refresh towels and minibar.",
        },
        result,
    )
    _ensure(
        "Hospitality ADV Maintenance Event",
        {"subject": "Demo air-conditioning inspection"},
        {
            "room": rooms.get("D101"),
            "subject": "Demo air-conditioning inspection",
            "issue_type": "HVAC",
            "severity": "Medium",
            "status": "Open",
        },
        result,
    )
    _ensure(
        "Hospitality ADV Hotspot Session",
        {"device_name": "Ava's Tablet"},
        {
            "guest": guest_name,
            "room": rooms.get("D201"),
            "device_name": "Ava's Tablet",
            "ip_address": "10.20.0.41",
            "mac_address": "00:11:22:33:44:55",
            "plan": "Premium",
            "used_bytes": 835000000,
            "status": "Active",
        },
        result,
    )
    _ensure(
        "Hospitality ADV Network Flow",
        {"host_ip": "10.20.0.41"},
        {
            "host_ip": "10.20.0.41",
            "destination_ip": "142.250.77.46",
            "protocol": "tcp",
            "port_service": "443 HTTPS",
            "total_bytes": 184000000,
            "connections": 12,
            "in_bytes": 151000000,
            "out_bytes": 33000000,
        },
        result,
    )
    _ensure(
        "Hospitality ADV Lift Permission",
        {"profile_name": "Demo VIP Guest"},
        {
            "profile_name": "Demo VIP Guest",
            "identity_type": "VIP Guest",
            "floors": "L,1,2,EXEC",
            "amenity_zones": "Pool, Gym, Lounge",
            "active": 1,
        },
        result,
    )
    _ensure(
        "Hospitality ADV Guest Credential",
        {"guest": guest_name},
        {
            "guest": guest_name,
            "room": rooms.get("D201"),
            "credential_type": "Mobile Key",
            "status": "Active",
            "valid_from": nowdate(),
            "valid_until": add_days(nowdate(), 3),
            "lift_profile": "Demo VIP Guest",
        },
        result,
    )
    _ensure(
        "Hospitality ADV Access Event",
        {"credential_id": "HADV-DEMO-KEY"},
        {
            "credential_id": "HADV-DEMO-KEY",
            "identity_type": "Guest",
            "guest": guest_name,
            "room": rooms.get("D201"),
            "zone": "Executive Lounge",
            "event_time": frappe.utils.now(),
            "result": "Granted",
            "controller": "Demo Controller",
        },
        result,
    )
    outlet_name = _ensure(
        "Hospitality ADV POS Outlet",
        {"outlet_name": "Demo Harbour Restaurant"},
        {"property": property_name, "outlet_name": "Demo Harbour Restaurant", "active": 1},
        result,
    )
    _ensure(
        "Hospitality ADV POS Order",
        {"outlet": outlet_name, "guest": guest_name},
        {
            "outlet": outlet_name,
            "guest": guest_name,
            "room": rooms.get("D201"),
            "posting_datetime": frappe.utils.now(),
            "status": "Draft",
            "subtotal": 1250,
            "tax": 225,
            "grand_total": 1475,
        },
        result,
    )
    _ensure(
        "Hospitality ADV OTA Channel",
        {"channel": "Demo Booking Channel"},
        {
            "property": property_name,
            "channel": "Demo Booking Channel",
            "status": "Healthy",
            "reservations_today": 4,
            "mapping_warnings": 1,
            "last_sync": frappe.utils.now(),
        },
        result,
    )
    _ensure(
        "Hospitality ADV Integration Event",
        {"integration": "Demo ERPNext Sync"},
        {
            "integration": "Demo ERPNext Sync",
            "event_type": "Sync",
            "status": "Healthy",
            "message": "Demo integration data loaded.",
            "event_time": frappe.utils.now(),
        },
        result,
    )
    _ensure(
        "Hospitality ADV Guest Stay",
        {"guest": guest_name, "room": rooms.get("D101")},
        {
            "reservation": reservation_name,
            "guest": guest_name,
            "room": rooms.get("D101"),
            "checked_in_at": frappe.utils.now(),
            "folio_balance": 2450,
            "status": "In House",
        },
        result,
    )
    _ensure(
        "Hospitality ADV Staff Roster",
        {"employee_name": "Demo Front Office"},
        {
            "employee_name": "Demo Front Office",
            "department": "Front Office",
            "shift_type": "Morning",
            "attendance_status": "Present",
            "check_in": frappe.utils.now(),
            "task_count": 3,
        },
        result,
    )
    _ensure(
        "Hospitality ADV Guest Message",
        {"subject": "Demo airport pickup request"},
        {
            "guest": guest_name,
            "room": rooms.get("D201"),
            "reservation": reservation_name,
            "subject": "Demo airport pickup request",
            "message": "Please arrange a pickup at 18:30.",
            "priority": "High",
            "status": "Open",
            "task": task_name,
        },
        result,
    )


def _seed_erpnext(result):
    company = frappe.defaults.get_global_default("company") or _first_name("Company")
    customer_group = _first_name("Customer Group")
    territory = _first_name("Territory")
    supplier_group = _first_name("Supplier Group")
    item_group = _first_name("Item Group")
    stock_uom = _first_name("UOM") or "Nos"
    warehouse = _first_name("Warehouse")

    customer = _ensure(
        "Customer",
        {"customer_name": DEMO_CUSTOMER},
        {
            "customer_name": DEMO_CUSTOMER,
            "customer_type": "Company",
            "customer_group": customer_group,
            "territory": territory,
        },
        result,
    )
    supplier = _ensure(
        "Supplier",
        {"supplier_name": DEMO_SUPPLIER},
        {"supplier_name": DEMO_SUPPLIER, "supplier_group": supplier_group},
        result,
    )
    item = _ensure(
        "Item",
        {"item_code": DEMO_ITEM},
        {
            "item_code": DEMO_ITEM,
            "item_name": "Hospitality ADV Demo Minibar Item",
            "item_group": item_group,
            "stock_uom": stock_uom,
            "is_stock_item": 1,
        },
        result,
    )
    if not all([company, customer, supplier, item]):
        result["skipped"].append(
            "ERPNext transactions: Company, Customer, Supplier, and Item must be available"
        )
        return

    item_row = [{"item_code": item, "qty": 2, "rate": 1250, "uom": stock_uom}]

    _ensure(
        "Quotation",
        {"party_name": customer, "docstatus": 0},
        {
            "quotation_to": "Customer",
            "party_name": customer,
            "transaction_date": nowdate(),
            "valid_till": add_days(nowdate(), 14),
            "company": company,
            "items": item_row,
        },
        result,
    )
    _ensure(
        "Sales Invoice",
        {"customer": customer, "docstatus": 0},
        {
            "company": company,
            "customer": customer,
            "posting_date": nowdate(),
            "due_date": add_days(nowdate(), 14),
            "items": item_row,
        },
        result,
    )
    _ensure(
        "Purchase Order",
        {"supplier": supplier, "docstatus": 0},
        {
            "company": company,
            "supplier": supplier,
            "transaction_date": nowdate(),
            "schedule_date": add_days(nowdate(), 7),
            "items": item_row,
        },
        result,
    )
    _ensure(
        "Purchase Invoice",
        {"supplier": supplier, "docstatus": 0},
        {
            "company": company,
            "supplier": supplier,
            "posting_date": nowdate(),
            "due_date": add_days(nowdate(), 14),
            "items": item_row,
        },
        result,
    )
    _ensure(
        "Material Request",
        {"material_request_type": "Material Purchase", "docstatus": 0},
        {
            "company": company,
            "material_request_type": "Material Purchase",
            "transaction_date": nowdate(),
            "schedule_date": add_days(nowdate(), 5),
            "items": [{"item_code": item, "qty": 8, "schedule_date": add_days(nowdate(), 5), "uom": stock_uom}],
        },
        result,
    )
    employee = _ensure(
        "Employee",
        {"first_name": "Demo Hospitality Associate"},
        {
            "first_name": "Demo Hospitality Associate",
            "company": company,
            "date_of_joining": nowdate(),
            "status": "Active",
            "gender": "Female",
        },
        result,
    )
    _ensure(
        "Attendance",
        {"employee": employee, "attendance_date": nowdate()},
        {"employee": employee, "attendance_date": nowdate(), "status": "Present", "company": company},
        result,
    )
    leave_type = _first_name("Leave Type")
    _ensure(
        "Leave Application",
        {"employee": employee, "from_date": add_days(nowdate(), 7)},
        {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": add_days(nowdate(), 7),
            "to_date": add_days(nowdate(), 8),
            "company": company,
        },
        result,
    )


def seed_demo_data():
    """Create idempotent demo records for the Hospitality ADV command center.

    Run with: bench --site your-site.local execute hospitality_adv.demo.seed_demo_data
    """

    _require_system_manager()
    result = defaultdict(list)
    _seed_hospitality(result)
    _seed_erpnext(result)
    frappe.db.commit()
    return dict(result)
