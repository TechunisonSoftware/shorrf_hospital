// Copyright (c) 2016, ESS and contributors
// For license information, please see license.txt

cur_frm.cscript.custom_refresh = function (doc) {
	cur_frm.toggle_display('sb_sensitivity', doc.sensitivity_toggle);
	cur_frm.toggle_display('organisms_section', doc.descriptive_toggle);
	cur_frm.toggle_display('sb_descriptive', doc.descriptive_toggle);
	cur_frm.toggle_display('sb_normal', doc.normal_toggle);
	cur_frm.toggle_display('sb_descriptive_result', doc.imaging_toggle);
};

frappe.ui.form.on('Lab Test', {	
	validate: function (frm) {        
        if (frm.is_submitted && frm.doc.lab_status === "Acknowledged" && frm.doc.__unsaved) {          
            frappe.db.get_value('Lab Test', frm.doc.name, 'lab_status', (r) => {
                if (r.lab_status === "Completed") {
                    frappe.throw(__('Lab Status cannot be changed from Completed to Acknowledged after submission.'));
                }
            });
        }
		if (frm.doc.lab_test_name) {
			let routeOptions={}
			routeOptions = {
                lab_test_name: frm.doc.lab_test_name
            }
			frappe.route_options=routeOptions
			
			
		}
    },
	// setup: function (frm) {
	// 	frm.get_field('normal_test_items').grid.editable_fields = [
	// 		{ fieldname: 'lab_test_name', columns: 2 },
	// 		{ fieldname: 'lab_test_event', columns: 2 },
	// 		{ fieldname: 'result_value', columns: 1 },
	// 		{ fieldname: 'lab_test_uom', columns: 1 },
	// 		{ fieldname: 'normal_range', columns: 2 },
	// 		{ fieldname: 'text', columns: 1 },
	// 	];
	// 	frm.get_field('descriptive_test_items').grid.editable_fields = [
	// 		{ fieldname: 'lab_test_particulars', columns: 3 },
	// 		{ fieldname: 'result_value', columns: 7 }
	// 	];

	// 	frm.set_query('service_request', function() {
	// 		return {
	// 			filters: {
	// 				'patient': frm.doc.patient,
	// 				'status': 'Active',
	// 				'docstatus': 1,
	// 				'template_dt': 'Lab Test template'
	// 			}
	// 		};
	// 	});
	// },

	// lab_test_template: function(frm) {
	// 	console.log("lab_test_template~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");		
    //     frm.trigger("set_normal_test_items_visibility");
    // },

    // onload: function(frm) {
	// 	console.log("onload^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");		
    //     frm.trigger("set_normal_test_items_visibility");
    // },

    // set_normal_test_items_visibility: function(frm) {
	// 	console.log("set_normal_test_items_visibility*********************************************************");
    //     if (!frm.doc.template) return;

    //     frappe.db.get_doc("Lab Test Template", frm.doc.template)
    //         .then(doc => {
	// 			console.log("doc~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", doc);
				
    //             let data_type = doc.permitted_data_type;

    //             frm.fields_dict["normal_test_items"].grid.update_docfield_property("text", "hidden", data_type !== "Text");
    //             frm.fields_dict["normal_test_items"].grid.update_docfield_property("options", "hidden", data_type !== "Select");

    //             frm.fields_dict["normal_test_items"].grid.refresh();
    //         });
    // },

	

		// lab_test_template: function(frm) {
		// 	frm.trigger("update_normal_test_items_columns");
		// },
	
		// onload: function(frm) {
		// 	frm.trigger("update_normal_test_items_columns");
		// },
	
		// update_normal_test_items_columns: function(frm) {
		// 	if (!frm.doc.template) return;
	
		// 	frappe.db.get_doc("Lab Test Template", frm.doc.template).then(template => {
		// 		let data_type = template.permitted_data_type;
		// 		console.log("data type:", data_type);
	
		// 		let grid = frm.get_field("normal_test_items").grid;
	
		// 		// Always make sure the grid is initialized before using update_docfield_property
		// 		if (!grid || !grid.update_docfield_property) return;
	
		// 		let show_text = data_type === "Text";
		// 		let show_select = data_type === "Select";
	
		// 		// Update column visibility
		// 		// grid.update_docfield_property("text", "reqd", show_text);
		// 		grid.update_docfield_property("text", "hidden", !show_text);
	
		// 		// grid.update_docfield_property("options", "reqd", show_select);
		// 		grid.update_docfield_property("options", "hidden", !show_select);
		// 		grid.update_docfield_property("text", "in_list_view", show_text);
	
		// 		grid.update_docfield_property("options", "in_list_view", show_select);

		// 		// Optional: also update editable_columns layout
		// 		grid.editable_fields = [
		// 			{ fieldname: 'lab_test_name', columns: 2 },
		// 			// { fieldname: 'lab_test_event', columns: 2 },
		// 			{ fieldname: 'result_value', columns: 1 },
		// 			// { fieldname: 'lab_test_uom', columns: 1 },
		// 			{ fieldname: 'normal_range', columns: 1 },
		// 			{ fieldname: 'text', columns: show_text ? 2 : 0 },
		// 			{ fieldname: 'options', columns: show_select ? 2 : 0 }
		// 		];
				
		// 		grid.visible_columns = null;
		// 		grid.setup_visible_columns();
		// 		grid.refresh();
		// 		grid.grid_rows.forEach(row => row.refresh());
				
		// 		frm.refresh_field("normal_test_items");


		// 	});
		// },
		update_normal_test_items_columns: function(frm) {
			if (!frm.doc.template) return;
		
			frappe.db.get_doc("Lab Test Template", frm.doc.template).then(template => {
				let data_type = template.permitted_data_type;
				let grid = frm.get_field("normal_test_items").grid;
		
				if (!grid) return;
		
				// 1. Update column visibility (your existing logic)
				let show_text = data_type === "Text";
				let show_select = data_type === "Select";
				
				grid.update_docfield_property("text", "hidden", !show_text);
				grid.update_docfield_property("options", "hidden", !show_select);
				
				grid.update_docfield_property("text", "in_list_view", show_text);
	
				grid.update_docfield_property("options", "in_list_view", show_select);

				// Optional: also update editable_columns layout
				grid.editable_fields = [
					{ fieldname: 'lab_test_name', columns: 2 },
					// { fieldname: 'lab_test_event', columns: 2 },
					{ fieldname: 'result_value', columns: 1 },
					// { fieldname: 'lab_test_uom', columns: 1 },
					{ fieldname: 'normal_range', columns: 1 },
					{ fieldname: 'text', columns: show_text ? 2 : 0 },
					{ fieldname: 'options', columns: show_select ? 2 : 0 }
				];
				
				grid.visible_columns = null;

				// 2. FORCE ROW HEIGHT (Key Fix!)
				setTimeout(() => { // Small delay to ensure DOM loads
					// Set minimum row height for ALL rows
					let rows = grid.grid_rows;
					if (rows) {
						rows.forEach(row => {
							row.$wrapper.style.minHeight = "42px"; // Adjust height as needed
							row.$wrapper.style.alignItems = "center"; // Keeps content centered vertically
						});
					}
					
					// Refresh the grid to apply changes
					grid.refresh();
					frm.refresh_field("normal_test_items");
				}, 100);
			});
		},
	

	refresh: function (frm) {
		if (frm.doc.docstatus === 0 && frm.doc.lab_status) {
            let status_map = {
                "Completed": "green",
                "Acknowledge": "blue",
                "Result Entry": "yellow",
            };

            let color = status_map[frm.doc.lab_status] || "gray";             
            frm.page.set_indicator(frm.doc.lab_status, color);
			
        }

		refresh_field('normal_test_items');
		refresh_field('descriptive_test_items');
		if (frm.doc.__islocal) {
			frm.add_custom_button(__('Get from Patient Encounter'), function () {
				get_lab_test_prescribed(frm);
			});
		}

		frm.set_query("code_value", "codification_table", function(doc, cdt, cdn) {
			let row = frappe.get_doc(cdt, cdn);
			if (row.code_system) {
				return {
					filters: {
						code_system: row.code_system
					}
				};
			}
		});

		if (frappe.defaults.get_default('lab_test_approval_required') && frappe.user.has_role('LabTest Approver')) {
			if (frm.doc.docstatus === 1 && frm.doc.status !== 'Approved' && frm.doc.status !== 'Rejected') {
				frm.add_custom_button(__('Approve'), function () {
					status_update(1, frm);
				}, __('Actions'));
				frm.add_custom_button(__('Reject'), function () {
					status_update(0, frm);
				}, __('Actions'));
			}
		}

		if (frm.doc.docstatus === 1 && frm.doc.sms_sent === 0 && frm.doc.status !== 'Rejected' ) {
			frm.add_custom_button(__('Send SMS'), function () {
				frappe.call({
					method: 'healthcare.healthcare.doctype.healthcare_settings.healthcare_settings.get_sms_text',
					args: { doc: frm.doc.name },
					callback: function (r) {
						if (!r.exc) {
							var emailed = r.message.emailed;
							var printed = r.message.printed;
							make_dialog(frm, emailed, printed);
						}
					}
				});
			});
		}
	},

	template: function(frm) {
		if (frm.doc.template) {
			frappe.call({
				"method": "healthcare.healthcare.utils.get_medical_codes",
				args: {
					template_dt: "Lab Test Template",
					template_dn: frm.doc.template,
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.doc.codification_table = []
						$.each(r.message, function(k, val) {
							if (val.code_value) {
								var child = cur_frm.add_child("codification_table");
								child.code_value = val.code_value
								child.code_system = val.code_system
								child.code = val.code
								child.description = val.description
								child.system = val.system
							}
						});
						frm.refresh_field("codification_table");
					} else {
						frm.clear_table("codification_table")
						frm.refresh_field("codification_table");
					}
				}
			})
		} else {
			frm.clear_table("codification_table")
			frm.refresh_field("codification_table");
		}
	}
});


frappe.ui.form.on('Lab Test', 'patient', function (frm) {
	if (frm.doc.patient) {
		frappe.call({
			'method': 'healthcare.healthcare.doctype.patient.patient.get_patient_detail',
			args: { patient: frm.doc.patient },
			callback: function (data) {
				var age = null;
				if (data.message.dob) {
					age = calculate_age(data.message.dob);
				}
				let values = {
					'patient_age': age,
					'patient_sex': data.message.sex,
					'email': data.message.email,
					'mobile': data.message.mobile,
					'report_preference': data.message.report_preference
				};
				frm.set_value(values);
			}
		});
	}
});

frappe.ui.form.on('Normal Test Result', {
	normal_test_items_remove: function () {
		frappe.msgprint(__('Not permitted, configure Lab Test Template as required'));
		cur_frm.reload_doc();
	}
});

frappe.ui.form.on('Descriptive Test Result', {
	descriptive_test_items_remove: function () {
		frappe.msgprint(__('Not permitted, configure Lab Test Template as required'));
		cur_frm.reload_doc();
	}
});

var status_update = function (approve, frm) {
	var doc = frm.doc;
	var status = null;
	if (approve == 1) {
		status = 'Approved';
	}
	else {
		status = 'Rejected';
	}
	frappe.call({
		method: 'healthcare.healthcare.doctype.lab_test.lab_test.update_status',
		args: { status: status, name: doc.name },
		callback: function () {
			cur_frm.reload_doc();
		}
	});
};

var get_lab_test_prescribed = function (frm) {
	if (frm.doc.patient) {
		frappe.call({
			method: 'healthcare.healthcare.doctype.lab_test.lab_test.get_lab_test_prescribed',
			args: { patient: frm.doc.patient },
			callback: function (r) {
				show_lab_tests(frm, r.message);
			}
		});
	}
	else {
		frappe.msgprint(__('Please select Patient to get Lab Tests'));
	}
};

var show_lab_tests = function (frm, lab_test_list) {
	var d = new frappe.ui.Dialog({
		title: __('Lab Tests'),
		fields: [{
			fieldtype: 'HTML', fieldname: 'lab_test'
		}]
	});
	var html_field = d.fields_dict.lab_test.$wrapper;
	html_field.empty();
	$.each(lab_test_list, function (x, y) {
		var row = $(repl(
			'<div class="col-xs-12 row" style="padding-top:12px;">\
			<div class="col-xs-3"> %(lab_test)s </div>\
			<div class="col-xs-4">%(encounter)s</div>\
			<div class="col-xs-3"> %(date)s </div>\
			<div class="col-xs-1">\
				<a data-name="%(name)s" data-lab-test="%(lab_test)s"\
				data-encounter="%(encounter)s" data-practitioner="%(practitioner)s" \
				data-invoiced="%(invoiced)s" data-source="%(source)s"\
				data-referring-practitioner="%(referring_practitioner)s" href="#"><button class="btn btn-default btn-xs">Get</button></a>\
			</div>\
		</div><hr>',
		{ lab_test: y[0], encounter: y[1], invoiced: y[2], practitioner: y[3], date: y[4],
			name: y[5]})
		).appendTo(html_field);
		row.find("a").click(function () {
			frm.doc.template = $(this).attr('data-lab-test');
			frm.doc.service_request = $(this).attr('data-name');
			frm.doc.practitioner = $(this).attr('data-practitioner');
			frm.set_df_property('template', 'read_only', 1);
			frm.set_df_property('patient', 'read_only', 1);
			frm.set_df_property('practitioner', 'read_only', 1);
			frm.doc.invoiced = 0;
			if ($(this).attr('data-invoiced') === "Invoiced") {
				frm.doc.invoiced = 1;
			}
			refresh_field('invoiced');
			refresh_field('template');
			frm.refresh_field('service_request');
			d.hide();
			return false;
		});
	});
	if (!lab_test_list.length) {
		var msg = __('No Lab Tests found for the Patient {0}', [frm.doc.patient_name.bold()]);
		html_field.empty();
		$(repl('<div class="col-xs-12" style="padding-top:0px;" >%(msg)s</div>', { msg: msg })).appendTo(html_field);
	}
	d.show();
};

var make_dialog = function (frm, emailed, printed) {
	var number = frm.doc.mobile;

	var dialog = new frappe.ui.Dialog({
		title: 'Send SMS',
		width: 400,
		fields: [
			{ fieldname: 'result_format', fieldtype: 'Select', label: 'Result Format', options: ['Emailed', 'Printed'] },
			{ fieldname: 'number', fieldtype: 'Data', label: 'Mobile Number', reqd: 1 },
			{ fieldname: 'message', fieldtype: 'Small Text', label: 'Message', reqd: 1 }
		],
		primary_action_label: __('Send'),
		primary_action: function () {
			var values = dialog.fields_dict;
			if (!values) {
				return;
			}
			send_sms(values, frm);
			dialog.hide();
		}
	});
	if (frm.doc.report_preference === 'Print') {
		dialog.set_values({
			'result_format': 'Printed',
			'number': number,
			'message': printed
		});
	} else {
		dialog.set_values({
			'result_format': 'Emailed',
			'number': number,
			'message': emailed
		});
	}
	var fd = dialog.fields_dict;
	$(fd.result_format.input).change(function () {
		if (dialog.get_value('result_format') === 'Emailed') {
			dialog.set_values({
				'number': number,
				'message': emailed
			});
		} else {
			dialog.set_values({
				'number': number,
				'message': printed
			});
		}
	});
	dialog.show();
};

var send_sms = function (vals, frm) {
	var number = vals.number.value;
	var message = vals.message.last_value;

	if (!number || !message) {
		frappe.throw(__('Did not send SMS, missing patient mobile number or message content.'));
	}
	frappe.call({
		method: 'frappe.core.doctype.sms_settings.sms_settings.send_sms',
		args: {
			receiver_list: [number],
			msg: message
		},
		callback: function (r) {
			if (r.exc) {
				frappe.msgprint(r.exc);
			} else {
				frm.reload_doc();
			}
		}
	});
};

var calculate_age = function (dob) {
	var ageMS = Date.parse(Date()) - Date.parse(dob);
	var age = new Date();
	age.setTime(ageMS);
	var years = age.getFullYear() - 1970;
	return `${years} ${__('Years(s)')} ${age.getMonth()} ${__('Month(s)')} ${age.getDate()} ${__('Day(s)')}`;
};


frappe.ui.form.on("Normal Test Result", {
    normal_test_items_add: function(frm) {
        frm.trigger("set_normal_test_items_visibility");
    }
});
