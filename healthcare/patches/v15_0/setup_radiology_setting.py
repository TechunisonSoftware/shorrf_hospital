import frappe

def execute():
    if not frappe.db.exists("Radiology Setting", "Default"):
        doc = frappe.get_doc({
            "doctype": "Radiology Setting",
            "name": "Default",
            "mirth_connect_url": "http://103.42.86.164:6000",
            "authenticate_user": "IntegrationUser",
            "authenticate_password": "H7f!mP2r@9dTqV",
            "orthanc_url": "http://hisuser:hisuser@10.0.0.38:8042"
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()