// Copyright (c) 2025, earthians Health Informatics Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Radiology Result Entry", {
	refresh(frm) {
        frm.add_custom_button(__('View DICOM'),function(){		
            // console.log(frm.doc.uid);
                    
            if(frm.doc.patient){
                frappe.db.get_single_value('Radiology Setting', 'orthanc_url').then(orthanc_url => {	
                    // console.log(orthanc_url);
                                                            
                    if(orthanc_url){
                        window.open(`${orthanc_url}/ui/app/#/filtered-studies?PatientID=${frm.doc.patient_uid}&order-by=LastUpdate,DESC`)
                    }else{
                        frappe.msgprint({
                            title: __('Error'),
                            indicator: 'red',
                            message: __('Please configure the requesting URL on radiology setting.')
                        });
                    }						
                });					
                
            }
        })

	},
});
