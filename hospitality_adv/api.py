import frappe
from frappe import _
from frappe.utils import add_days, getdate, now


def _json(data):
    if isinstance(data, str):
        return frappe.parse_json(data)
    return data or {}


def _property_filter(property_name=None):
    return {"property": property_name} if property_name else {}


@frappe.whitelist()
def dashboard(property_name=None):
    room_filters = _property_filter(property_name)
    total_rooms = frappe.db.count("Hospitality ADV Room", room_filters)
    occupied = frappe.db.count("Hospitality ADV Room", {**room_filters, "status": "Occupied"})
    reservations_today = frappe.db.count(
        "Hospitality ADV Reservation",
        {**room_filters, "arrival_date": ["<=", getdate()], "departure_date": [">", getdate()], "status": ["in", ["Confirmed", "Checked In"]]},
    )
    open_tasks = frappe.db.count("Hospitality ADV Operation Task", {"status": ["not in", ["Done", "Cancelled"]]})
    wifi_sessions = frappe.db.count("Hospitality ADV Hotspot Session", {"status": "Active"})
    access_denied = frappe.db.count("Hospitality ADV Access Event", {"result": "Denied"})
    folio_balance = frappe.db.sql(
        "select coalesce(sum(folio_balance), 0) from `tabHospitality ADV Room` where status = 'Occupied'",
        as_list=True,
    )[0][0]

    return {
        "property": property_name,
        "rooms": {"total": total_rooms, "occupied": occupied, "occupancy": round((occupied / total_rooms) * 100, 1) if total_rooms else 0},
        "reservations_today": reservations_today,
        "open_tasks": open_tasks,
        "wifi_sessions": wifi_sessions,
        "access_denied": access_denied,
        "folio_balance": folio_balance,
    }


@frappe.whitelist()
def reservations_calendar(start=None, end=None, view="week", property_name=None):
    start_date = getdate(start) if start else getdate()
    end_date = getdate(end) if end else add_days(start_date, 30 if view == "month" else 7)
    filters = {
        "arrival_date": ["<=", end_date],
        "departure_date": [">=", start_date],
        "status": ["not in", ["Cancelled", "No Show"]],
    }
    if property_name:
        filters["property"] = property_name
    reservations = frappe.get_all(
        "Hospitality ADV Reservation",
        filters=filters,
        fields=["name", "guest", "arrival_date", "departure_date", "room_type", "room", "status", "source", "rate"],
        order_by="arrival_date asc",
    )
    rooms = frappe.get_all(
        "Hospitality ADV Room",
        filters=_property_filter(property_name),
        fields=["name", "room_number", "room_type", "status", "floor"],
        order_by="floor asc, room_number asc",
    )
    return {"view": view, "start": start_date, "end": end_date, "rooms": rooms, "reservations": reservations}


@frappe.whitelist()
def room_status_board(status=None, property_name=None):
    filters = _property_filter(property_name)
    if status and status != "All":
        filters["status"] = status
    rooms = frappe.get_all(
        "Hospitality ADV Room",
        filters=filters,
        fields=[
            "name",
            "room_number",
            "room_type",
            "floor",
            "status",
            "housekeeping_status",
            "internet_available",
            "door_lock_working",
            "folio_balance",
            "guest_message_pending",
            "current_guest",
            "cleaning_scheduled",
        ],
        order_by="floor asc, room_number asc",
    )
    return rooms


@frappe.whitelist()
def create_reservation(data):
    payload = _json(data)
    doc = frappe.get_doc({"doctype": "Hospitality ADV Reservation", **payload})
    doc.insert(ignore_permissions=True)
    if doc.room:
        frappe.db.set_value("Hospitality ADV Room", doc.room, "status", "Reserved / VIP" if payload.get("vip") else "Reserved / VIP")
    return doc.as_dict()


@frappe.whitelist()
def create_task(data):
    payload = _json(data)
    doc = frappe.get_doc({"doctype": "Hospitality ADV Operation Task", **payload})
    doc.insert(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def assign_task(task, assigned_to, due_datetime=None):
    doc = frappe.get_doc("Hospitality ADV Operation Task", task)
    doc.assigned_to = assigned_to
    doc.status = "Assigned"
    if due_datetime:
        doc.due_datetime = due_datetime
    doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def create_task_from_guest_message(doc, method=None):
    if isinstance(doc, str):
        doc = frappe.get_doc("Hospitality ADV Guest Message", doc)
    if getattr(doc, "task", None):
        return
    task = frappe.get_doc(
        {
            "doctype": "Hospitality ADV Operation Task",
            "task_type": "Guest Request",
            "room": doc.room,
            "guest": doc.guest,
            "reservation": doc.reservation,
            "subject": doc.subject,
            "description": frappe.utils.strip_html(doc.message or ""),
            "priority": doc.priority,
            "status": "Open",
        }
    )
    task.insert(ignore_permissions=True)
    doc.db_set("task", task.name)
    doc.db_set("status", "Assigned")
    if doc.room:
        frappe.db.set_value("Hospitality ADV Room", doc.room, "guest_message_pending", 1)


@frappe.whitelist()
def resolve_guest_message(message, task=None):
    doc = frappe.get_doc("Hospitality ADV Guest Message", message)
    doc.status = "Resolved"
    doc.save(ignore_permissions=True)
    if task or doc.task:
        task_doc = frappe.get_doc("Hospitality ADV Operation Task", task or doc.task)
        task_doc.status = "Done"
        task_doc.completed_on = now()
        task_doc.save(ignore_permissions=True)
    if doc.room:
        open_count = frappe.db.count("Hospitality ADV Guest Message", {"room": doc.room, "status": ["in", ["Open", "Assigned"]]})
        frappe.db.set_value("Hospitality ADV Room", doc.room, "guest_message_pending", 1 if open_count else 0)
    return doc.as_dict()


@frappe.whitelist()
def task_list(task_type=None, status=None, property_name=None):
    filters = {}
    if task_type and task_type != "All":
        filters["task_type"] = task_type
    if status and status != "All":
        filters["status"] = status
    if property_name:
        filters["property"] = property_name
    return frappe.get_all(
        "Hospitality ADV Operation Task",
        filters=filters,
        fields=["name", "task_type", "subject", "room", "guest", "priority", "status", "assigned_to", "due_datetime"],
        order_by="modified desc",
        limit_page_length=100,
    )


@frappe.whitelist()
def lift_permission_matrix():
    return frappe.get_all(
        "Hospitality ADV Lift Permission",
        fields=["name", "profile_name", "identity_type", "floors", "amenity_zones", "active"],
        order_by="identity_type asc",
    )


@frappe.whitelist()
def update_lift_permission(profile_name, floors=None, amenity_zones=None, active=1):
    doc = frappe.get_doc("Hospitality ADV Lift Permission", profile_name)
    if floors is not None:
        doc.floors = floors
    if amenity_zones is not None:
        doc.amenity_zones = amenity_zones
    doc.active = int(active)
    doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def internet_summary():
    return {
        "active_sessions": frappe.db.count("Hospitality ADV Hotspot Session", {"status": "Active"}),
        "idle_sessions": frappe.db.count("Hospitality ADV Hotspot Session", {"status": "Idle"}),
        "flows": frappe.get_all(
            "Hospitality ADV Network Flow",
            fields=["host_ip", "destination_ip", "protocol", "port_service", "total_bytes", "connections", "in_bytes", "out_bytes"],
            order_by="total_bytes desc",
            limit_page_length=25,
        ),
    }


@frappe.whitelist()
def pos_summary():
    orders = frappe.get_all("Hospitality ADV POS Order", fields=["outlet", "status", "grand_total", "folio_posted"], limit_page_length=100)
    return {
        "orders": orders,
        "revenue": sum(order.grand_total or 0 for order in orders),
        "folio_pending": len([order for order in orders if not order.folio_posted]),
    }


@frappe.whitelist()
def hr_summary():
    return frappe.get_all(
        "Hospitality ADV Staff Roster",
        fields=["employee", "employee_name", "department", "shift_type", "attendance_status", "task_count"],
        order_by="department asc, employee_name asc",
        limit_page_length=100,
    )


@frappe.whitelist()
def ota_summary(property_name=None):
    return frappe.get_all(
        "Hospitality ADV OTA Channel",
        filters=_property_filter(property_name),
        fields=["channel", "status", "reservations_today", "mapping_warnings", "last_sync"],
        order_by="channel asc",
    )


@frappe.whitelist()
def integration_health():
    return frappe.get_all(
        "Hospitality ADV Integration Event",
        fields=["integration", "event_type", "status", "reference_doctype", "reference_name", "message", "event_time"],
        order_by="event_time desc, modified desc",
        limit_page_length=50,
    )


@frappe.whitelist()
def action_message(title, message=None):
    frappe.publish_realtime(
        "hospitality_adv_action",
        {"title": title, "message": message or _("The action was received and will be routed to ERPNext workflow rules.")},
        user=frappe.session.user,
    )
    return {"ok": True, "title": title, "message": message}
