import frappe
from frappe.utils import flt, nowdate
from collections import defaultdict
from frappe.utils import now



@frappe.whitelist()
def create_patient_invoice_summary(patient, from_date, to_date, invoice_status=None):
    patient_doc = frappe.get_doc("Patient", patient)

    doc = frappe.new_doc("Patient Sales Invoice Report")
    doc.patient = patient
    doc.patient_name = patient_doc.patient_name
    doc.patient_age = patient_doc.patient_age
    doc.first_name = patient_doc.first_name
    doc.last_name = patient_doc.last_name
    doc.uid = patient_doc.uid
    doc.sex = patient_doc.sex
    doc.dob = patient_doc.dob
    doc.mobile = patient_doc.mobile
    doc.aadhar_number = patient_doc.aadhar_number
    doc.from_date = from_date
    doc.to_date = to_date
    doc.generated_on = now()
    doc.patient_barcode=patient_doc.patient_barcode
    doc.html_content = get_invoice_table_html(patient, from_date, to_date, invoice_status)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name

def get_invoice_table_html(patient, from_date, to_date, invoice_status=None):
    conditions = "si.patient = %s AND si.posting_date BETWEEN %s AND %s"
    params = [patient, from_date, to_date]

    if invoice_status == "Paid":
        conditions += " AND si.status = 'Paid'"
    elif invoice_status == "Unpaid":
        conditions += " AND si.status IN ('Unpaid', 'Overdue')"
    else:
        conditions += " AND si.status IN ('Paid', 'Unpaid', 'Overdue')"

    invoices = frappe.db.sql(f"""
        SELECT si.name AS invoice, si.posting_date, sii.item_name, si.status, sii.amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE {conditions}
        ORDER BY si.posting_date ASC
    """, tuple(params), as_dict=True)

    rows = ""
    total = 0
    for idx, i in enumerate(invoices, start=1):
        total += i.amount
        rows += f"""
        <tr>
            <td>{idx}</td>
            <td>{i.posting_date}</td>
            <td>{i.invoice}</td>
            <td>{i.item_name}</td>
            <td>{frappe.utils.fmt_money(i.amount)}</td>
        </tr>
    """

    return f"""
    <style>
        .invoice-summary-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-family: 'Times New Roman', Times, serif;
            font-size: 14px;
        }}
        .invoice-summary-table th,
        .invoice-summary-table td {{
            border: 1px solid #000;
            padding: 6px 10px;
            text-align: left;
        }}
        .invoice-summary-table th {{
            background-color: #f9f9f9;
        }}
    </style>

    <table class="invoice-summary-table">
        <thead>
            <tr>
                <th>S.No</th>
                <th>Date</th>
                <th>Invoice</th>
                <th>Item</th>
                <th>Amount</th>
            </tr>
        </thead>
        <tbody>
            {rows}
            <tr>
                <td colspan="4"><strong>Grand Total</strong></td>
                <td><strong>{frappe.utils.fmt_money(total)}</strong></td>
            </tr>
        </tbody>
    </table>
"""




def execute(filters=None):
    columns = [
        {"label": "Sales Invoice", "fieldname": "invoice", "fieldtype": "Data", "width": 200, "allow_html": 1},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 130},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Item", "fieldname": "item", "fieldtype": "Data", "width": 180},
        {"label": "Item Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Total", "fieldname": "item_total", "fieldtype": "Currency", "width": 120},
        {"label": "Advance Payment", "fieldname": "advance_payment", "fieldtype": "Currency", "width": 160},
        {"label": "Advance Date", "fieldname": "advance_date", "fieldtype": "Date", "width": 130},
        {"label": "Payment ID", "fieldname": "payment_id", "fieldtype": "Data", "width": 200},
        {"label": "Complete Amount", "fieldname": "complete_amount", "fieldtype": "Currency", "width": 200},
    ]

    data = []
    if not filters.get("patient"):
        return columns, data

    patient = filters.get("patient")
    from_date = filters.get("from_date") or "1900-01-01"
    to_date = filters.get("to_date") or nowdate()
    invoice_status = filters.get("invoice_status")

    if invoice_status == "Paid":
        status_filter = ["Paid"]
        status_condition = "si.status IN %(status_filter)s"
    elif invoice_status == "Unpaid":
        status_filter = ["Unpaid", "Overdue"]
        status_condition = "si.status IN %(status_filter)s"
    elif invoice_status == "Others":
        status_filter = ["Paid", "Unpaid", "Overdue"]
        status_condition = "si.status NOT IN %(status_filter)s"
    else:
        status_filter = ["Paid", "Unpaid", "Overdue"]
        status_condition = "si.status IN %(status_filter)s"

    payment_refs = frappe.db.sql("""
        SELECT 
            pe.name AS payment_id,
            pe.posting_date AS advance_date,
            per.reference_name AS invoice,
            per.allocated_amount,
            pe.paid_amount
        FROM 
            `tabPayment Entry` pe
        LEFT JOIN 
            `tabPayment Entry Reference` per ON pe.name = per.parent
        WHERE 
            pe.party_type = 'Customer'
            AND pe.party = %(patient)s
            AND pe.docstatus = 1
            AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {
        "patient": patient,
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=1)

    invoice_advances_map = defaultdict(list)
    for row in payment_refs:
        if row.invoice:
            invoice_advances_map[row.invoice].append({
                "payment_id": row.payment_id,
                "advance_date": row.advance_date,
                "allocated_amount": flt(row.allocated_amount)
            })
        else:
            invoice_advances_map["__unallocated__"].append({
                "payment_id": row.payment_id,
                "advance_date": row.advance_date,
                "allocated_amount": flt(row.paid_amount)
            })

    invoices = frappe.db.sql(f"""
        SELECT 
            si.name, si.posting_date, sii.item_name, si.status, sii.amount
        FROM 
            `tabSales Invoice` si
        JOIN 
            `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE 
            si.patient = %(patient)s
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND {status_condition}
        ORDER BY 
            si.posting_date, si.name
    """, {
        "patient": patient,
        "from_date": from_date,
        "to_date": to_date,
        "status_filter": tuple(status_filter)
    }, as_dict=1)

    invoice_item_map = defaultdict(list)
    for inv in invoices:
        invoice_item_map[inv.name].append(inv)

    allocate_advances_map = frappe._dict({
        d.name: d.allocate_advances_automatically
        for d in frappe.db.get_all("Sales Invoice", filters={"name": ["in", list(invoice_item_map.keys())]}, fields=["name", "allocate_advances_automatically"])
    })

    net_total = 0
    advance_total = 0
    complete_total = 0

    for invoice_id, items in invoice_item_map.items():
        total_item_amount = sum([flt(i.amount) for i in items])
        net_total += total_item_amount
        payment_id = ""
        advance_date = ""

        if invoice_id in invoice_advances_map and invoice_advances_map[invoice_id]:
            adv = invoice_advances_map[invoice_id].pop(0)
            print("adv",adv)
        elif invoice_advances_map["__unallocated__"]:
            adv = invoice_advances_map["__unallocated__"].pop(0)
        else:
            adv = {}

        if not adv and not allocate_advances_map.get(invoice_id):
            advance_amt = None
        else:
            advance_amt = flt(adv.get("allocated_amount", 0))

        payment_id = adv.get("payment_id", "")
        advance_date = adv.get("advance_date", "")

        complete_amt = total_item_amount - flt(advance_amt or 0)
        advance_total += flt(advance_amt or 0)
        complete_total += complete_amt

        for idx, item in enumerate(items):
            data.append({
                "invoice": f"<b>{item.name}</b>" if idx == 0 else "",
                "date": item.posting_date if idx == 0 else "",
                "item": item.item_name,
                "amount": item.amount,
                "status": item.status if idx == 0 else "",
                "item_total": total_item_amount if idx == 0 else None,
                "advance_payment": advance_amt if idx == 0 else None,
                "advance_date": advance_date if idx == 0 and advance_amt else "",
                "payment_id": payment_id if idx == 0 and advance_amt else "",
                "complete_amount": complete_amt if idx == 0 else None
            })

    data.append({"invoice": "", "date": "", "status": "", "item": "", "amount": None, "item_total": None, "advance_payment": None, "advance_date": "", "payment_id": "", "complete_amount": None})
    data.append({
        "amount": None,
        "payment_id": "<b>Net Total</b>",
        "complete_amount": net_total,
        "advance_payment": None,
        "item_total": None,
        "status": ""
    })
    data.append({
        "payment_id": "<b>Advance Total</b>",
        "complete_amount": advance_total,
        "advance_payment": None,
        "amount": None,
        "item_total": None,
        "status": ""
    })
    data.append({
        "payment_id": "<b>Grand Total</b>",
        "complete_amount": net_total - advance_total,
        "advance_payment": None,
        "amount": None,
        "item_total": None,
        "status": ""
    })

    return columns, data
