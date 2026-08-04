"""Desk session customizations for Hospitality ADV."""

import frappe


COMMAND_CENTER_PAGE = "hospitality-adv-dashboard"


def set_command_center_home(bootinfo):
    """Route permitted Desk users to the Command Center after the normal boot completes."""
    if frappe.session.user == "Guest":
        return

    try:
        page = frappe.get_cached_doc("Page", COMMAND_CENTER_PAGE)
    except frappe.DoesNotExistError:
        return

    if page.is_permitted():
        bootinfo.home_page = COMMAND_CENTER_PAGE
