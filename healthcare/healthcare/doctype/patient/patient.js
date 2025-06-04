// Copyright (c) 2016, ESS LLP and contributors
// For license information, please see license.txt
{% include 'healthcare/regional/india/abdm/js/patient.js' %}

frappe.ui.form.on('Patient', {
	validate: function (frm) {
       
		if (!frm.doc.not_having_aadhar && frm.doc.aadhar_number) {
            let cleaned = frm.doc.aadhar_number.replace(/\D/g, '');           
            if (!/^\d{12}$/.test(cleaned)) {
                frm.set_value('aadhar_number', '');
                frappe.throw(__('Please enter a valid 12-digit Aadhar number.'));
            }  
			// console.log(cleaned);
			        
            let formatted = cleaned.replace(/(\d{4})(\d{4})(\d{4})/, '$1-$2-$3');
            frm.set_value('aadhar_number', formatted);
        }

       
        let today = frappe.datetime.get_today();
        if (frm.doc.dob && frm.doc.dob > today) {
            frm.set_value('dob', '');  
            frappe.throw(__('Please enter a valid Date of Birth.'));  
        }
    },
	refresh: function (frm) {
		frm.set_query('patient', 'patient_relation', function () {
			return {
				filters: [
					['Patient', 'name', '!=', frm.doc.name]
				]
			};
		});
		frm.set_query('customer_group', {'is_group': 0});
		frm.set_query('default_price_list', { 'selling': 1});

		if (frappe.defaults.get_default('patient_name_by') != 'Naming Series') {
			frm.toggle_display('naming_series', false);
		} else {
			erpnext.toggle_naming_series();
		}

		if (frappe.defaults.get_default('collect_registration_fee') && frm.doc.status == 'Disabled') {
			frm.add_custom_button(__('Invoice Patient Registration'), function () {
				invoice_registration(frm);
			});
		}

		if (frm.doc.patient_name && frappe.user.has_role('Physician')) {
			frm.add_custom_button(__('Patient Progress'), function() {
				frappe.route_options = {'patient': frm.doc.name};
				frappe.set_route('patient-progress');
			}, __('View'));

			frm.add_custom_button(__('Patient History'), function() {
				frappe.route_options = {'patient': frm.doc.name};
				frappe.set_route('patient_history');
			}, __('View'));
		}

		frappe.dynamic_link = {doc: frm.doc, fieldname: 'name', doctype: 'Patient'};
		frm.toggle_display(['address_html', 'contact_html'], !frm.is_new());

		if (!frm.is_new()) {
			if ((frappe.user.has_role('Nursing User') || frappe.user.has_role('Physician'))) {
				frm.add_custom_button(__('Medical Record'), function () {
					create_medical_record(frm);
				}, __('Create'));
				frm.toggle_enable(['customer'], 0);
			}
			frappe.contacts.render_address_and_contact(frm);
			erpnext.utils.set_party_dashboard_indicators(frm);
		} else {
			frappe.contacts.clear_address_and_contact(frm);
		}
		hiding_barcode(frm)

		if (!frm.custom_buttons["Toggle Voice Recording"]) {
			frm.add_custom_button(__("Enable Voice Recording"), function () {
			  toggleVoiceRecording(frm);
			})
			  .addClass("btn-info")
			  .attr("id", "voice-record-toggle");
	
			$("#voice-record-toggle")
			  .text("Enable Voice Recording")
			  .css({ 'background-color': 'green', 'color': 'white', 'font-weight': 'bold' });
	
			frm.voice_recording_enabled = false;
			showVoiceIcons(frm, false);
		  }
	console.log("button added and voice recording enabled is ",frm.voice_recording_enabled);
		  const fields = [
			'medical_history',
			'surgical_history',
			'medication',
			'allergies'
		  ];
	
		  toggleVoiceRecording(frm, frm.voice_recording_enabled);
	
		  fields.forEach((field_name) => {
			const field_wrapper = frm.fields_dict[field_name].$wrapper;
			const field_label = field_wrapper.find(".control-label");
	
			if (!field_label.find(".voice-icon").length) {
			  const icon_html = `
						<span class="voice-icon" style="margin-left: 8px; cursor: pointer; color: red;">
							<i class="fa fa-microphone"></i>
						</span>`;
			  field_label.append(icon_html);
			}
	
			const field = frm.fields_dict[field_name].input;
			$(field).on("focus", function () {
			  if (frm.voice_recording_enabled) {
				startVoiceRecording(frm, field_name);
			  }
			});
			$(field).on("blur", function () {
			  if (frm.voice_recording_enabled) {
				stopVoiceRecording(frm);
			  }
			});
		  });
	},

	onload: function (frm) {
		healthcare.utils.set_company_if_local(frm);
		if (frm.doc.dob) {
			$(frm.fields_dict['age_html'].wrapper).html(`${__('AGE')} : ${get_age(frm.doc.dob)}`);
			frm.set_value('patient_age',get_age(frm.doc.dob))
			
		} else {
			$(frm.fields_dict['age_html'].wrapper).html('');
			frm.set_value('patient_age','')
			
		}
		hiding_barcode(frm)

	},
	before_save(frm){		
		get_uid(frm);
	},
	after_save: function(frm) {
		hiding_barcode(frm)    
      
    },
	not_having_aadhar:function(frm){   
		  console.log("Not having aadhar clicked");
		//   console.log(frm.doc.aadhar_number); 
		  
		  let is_required = !frm.doc.not_having_aadhar; 
		//   console.log(is_required);
		  
		  frm.set_df_property('aadhar_number', 'reqd', is_required);
			frm.refresh_field('aadhar_number');

			// If the field is not required, clear its value to avoid validation errors
			if (!is_required) {
				frm.set_value('aadhar_number', '');
			}
		  
	}
	

});



frappe.ui.form.on('Patient', 'dob', function(frm) {
	if (frm.doc.dob) {
		let today = new Date();
		let birthDate = new Date(frm.doc.dob);
		if (today < birthDate) {
			frappe.msgprint(__('Please select a valid Date'));
			frappe.model.set_value(frm.doctype,frm.docname, 'dob', '');
		} else {
			let age_str = get_age(frm.doc.dob);
			$(frm.fields_dict['age_html'].wrapper).html(`${__('AGE')} : ${age_str}`);
			frm.set_value('patient_age',age_str)
		}
	} else {
		$(frm.fields_dict['age_html'].wrapper).html('');
		frm.set_value('patient_age','')
	}
});


frappe.ui.form.on('Patient Relation', {
	patient_relation_add: function(frm){
		frm.fields_dict['patient_relation'].grid.get_field('patient').get_query = function(doc){
			let patient_list = [];
			if(!doc.__islocal) patient_list.push(doc.name);
			$.each(doc.patient_relation, function(idx, val){
				if (val.patient) patient_list.push(val.patient);
			});
			return { filters: [['Patient', 'name', 'not in', patient_list]] };
		};
	}
});

let create_medical_record = function (frm) {
	frappe.route_options = {
		'patient': frm.doc.name,
		'status': 'Open',
		'reference_doctype': 'Patient Medical Record',
		'reference_owner': frm.doc.owner
	};
	frappe.new_doc('Patient Medical Record');
};

function get_age(birth) {
    const birthDate = moment(birth).startOf('day');
    const today = moment().startOf('day');
 
    let years = today.diff(birthDate, 'years');
    let tempDate = birthDate.clone().add(years, 'years');
 
    let months = today.diff(tempDate, 'months');
    tempDate.add(months, 'months');
 
    let days = today.diff(tempDate, 'days');
 
    return `${years} ${__('Year(s)')} ${months} ${__('Month(s)')} ${days} ${__('Day(s)')}`;
}

let create_vital_signs = function (frm) {
	if (!frm.doc.name) {
		frappe.throw(__('Please save the patient first'));
	}
	frappe.route_options = {
		'patient': frm.doc.name,
	};
	frappe.new_doc('Vital Signs');
};

let create_encounter = function (frm) {
	if (!frm.doc.name) {
		frappe.throw(__('Please save the patient first'));
	}
	frappe.route_options = {
		'patient': frm.doc.name,
	};
	frappe.new_doc('Patient Encounter');
};

let invoice_registration = function (frm) {
	frappe.call({
		doc: frm.doc,
		method: 'invoice_patient_registration',
		callback: function(data) {
			if (!data.exc) {
				if (data.message.invoice) {
					frappe.set_route('Form', 'Sales Invoice', data.message.invoice);
				}
				cur_frm.reload_doc();
			}
		}
	});
};


function get_uid(frm){
	// console.log(frm.doc.service_unit);
	
	if(frm.is_new() && !frm.doc.uid && frm.doc.company){
        // frm.add_custom_button('Generate Barcode', () => {
            frappe.call({
                method: "healthcare.healthcare.doctype.patient.patient.generate_uid",
				args:{"company":frm.doc.company},
                callback: function(response) {
                    if (response.message) {
                        frm.set_value("uid", response.message);
                        frm.set_value("patient_barcode", frm.doc.uid);
						frm.refresh_field("uid");                        
                        frm.refresh_field("patient_barcode");																
						// frm.save();
						frm.set_df_property('patient_barcode', 'read_only', 1);	
                    }
                }
                
            });
        // });
    }

}

function hiding_barcode(frm){
	// console.log("calling hdidng barcode");	
	if (!frm.is_new() && frm.doc.patient_barcode) {		
		frm.set_df_property("patient_barcode", "hidden", true);
		frm.set_df_property("barcode_tab", "hidden", true);
	}
}




let recognition;
let recording = false;
function startVoiceRecording(frm, field_name) {
  let SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = "en";
  recognition.interimResults = true;
  recognition.start();

  recognition.onresult = function (event) {
    const speechResult = event.results[0][0].transcript;
    const currentValue = frm.fields_dict[field_name].get_value() || "";
    if (event.results[0].isFinal) {
      const updatedValue = currentValue + " " + speechResult;
      updateFieldValue(frm, field_name, updatedValue.trim());
    }
  };

  recognition.onspeechend = () => {
    startVoiceRecording(frm, field_name);
  };
}

function stopVoiceRecording(frm) {
  if (recognition) {
    recognition.stop();
    recognition = null;
  }
}

function updateFieldValue(frm, field_name, value) {
  frm.set_value(field_name, value);
}
function toggleVoiceRecording(frm, enable = null) {
  if (enable === null) {
    enable = !frm.voice_recording_enabled;
  }
  frm.voice_recording_enabled = enable;

  const button = $("#voice-record-toggle");

  if (enable) {
    button.text("Disable Voice Recording").css({ 'background-color': 'red', 'color': 'white', 'font-weight': 'bold' });
    showVoiceIcons(frm, true);
  } else {
    button.text("Enable Voice Recording").css({ 'background-color': 'green', 'color': 'white', 'font-weight': 'bold' });
    showVoiceIcons(frm, false);
  }
}

function showVoiceIcons(frm, show) {
  const fields = [
    'medical_history',
	'surgical_history',
	'medication',
	'allergies'
  ];

  fields.forEach((field_name) => {
    const field_wrapper = frm.fields_dict[field_name].$wrapper;
    const icon = field_wrapper.find(".voice-icon");
    if (show) {
      icon.show();
    } else {
      icon.hide();
    }
  });
}