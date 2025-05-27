// Copyright (c) 2025, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Schedule', {
    before_save: function(frm) {

        const job_type = frm.doc.job_type; // Field in Schedule doctype
        const frequency = frm.doc.frequency; // Field in Schedule doctype
        const method = frm.doc.method; // Field in Schedule doctype
        // Create a new entry in the Scheduled Job Type doctype
        frappe.call({            
            method: 'frappe.client.insert',            
            args: {
                doc: {
                    doctype: 'Scheduled Job Type',
                    job_type: job_type, // Use the Schedule name as the job type
                    frequency: frequency, // Set the frequency (you can customize this)
                    method: method, // Specify the method to execute
                    enabled: 1 // Enable the job
                }
            },
            
            
            callback: function(r) {
                console.log("JOB TYPE", job_type);
                console.log("FREQUENCY", frequency);
                console.log("METHOD", method);
                
                
                
                if (r.message) {
                    frappe.msgprint(__('Scheduled Job Type created successfully'));
                }
            }
        });
    }
});