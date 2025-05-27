// Copyright (c) 2025, earthians Health Informatics Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Patient Profiling", {
	height: function(frm) {      
        
		if (frm.doc.height && frm.doc.weight) {
			calculate_bmi(frm);
		}
	},

	weight: function(frm) {
        console.log(frm.doc.weight);
        
		if (frm.doc.height && frm.doc.weight) {
			calculate_bmi(frm);
		}
	},
    health_insurance_coverage:function(frm){   
        if(frm.doc.health_insurance_coverage && frm.doc.health_insurance_coverage == "Others"){          
            frm.set_df_property("health_insurance_coverage_others", "hidden", 0); 
        }else{
            frm.set_df_property("health_insurance_coverage_others", "hidden", 1); 
        }
    },

    previous_illness_episode:function(frm){
        if(frm.doc.previous_illness_episode && frm.doc.previous_illness_episode == "Did not go for any treatment"){          
            frm.set_df_property("reason_for_not_seeking_treatment", "hidden", 0);
        }else{
            frm.set_df_property("reason_for_not_seeking_treatment", "hidden", 1); 
        }

    },
    occupation:function(frm){
          if(frm.doc.occupation && frm.doc.occupation == "Others"){
                frm.set_df_property("occupation_others", "hidden", 0);
          }else{
                frm.set_df_property("occupation_others", "hidden", 1);
          }
    },

    reason_for_not_seeking_treatment:function(frm){  
                       
           let selected_value = frm.doc.reason_for_not_seeking_treatment || []
          
           let show_field = false;

   
            (selected_value).forEach(row => {       
                
                if (row.reason === 'Others') {
                    show_field = true;
                }
            });

    
    frm.set_df_property('reason_for_not_seeking_treatment_others', 'hidden', !show_field);

    if (!show_field) {
        frm.set_value('reason_for_not_seeking_treatment_others', '');
    }
           
 
    },
    main_problem_faced_by_previous_healthcare_provider:function(frm){
        if(frm.doc.main_problem_faced_by_previous_healthcare_provider && frm.doc.main_problem_faced_by_previous_healthcare_provider == "Others"){          
            frm.set_df_property("main_problem_faced_by_previous_healthcare_provider_others", "hidden", 0); 
        }else{
            frm.set_df_property("main_problem_faced_by_previous_healthcare_provider_others", "hidden", 1); 
        }
    },
    patient:function(frm){
        if(frm.doc.patient){          
            frappe.call({
                method: "healthcare.healthcare.doctype.patient_profiling.patient_profiling.get_address_for_patient",
                args: {
                    patient: frm.doc.patient
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        const address = r.message[0];                                             
                        frm.set_value("state", address.state || "");
                        frm.set_df_property("state", "read_only", 1);                        
                        frm.set_value("district", address.county || "");
                        frm.set_df_property("district", "read_only", 1);                        
                        frm.set_value("pincode", address.pincode || "");
                        frm.set_df_property("pincode", "read_only", 1);
                        
                       
                    } else {
                     
                        frm.set_df_property("state", "read_only", 0); 
                        frm.set_df_property("district", "read_only", 0);
                        frm.set_df_property("pincode", "read_only", 0);
                    }
                }
            });
        
        }else{
            frm.set_df_property("state", "read_only", 0); 
            frm.set_df_property("pincode", "read_only", 0);
            frm.set_df_property("district", "read_only", 0);
            frm.set_value("state", "");           
            frm.set_value("district", "");
            frm.set_value("pincode", ""); 
        }
    }


});

let calculate_bmi = function(frm) {	
    
   
    let height_in_meters = frm.doc.height / 100;
    
    let bmi = (frm.doc.weight / (height_in_meters * height_in_meters)).toFixed(2);	
    console.log(bmi);
    
    frappe.model.set_value(frm.doctype, frm.docname, 'bmi', bmi);	
};
