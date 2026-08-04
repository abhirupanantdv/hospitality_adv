import frappe
from frappe.defaults import get_global_default, set_global_default


DESK_PAGE = "hospitality-adv-dashboard"


def after_install():
    set_default_desk_page()


def after_migrate():
    set_default_desk_page()


def set_default_desk_page():
    set_global_default("desktop:home_page", DESK_PAGE)
    frappe.clear_cache()


def before_uninstall():
    if get_global_default("desktop:home_page") == DESK_PAGE:
        set_global_default("desktop:home_page", None)
        frappe.clear_cache()
