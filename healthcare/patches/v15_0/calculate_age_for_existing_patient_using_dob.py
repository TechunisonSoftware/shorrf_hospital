from datetime import datetime, time
from dateutil.relativedelta import relativedelta
import frappe
 
def execute():
    patients = frappe.get_all(
        "Patient",
        # filters=[
        #     ["dob", "is", "set"],
        #     ["patient_age", "is", "not set"]
        # ],
        fields=["name", "dob"]
    )
    print(f"Found {len(patients)} patients to process.")
 
    for patient in patients:
        dob = patient.dob
        if not dob:
            continue
 
        # Combine date with midnight to match JS behavior
        dob_datetime = datetime.combine(dob, time.min)
        now = datetime.now()
        diff = relativedelta(now, dob_datetime)
 
        age_str = f"{diff.years} Year(s) {diff.months} Month(s) {diff.days} Day(s)"
 
        frappe.db.set_value("Patient", patient.name, "patient_age", age_str)
        profiling_records = frappe.get_all(
            "Patient Profiling",
            filters={"patient": patient.name},
            fields=["name"]
        )
        for profiling in profiling_records:
            frappe.db.set_value("Patient Profiling", profiling.name, "age", age_str)
        
 
    frappe.db.commit()