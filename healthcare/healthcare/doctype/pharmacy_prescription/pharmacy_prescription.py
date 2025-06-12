import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class PharmacyPrescription(Document):
    pass
    
         

@frappe.whitelist()
def get_medication_quantity(order_group, medication_item):
    """Fetch quantity of medication from Medication Request"""
    medication_requests = frappe.get_all(
        'Medication Request',
        filters={'order_group': order_group, 'medication_item': medication_item},
        fields=['quantity']
    )

    return medication_requests[0].get('quantity') if medication_requests else None

@frappe.whitelist()
def create_stock_entry(prescription_name, item, source_warehouse, target_warehouse, quantity):
    """Create a stock entry for the dispensed medication"""
    try:
        if not all([item, source_warehouse, target_warehouse, quantity]):
            frappe.throw("All fields are required to create a Stock Entry.")

        # Create Stock Entry
        stock_entry = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Issue',
            'items': [
                {
                    'item_code': item,
                    'qty': float(quantity),
                    's_warehouse': source_warehouse,
                    't_warehouse': target_warehouse
                }
            ]
        })
        stock_entry.insert()
        stock_entry.submit()

        # Fetch and update Stock Ledger Entries for this Stock Entry
        sle_entries = frappe.get_all("Stock Ledger Entry", filters={"voucher_no": stock_entry.name}, fields=["name"])
        for sle in sle_entries:
            new_name = make_autoname("MAT-SLE-.YYYY.-.#####")
            frappe.db.set_value("Stock Ledger Entry", sle["name"], "name", new_name)

        frappe.db.commit()  # Commit changes to apply new naming

        # frappe.msgprint(f"Stock Entry {stock_entry.name} has been created successfully.")
        return stock_entry.name
    except Exception as e:
        frappe.log_error(message=str(e), title="Stock Entry Creation Error")
        

@frappe.whitelist()
def get_medication_requests(patient_encounter):
    """Fetch Medication Requests and update status to 'Completed'"""
    
    # Fetch the 'Completed' entry from Code Value
    completed_status = frappe.get_value(
        "Code Value",
        {"code_system": "Medication Request Status", "code_value": "completed"},
        "name")

    if not completed_status:
        frappe.throw("The 'Completed' status does not exist in Code Value!")

    # Fetch all Medication Requests linked to the given Patient Encounter
    medication_requests = frappe.get_all(
        'Medication Request',
        filters={'order_group': patient_encounter},
        fields=['name', 'medication_item']
    )

    # Update the status of each Medication Request to 'Completed'
    for request in medication_requests:
        frappe.db.set_value('Medication Request', request['name'], 'status', completed_status)

    frappe.db.commit()  # Save changes
    return medication_requests


@frappe.whitelist()
def update_medication_request_status(medication_request_name):
    """Update the Medication Request status to 'Completed' only for the dispensed request"""

    if not medication_request_name:
        frappe.throw("Invalid Medication Request Name!")

    # Get the 'Completed' status from Code Value
    completed_status = frappe.get_value(
        "Code Value",
        {"code_system": "Medication Request Status", "code_value": "completed"},
        "name"
    )

    if not completed_status:
        frappe.throw("The 'Completed' status does not exist in Code Value!")

    # Check if the Medication Request exists
    medication_request_exists = frappe.db.exists("Medication Request", medication_request_name)
    if not medication_request_exists:
        frappe.throw(f"Medication Request {medication_request_name} does not exist!")

    # Update the Medication Request status
    frappe.db.set_value('Medication Request', medication_request_name, 'status', completed_status)
    frappe.db.commit()  # Save changes

    frappe.logger().info(f"✅ Medication Request {medication_request_name} updated to Completed.")

    return {"status": "Updated", "medication_request": medication_request_name}




@frappe.whitelist()
def update_prescription_status(prescription_name, status):
    frappe.db.set_value("Pharmacy Prescription", prescription_name, "status", status)
    frappe.db.commit()
    return f"Prescription {prescription_name} updated to {status}"

@frappe.whitelist()
def update_dispensed_amount(row_name, new_dispensed_amount):
    doc = frappe.get_doc("Pharmacy Drug Prescription", row_name)
    doc.dispensed_amount = new_dispensed_amount
    doc.save()
    frappe.db.commit()
    return "Updated"

@frappe.whitelist()
def get_item_rate(item_code):
    """Fetch price rate of an item from Item Price or Item master"""
    if not item_code:
        return 0
    
    print("Item code ",item_code)
 
    # First try Item Price (Selling)
    price = frappe.get_value("Item Price", {
        "item_code": item_code,
        "selling": 1
    }, "price_list_rate")
 
    # If not found, fallback to Item master 'standard_rate'
    if price is None:
        price = frappe.get_value("Item", item_code, "standard_rate")
 
    return price or 0