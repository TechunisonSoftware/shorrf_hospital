# Copyright (c) 2025, earthians Health Informatics Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class RadiologyResultEntry(Document):
    def on_submit(self):
    
        if not self.report_submitted_datetime:
            self.report_submitted_datetime = now_datetime()
            self.save()
