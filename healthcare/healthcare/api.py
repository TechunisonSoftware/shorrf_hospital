import frappe




@frappe.whitelist()
def update_lab_test_status_by_patient(sample_collection):
    if not sample_collection:
        frappe.throw(("Sample Collection is not specified"))

    try:
        lab_tests = frappe.get_all(
            "Lab Test",
            filters={"sample": sample_collection, "lab_status": ["in", ["Draft", "Collection","Result Entry"]],  "docstatus": 0 },
            fields=["name"]
        )

        if not lab_tests:
            return "No Lab Test records found for the specified patient"

        for lab_test in lab_tests:
            lab_test_doc = frappe.get_doc("Lab Test", lab_test["name"])
            lab_test_doc.lab_status = "Acknowledge"
            lab_test_doc.save()
        frappe.db.commit()
        return "success"
        
    except Exception as e:
        frappe.log_error(f"Error updating Lab Test status for patient {sample_collection}: {str(e)}", "Update Lab Test Status")
        return "error"



@frappe.whitelist()
def update_lab_test_status_based_on_items(doc, method):
    if not doc.normal_test_items:
        return  # No normal_test_items, nothing to update

    # Loop through each child in the normal_test_items table
    for row in doc.normal_test_items:
        if row.result_value:  # Check if result_value is updated
            if doc.lab_status != "Result Entry":  # Avoid redundant updates
                doc.lab_status = "Result Entry"
                doc.save()
                frappe.db.commit()
                break  # No need to loop once the status is updated