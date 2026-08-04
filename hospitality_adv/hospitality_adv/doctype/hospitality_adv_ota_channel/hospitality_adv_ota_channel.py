from frappe.model.document import Document
from hospitality_adv.naming import set_hospitality_adv_name


class HospitalityADVOTAChannel(Document):
    def autoname(self):
        set_hospitality_adv_name(self)
