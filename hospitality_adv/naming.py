"""Consistent document names for Hospitality ADV transactions."""

from frappe.model.naming import getseries
from frappe.utils import nowdate


SERIES_PREFIXES = {
    "Hospitality ADV Access Event": "HADV-ACCESS",
    "Hospitality ADV Guest": "HADV-GUEST",
    "Hospitality ADV Guest Credential": "HADV-CRED",
    "Hospitality ADV Guest Message": "HADV-MSG",
    "Hospitality ADV Guest Stay": "HADV-STAY",
    "Hospitality ADV Hotspot Session": "HADV-WIFI",
    "Hospitality ADV Housekeeping Inspection": "HADV-HK",
    "Hospitality ADV Integration Event": "HADV-INT",
    "Hospitality ADV Lift Permission": "HADV-LIFT",
    "Hospitality ADV Maintenance Event": "HADV-MAINT",
    "Hospitality ADV Network Flow": "HADV-FLOW",
    "Hospitality ADV Operation Task": "HADV-TASK",
    "Hospitality ADV OTA Channel": "HADV-OTA",
    "Hospitality ADV POS Order": "HADV-POS",
    "Hospitality ADV POS Outlet": "HADV-OUTLET",
    "Hospitality ADV Property": "HADV-PROP",
    "Hospitality ADV Reservation": "HADV-RES",
    "Hospitality ADV Room": "HADV-ROOM",
    "Hospitality ADV Room Type": "HADV-RTYPE",
    "Hospitality ADV Staff Roster": "HADV-ROSTER",
}


def set_hospitality_adv_name(doc):
    """Assign IDs such as ``HADV-TASK-2026-00001`` before a document is saved."""
    prefix = SERIES_PREFIXES.get(doc.doctype)
    if not prefix:
        return

    year = nowdate()[:4]
    series_key = f"{prefix}-{year}-"
    doc.name = f"{series_key}{getseries(series_key, 5)}"
