import frappe


MODULE = "ADV Hospitality Backend"


def field(label, fieldtype="Data", **kwargs):
    fieldname = kwargs.pop("fieldname", frappe.scrub(label))
    docfield = {"label": label, "fieldname": fieldname, "fieldtype": fieldtype}
    docfield.update(kwargs)
    return docfield


def permission(role, read=1, write=1, create=1, delete=0, submit=0, cancel=0):
    return {
        "role": role,
        "read": read,
        "write": write,
        "create": create,
        "delete": delete,
        "submit": submit,
        "cancel": cancel,
    }


COMMON_PERMS = [
    permission("System Manager", delete=1),
    permission("Hotel Operations Manager", delete=1),
    permission("Front Desk Agent", delete=0),
    permission("Housekeeping Supervisor", delete=0),
    permission("Security Operator", delete=0),
]


def after_install():
    ensure_roles()
    ensure_module()
    for definition in doctype_definitions():
        ensure_doctype(definition)
    seed_records()
    frappe.clear_cache()


def before_uninstall():
    frappe.msgprint(
        "ADV Hospitality Backend data is preserved. Delete DocTypes manually only after exporting or archiving hotel records."
    )


def ensure_roles():
    for role in ["Hotel Operations Manager", "Front Desk Agent", "Housekeeping Supervisor", "Security Operator"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def ensure_module():
    if not frappe.db.exists("Module Def", MODULE):
        frappe.get_doc({"doctype": "Module Def", "module_name": MODULE, "app_name": "adv_hospitality_backend"}).insert(
            ignore_permissions=True
        )


def ensure_doctype(definition):
    if frappe.db.exists("DocType", definition["name"]):
        return
    fields = []
    for idx, docfield in enumerate(definition.pop("fields"), start=1):
        docfield["idx"] = idx
        fields.append(docfield)
    doc = {
        "doctype": "DocType",
        "custom": 1,
        "module": MODULE,
        "istable": 0,
        "track_changes": 1,
        "permissions": COMMON_PERMS,
        **definition,
        "fields": fields,
    }
    frappe.get_doc(doc).insert(ignore_permissions=True)


def doctype_definitions():
    return [
        {
            "name": "ADV Property",
            "autoname": "field:property_name",
            "title_field": "property_name",
            "fields": [
                field("Property Name", reqd=1, unique=1),
                field("Hotel Code", reqd=1, unique=1),
                field("Company", "Link", options="Company"),
                field("Default Currency", "Link", options="Currency", default="PGK"),
                field("Timezone", default="Pacific/Port_Moresby"),
                field("Address", "Small Text"),
                field("Phone"),
                field("Email", "Data", options="Email"),
            ],
        },
        {
            "name": "ADV Room Type",
            "autoname": "field:room_type_name",
            "title_field": "room_type_name",
            "fields": [
                field("Room Type Name", reqd=1, unique=1),
                field("Capacity", "Int", default=2),
                field("Base Rate", "Currency"),
                field("Description", "Small Text"),
            ],
        },
        {
            "name": "ADV Room",
            "autoname": "field:room_number",
            "title_field": "room_number",
            "fields": [
                field("Room Number", reqd=1, unique=1),
                field("Property", "Link", options="ADV Property", reqd=1),
                field("Room Type", "Link", options="ADV Room Type", reqd=1),
                field("Floor"),
                field("Status", "Select", options="Vacant Clean\nVacant Dirty\nOccupied\nReserved / VIP\nMaintenance", default="Vacant Clean"),
                field("Housekeeping Status", "Select", options="Passed\nPending\nNeeds Review", default="Passed"),
                field("Internet Available", "Check", default=1),
                field("Door Lock Working", "Check", default=1),
                field("Folio Balance", "Currency"),
                field("Guest Message Pending", "Check"),
                field("Cleaning Scheduled", "Datetime"),
                field("Current Guest", "Link", options="ADV Guest"),
            ],
        },
        {
            "name": "ADV Guest",
            "autoname": "field:guest_name",
            "title_field": "guest_name",
            "fields": [
                field("Guest Name", reqd=1),
                field("ERPNext Customer", "Link", options="Customer"),
                field("Email", "Data", options="Email"),
                field("Phone"),
                field("Nationality"),
                field("Loyalty Tier", "Select", options="Standard\nSilver\nGold\nPlatinum"),
                field("VIP", "Check"),
                field("Preferences", "Small Text"),
                field("ID Document", "Attach"),
            ],
        },
        {
            "name": "ADV Reservation",
            "autoname": "format:ADV-RES-.#####",
            "title_field": "guest",
            "fields": [
                field("Property", "Link", options="ADV Property", reqd=1),
                field("Guest", "Link", options="ADV Guest", reqd=1),
                field("Arrival Date", "Date", reqd=1),
                field("Departure Date", "Date", reqd=1),
                field("Room Type", "Link", options="ADV Room Type", reqd=1),
                field("Room", "Link", options="ADV Room"),
                field("Status", "Select", options="Draft\nConfirmed\nChecked In\nChecked Out\nCancelled\nNo Show", default="Confirmed"),
                field("Source", "Select", options="Direct\nBooking.com\nExpedia\nAgoda\nWalk In\nCorporate\nOTA"),
                field("Adults", "Int", default=1),
                field("Children", "Int"),
                field("Rate", "Currency"),
                field("Channel Reference"),
                field("Notes", "Small Text"),
            ],
        },
        {
            "name": "ADV Guest Stay",
            "autoname": "format:ADV-STAY-.#####",
            "title_field": "guest",
            "fields": [
                field("Reservation", "Link", options="ADV Reservation"),
                field("Guest", "Link", options="ADV Guest", reqd=1),
                field("Room", "Link", options="ADV Room", reqd=1),
                field("Checked In At", "Datetime"),
                field("Checked Out At", "Datetime"),
                field("Folio Balance", "Currency"),
                field("Status", "Select", options="Expected\nIn House\nDue Out\nDeparted", default="Expected"),
            ],
        },
        {
            "name": "ADV Guest Message",
            "autoname": "format:ADV-MSG-.#####",
            "title_field": "subject",
            "fields": [
                field("Guest", "Link", options="ADV Guest"),
                field("Room", "Link", options="ADV Room"),
                field("Reservation", "Link", options="ADV Reservation"),
                field("Subject", reqd=1),
                field("Message", "Text Editor", reqd=1),
                field("Priority", "Select", options="Low\nMedium\nHigh\nUrgent", default="Medium"),
                field("Status", "Select", options="Open\nAssigned\nResolved\nClosed", default="Open"),
                field("Task", "Link", options="ADV Operation Task"),
            ],
        },
        {
            "name": "ADV Operation Task",
            "autoname": "format:ADV-TASK-.#####",
            "title_field": "subject",
            "fields": [
                field("Task Type", "Select", options="Housekeeping\nMaintenance\nRegular Check\nGuest Request\nSecurity\nInternet\nFront Desk", reqd=1),
                field("Property", "Link", options="ADV Property"),
                field("Room", "Link", options="ADV Room"),
                field("Guest", "Link", options="ADV Guest"),
                field("Reservation", "Link", options="ADV Reservation"),
                field("Subject", reqd=1),
                field("Description", "Small Text"),
                field("Priority", "Select", options="Low\nMedium\nHigh\nUrgent", default="Medium"),
                field("Status", "Select", options="Open\nAssigned\nIn Progress\nBlocked\nDone\nCancelled", default="Open"),
                field("Assigned To", "Link", options="User"),
                field("Due Datetime", "Datetime"),
                field("Completed On", "Datetime"),
            ],
        },
        {
            "name": "ADV Housekeeping Inspection",
            "autoname": "format:ADV-HK-.#####",
            "title_field": "room",
            "fields": [
                field("Room", "Link", options="ADV Room", reqd=1),
                field("Inspector", "Link", options="User"),
                field("Clean Status", "Select", options="Passed\nPending\nNeeds Review", default="Pending"),
                field("Linen", "Select", options="Passed\nPending\nNeeds Review", default="Pending"),
                field("Minibar", "Select", options="Passed\nPending\nNeeds Review", default="Pending"),
                field("Amenities", "Select", options="Passed\nPending\nNeeds Review", default="Pending"),
                field("Issues", "Small Text"),
            ],
        },
        {
            "name": "ADV Maintenance Event",
            "autoname": "format:ADV-MAINT-.#####",
            "title_field": "subject",
            "fields": [
                field("Room", "Link", options="ADV Room"),
                field("Asset", "Link", options="Asset"),
                field("Subject", reqd=1),
                field("Issue Type", "Select", options="Electrical\nPlumbing\nHVAC\nFurniture\nDoor Lock\nInternet\nOther"),
                field("Severity", "Select", options="Low\nMedium\nHigh\nCritical", default="Medium"),
                field("Status", "Select", options="Open\nAssigned\nIn Progress\nResolved\nClosed", default="Open"),
                field("Assigned To", "Link", options="User"),
                field("Scheduled For", "Datetime"),
            ],
        },
        {
            "name": "ADV Hotspot Session",
            "autoname": "format:ADV-WIFI-.#####",
            "title_field": "device_name",
            "fields": [
                field("Guest", "Link", options="ADV Guest"),
                field("Room", "Link", options="ADV Room"),
                field("Device Name"),
                field("IP Address"),
                field("MAC Address"),
                field("Plan"),
                field("Used Bytes", "Float"),
                field("Down Speed"),
                field("Up Speed"),
                field("Status", "Select", options="Active\nIdle\nExpired\nBlocked", default="Active"),
            ],
        },
        {
            "name": "ADV Network Flow",
            "autoname": "format:ADV-FLOW-.#####",
            "title_field": "host_ip",
            "fields": [
                field("Host IP", reqd=1),
                field("Destination IP"),
                field("Protocol", "Select", options="tcp\nudp\nicmp\nother"),
                field("Port Service"),
                field("Total Bytes", "Float"),
                field("Connections", "Int"),
                field("In Bytes", "Float"),
                field("Out Bytes", "Float"),
            ],
        },
        {
            "name": "ADV Access Event",
            "autoname": "format:ADV-ACCESS-.#####",
            "title_field": "zone",
            "fields": [
                field("Credential ID"),
                field("Identity Type", "Select", options="Guest\nEmployee\nVendor\nSystem", default="Guest"),
                field("Guest", "Link", options="ADV Guest"),
                field("Employee", "Link", options="Employee"),
                field("Room", "Link", options="ADV Room"),
                field("Zone"),
                field("Event Time", "Datetime"),
                field("Result", "Select", options="Granted\nDenied\nAlert", default="Granted"),
                field("Controller"),
            ],
        },
        {
            "name": "ADV Guest Credential",
            "autoname": "format:ADV-CRED-.#####",
            "title_field": "guest",
            "fields": [
                field("Guest", "Link", options="ADV Guest", reqd=1),
                field("Room", "Link", options="ADV Room"),
                field("Credential Type", "Select", options="Mobile Key\nRFID Card\nPIN\nQR", default="Mobile Key"),
                field("Status", "Select", options="Active\nSuspended\nExpired\nRevoked", default="Active"),
                field("Valid From", "Datetime"),
                field("Valid Until", "Datetime"),
                field("Lift Profile", "Link", options="ADV Lift Permission"),
            ],
        },
        {
            "name": "ADV Lift Permission",
            "autoname": "field:profile_name",
            "title_field": "profile_name",
            "fields": [
                field("Profile Name", reqd=1, unique=1),
                field("Identity Type", "Select", options="Guest\nVIP Guest\nReception\nHousekeeping\nMaintenance\nSecurity", reqd=1),
                field("Floors", "Data", description="Comma separated floor keys such as B,L,1,2,3,4,5,EXEC."),
                field("Amenity Zones", "Small Text"),
                field("Active", "Check", default=1),
            ],
        },
        {
            "name": "ADV POS Outlet",
            "autoname": "field:outlet_name",
            "title_field": "outlet_name",
            "fields": [
                field("Property", "Link", options="ADV Property"),
                field("Outlet Name", reqd=1, unique=1),
                field("Cost Center", "Link", options="Cost Center"),
                field("Default Warehouse", "Link", options="Warehouse"),
                field("Default Income Account", "Link", options="Account"),
                field("Active", "Check", default=1),
            ],
        },
        {
            "name": "ADV POS Order",
            "autoname": "format:ADV-POS-.#####",
            "title_field": "outlet",
            "fields": [
                field("Outlet", "Link", options="ADV POS Outlet", reqd=1),
                field("Guest", "Link", options="ADV Guest"),
                field("Room", "Link", options="ADV Room"),
                field("Posting Datetime", "Datetime"),
                field("Status", "Select", options="Draft\nSubmitted\nPaid\nPosted to Folio\nCancelled", default="Draft"),
                field("Subtotal", "Currency"),
                field("Tax", "Currency"),
                field("Grand Total", "Currency"),
                field("Folio Posted", "Check"),
                field("ERPNext Sales Invoice", "Link", options="Sales Invoice"),
            ],
        },
        {
            "name": "ADV Staff Roster",
            "autoname": "format:ADV-ROSTER-.#####",
            "title_field": "employee_name",
            "fields": [
                field("Employee", "Link", options="Employee"),
                field("Employee Name"),
                field("Department"),
                field("Shift Type"),
                field("Attendance Status", "Select", options="Present\nLate\nAbsent\nOn Leave", default="Present"),
                field("Check In", "Datetime"),
                field("Check Out", "Datetime"),
                field("Task Count", "Int"),
            ],
        },
        {
            "name": "ADV OTA Channel",
            "autoname": "field:channel",
            "title_field": "channel",
            "fields": [
                field("Property", "Link", options="ADV Property"),
                field("Channel", reqd=1, unique=1),
                field("Status", "Select", options="Healthy\nWarning\nError\nPaused", default="Healthy"),
                field("Reservations Today", "Int"),
                field("Mapping Warnings", "Int"),
                field("Last Sync", "Datetime"),
            ],
        },
        {
            "name": "ADV Integration Event",
            "autoname": "format:ADV-INT-.#####",
            "title_field": "integration",
            "fields": [
                field("Integration", reqd=1),
                field("Event Type", "Select", options="Sync\nWebhook\nExport\nImport\nAlert"),
                field("Status", "Select", options="Healthy\nWarning\nFailed\nQueued", default="Healthy"),
                field("Reference Doctype", "Link", options="DocType"),
                field("Reference Name"),
                field("Message", "Small Text"),
                field("Event Time", "Datetime"),
            ],
        },
    ]


def seed_records():
    seed("ADV Property", "Harbour View Hotel", property_name="Harbour View Hotel", hotel_code="HVH", timezone="Pacific/Port_Moresby")
    for room_type, rate, capacity in [
        ("Single", 420, 1),
        ("Double", 560, 2),
        ("Triple", 720, 3),
        ("Executive Suite", 1150, 3),
        ("Accessible", 620, 2),
    ]:
        seed("ADV Room Type", room_type, room_type_name=room_type, base_rate=rate, capacity=capacity)

    for room_number, room_type, status, floor in [
        ("101", "Single", "Vacant Clean", "1"),
        ("102", "Single", "Vacant Dirty", "1"),
        ("103", "Double", "Occupied", "1"),
        ("104", "Double", "Reserved / VIP", "1"),
        ("105", "Double", "Occupied", "1"),
        ("106", "Triple", "Vacant Clean", "1"),
        ("107", "Triple", "Maintenance", "1"),
        ("108", "Executive Suite", "Occupied", "1"),
        ("508", "Executive Suite", "Occupied", "5"),
        ("621", "Accessible", "Reserved / VIP", "6"),
    ]:
        seed(
            "ADV Room",
            room_number,
            room_number=room_number,
            property="Harbour View Hotel",
            room_type=room_type,
            status=status,
            floor=floor,
            internet_available=1,
            door_lock_working=1,
            folio_balance=850 if status == "Occupied" else 0,
        )

    seed("ADV Guest", "Sarah Williams", guest_name="Sarah Williams", email="sarah@example.com", loyalty_tier="Gold", vip=1, preferences="High floor, quiet room, late checkout.")
    seed("ADV Guest", "Mei Zhang", guest_name="Mei Zhang", email="mei@example.com", loyalty_tier="Gold", vip=1)
    seed(
        "ADV Lift Permission",
        "VIP guest",
        profile_name="VIP guest",
        identity_type="VIP Guest",
        floors="B,L,1,2,3,4,5,EXEC",
        amenity_zones="Gym, Pool, Parking",
        active=1,
    )
    seed("ADV Lift Permission", "Housekeeping", profile_name="Housekeeping", identity_type="Housekeeping", floors="L,1,2,3,4,5,6", active=1)
    seed("ADV POS Outlet", "Harbour Restaurant", property="Harbour View Hotel", outlet_name="Harbour Restaurant", active=1)
    for channel in ["Booking.com", "Expedia", "Agoda", "Direct Booking Engine"]:
        seed("ADV OTA Channel", channel, property="Harbour View Hotel", channel=channel, status="Healthy")
    seed(
        "ADV Integration Event",
        None,
        integration="ERPNext Core",
        event_type="Sync",
        status="Healthy",
        message="Reservation, POS and HR sync ready.",
        event_time=frappe.utils.now(),
    )


def seed(doctype, name=None, **values):
    lookup = name or values.get("name")
    if lookup and frappe.db.exists(doctype, lookup):
        return
    if not lookup and frappe.db.exists(doctype, values):
        return
    frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True, ignore_mandatory=True)

