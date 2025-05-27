// Copyright (c) 2025, earthians Health Informatics Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("One Million Scan", {
	// refresh(frm) {

	// },
    height: function(frm) {      
        
		if (frm.doc.height && frm.doc.weight) {
			calculate_bmi(frm);
		}
	},

	weight: function(frm) {
		if (frm.doc.height && frm.doc.weight) {
			calculate_bmi(frm);
		}
	},
	has_reached_menopause:function(frm){
		if (frm.doc.has_reached_menopause === "Yes") {
            frm.set_df_property("if_yes_at_what_age", "hidden", 0); 
        } 
        else {
            frm.set_df_property("if_yes_at_what_age", "hidden", 1); 
        }

	},
	has_insurance:function(frm){
		if(frm.doc.has_insurance){
			 
			frm.set_df_property("type", "hidden", 0); 
		}else{
			
			frm.set_df_property("type", "hidden", 1); 
		}
	},
	others:function(frm){
       if(frm.doc.others){
		frm.set_df_property("others_notes", "hidden", 0); 
	   }else{
		frm.set_df_property("others_notes", "hidden", 1); 
	   }
	}

});

let calculate_bmi = function(frm){	
	let bmi = (frm.doc.weight / (frm.doc.height * frm.doc.height)).toFixed(2);	
	frappe.model.set_value(frm.doctype,frm.docname, 'bmi', bmi);	
};
