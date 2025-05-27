// Copyright (c) 2025, earthians Health Informatics Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Schedule Procedures", {
	refresh(frm) {   
            frm.set_query('radiology', function() {
                return {
                    filters: {
                        observation_category: 'Imaging'  
                    }
                };
            });
        

	},
});
