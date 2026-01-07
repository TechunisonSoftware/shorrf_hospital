import frappe
from healthcare.healthcare.doctype.patient.patient import generate_uid
 
 
 
def execute():
    
    patients = frappe.get_all("Patient", filters={"uid": ["is", "not set"]}, fields=["name", "company"])
    if not patients:
        frappe.logger().info("No patients found without UID. Skipping.")
        return
    frappe.logger().info(f"Found {len(patients)} patients without UID. Generating UIDs and SVGs.")
    # Generate UID and SVG for each patient
    print(f"Generating UID and SVG for {len(patients)} patients")
    for patient in patients:
        try:
            if not patient.company:
                frappe.logger().warning(f"Patient {patient.name} has no company. Skipping.")
                continue
 
            uid = generate_uid(patient.company)
            
 
            frappe.db.set_value("Patient", patient.name, {
                "uid": uid
               
            })
 
            frappe.logger().info(f"Updated UID + SVG for Patient {patient.name}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to update Patient {patient.name}")