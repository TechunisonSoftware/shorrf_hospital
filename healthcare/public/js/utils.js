frappe.provide('healthcare.utils');

healthcare.utils.set_company_if_local = function(frm) {
    if (!frm.doc.__islocal) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Employee',
            filters: {
                user_id: frappe.session.user
            },
            fieldname: 'company'
        },
        callback: function(r) {
            if (r.message && !frm.doc.company) {
                frm.set_value('company', r.message.company);
            }
        }
    });
};


