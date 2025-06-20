frappe.query_reports["Patient Invoice Details"] = {
  filters: [
    {
      fieldname: "patient",
      label: "Patient",
      fieldtype: "Link",
      options: "Patient",
      reqd: 1,
      on_change: function () {
        const patient = frappe.query_report.get_filter_value("patient");
        if (!patient) return;

        frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Inpatient Record",
            filters: {
              patient: patient,
              status: ["in", ["Admitted", "Discharge Scheduled"]]
            },
            fields: ["scheduled_date"],
            order_by: "creation desc",
            limit: 1
          },
          callback: function (r) {
            if (r.message && r.message.length) {
              const scheduled_date = r.message[0].scheduled_date;
              frappe.query_report.set_filter_value("from_date", scheduled_date);
              frappe.query_report.set_filter_value("to_date", frappe.datetime.get_today());
            } else {
              frappe.query_report.set_filter_value("from_date", "");
              frappe.query_report.set_filter_value("to_date", frappe.datetime.get_today());
              frappe.msgprint("No active Inpatient Record found. Please select dates manually.");
            }
          }
        });
      }
    },
    {
      fieldname: "from_date",
      label: "From Date",
      fieldtype: "Date"
    },
    {
      fieldname: "to_date",
      label: "To Date",
      fieldtype: "Date",
      default: frappe.datetime.get_today()
    },
    {
      fieldname: "invoice_status",
      label: "Invoice Status",
      fieldtype: "Select",
      options: "\nPaid\nUnpaid",
      default: ""
    }
  ],
onload: function (report) {
  report.page.add_inner_button("Print Report", () => {
    const filters = report.get_filter_values();
    if (!filters.patient || !filters.from_date || !filters.to_date) {
      frappe.msgprint("Please select Patient, From Date, and To Date.");
      return;
    }

    frappe.call({
      method: "healthcare.healthcare.report.patient_invoice_details.patient_invoice_details.create_patient_invoice_summary",
      args: {
        patient: filters.patient,
        from_date: filters.from_date,
        to_date: filters.to_date,
        invoice_status: filters.invoice_status || null
      },
      callback: function (r) {
        if (r.message) {
          frappe.set_route("print", "Patient Sales Invoice Report", r.message);
        }
      }
    });
  });
}


};
