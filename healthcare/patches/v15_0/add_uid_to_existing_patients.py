import frappe
from healthcare.healthcare.doctype.patient.patient import generate_uid

def generate_full_svg(uid):
    return f"""<svg height="88px" width="100%" x="0px" y="0px" viewBox="0 0 323 88" xmlns="http://www.w3.org/2000/svg" version="1.1" style="transform: translate(0,0)" data-barcode-value="{uid}">
    <rect x="0" y="0" width="323" height="88" style="fill:#ffffff;"></rect>
    <g transform="translate(10, 10)" style="fill:#000000;">
    <rect x="0" y="0" width="6" height="50"></rect>
    <rect x="9" y="0" width="3" height="50"></rect>
    <rect x="18" y="0" width="3" height="50"></rect>
    <rect x="33" y="0" width="6" height="50"></rect>
    <rect x="48" y="0" width="3" height="50"></rect>
    <rect x="54" y="0" width="9" height="50"></rect>
    <rect x="66" y="0" width="3" height="50"></rect>
    <rect x="72" y="0" width="9" height="50"></rect>
    <rect x="84" y="0" width="12" height="50"></rect>
    <rect x="99" y="0" width="9" height="50"></rect>
    <rect x="114" y="0" width="3" height="50"></rect>
    <rect x="120" y="0" width="6" height="50"></rect>
    <rect x="132" y="0" width="6" height="50"></rect>
    <rect x="141" y="0" width="6" height="50"></rect>
    <rect x="153" y="0" width="6" height="50"></rect>
    <rect x="165" y="0" width="6" height="50"></rect>
    <rect x="174" y="0" width="6" height="50"></rect>
    <rect x="186" y="0" width="6" height="50"></rect>
    <rect x="198" y="0" width="6" height="50"></rect>
    <rect x="210" y="0" width="6" height="50"></rect>
    <rect x="222" y="0" width="6" height="50"></rect>
    <rect x="231" y="0" width="9" height="50"></rect>
    <rect x="243" y="0" width="6" height="50"></rect>
    <rect x="255" y="0" width="3" height="50"></rect>
    <rect x="264" y="0" width="6" height="50"></rect>
    <rect x="279" y="0" width="9" height="50"></rect>
    <rect x="291" y="0" width="3" height="50"></rect>
    <rect x="297" y="0" width="6" height="50"></rect>
    <text style="font: 16px monospace" text-anchor="middle" x="151.5" y="68">{uid}</text>
    </g></svg>"""

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
            svg = generate_full_svg(uid)

            frappe.db.set_value("Patient", patient.name, {
                "uid": uid,
                "patient_barcode": svg
            })

            frappe.logger().info(f"Updated UID + SVG for Patient {patient.name}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to update Patient {patient.name}")
