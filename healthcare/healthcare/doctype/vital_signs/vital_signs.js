// Copyright (c) 2016, ESS LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vital Signs', {
	onload: function(frm) {
		healthcare.utils.set_company_if_local(frm);
		frm.fields_dict.patient.get_query = function() {
            if (frm.doc.company) {
                return {
                    filters: {
                        company: frm.doc.company
                    }
                };
            }
        };
	},

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

	bp_systolic: function(frm) {
		if (frm.doc.bp_systolic && frm.doc.bp_diastolic) {
			set_bp(frm);
		}
	},

	bp_diastolic: function(frm) {
		if (frm.doc.bp_systolic && frm.doc.bp_diastolic) {
			set_bp(frm);
		}
	}
});

let calculate_bmi = function(frm){
	// Reference https://en.wikipedia.org/wiki/Body_mass_index
	// bmi = weight (in Kg) / height * height (in Meter)
	let bmi = (frm.doc.weight / (frm.doc.height * frm.doc.height)).toFixed(2);
	let bmi_note = null;

	if (bmi<18.5) {
		bmi_note = __('Underweight');
	} else if (bmi>=18.5 && bmi<25) {
		bmi_note = __('Normal');
	} else if (bmi>=25 && bmi<30) {
		bmi_note = __('Overweight');
	} else if (bmi>=30) {
		bmi_note = __('Obese');
	}
	frappe.model.set_value(frm.doctype,frm.docname, 'bmi', bmi);
	frappe.model.set_value(frm.doctype,frm.docname, 'nutrition_note', bmi_note);
};

let set_bp = function(frm){
	let bp = frm.doc.bp_systolic+ '/' + frm.doc.bp_diastolic + ' mmHg';
	frappe.model.set_value(frm.doctype,frm.docname, 'bp', bp);
};
