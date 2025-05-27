# Copyright (c) 2025, earthians Health Informatics Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PatientProfiling(Document):
	pass



@frappe.whitelist()
def get_address_for_patient(patient):
    return frappe.db.sql("""
        SELECT 
            a.city, 
            a.state, a.county, a.pincode
        FROM 
            `tabAddress` a
        JOIN 
            `tabDynamic Link` l ON l.parent = a.name
        WHERE 
            l.link_doctype = 'Patient' AND l.link_name = %s
        LIMIT 1
    """, (patient,), as_dict=True)
