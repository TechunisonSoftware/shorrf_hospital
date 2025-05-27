/*
(c) ESS 2015-16
*/
frappe.listview_settings['Lab Test'] = {
	add_fields: ['document_status'],
	hide_name_column:false,
	get_indicator: function (doc) {	
		if (doc.lab_status==="Draft") {
			console.log("DRAFT");
			
            return [__("Draft"), "red", "status,=,Draft"];
        }else if (doc.lab_status === "Collection") {
			console.log("COLLECTION");
			
            return [__("Collection"), "blue", "lab_status,=,Collection"];
        }else if (doc.lab_status === "Acknowledge") {
			console.log("ACK");
			
            return [__("Acknowledge"), "yellow", "lab_status,=,Acknowledge"];
		}else if (doc.lab_status === 'Result Entry') {
			return [__('Result Entry'), 'purple', 'lab_status,=,Result Entry'];
		}else if (doc.lab_status === 'Approved') {
			return [__('Approved'), 'yellow', 'lab_status,=,Approved'];
		} else if (doc.lab_status === 'Rejected') {
			return [__('Rejected'), 'red', 'lab_status,=,Rejected'];
		} else if (doc.lab_status === 'Completed') {
			return [__('Completed'), 'green', 'lab_status,=,Completed'];
		} else if (doc.lab_status === 'Cancelled') {
			return [__('Cancelled'), 'yellow', 'lab_status,=,Cancelled'];
		}
	},
	onload: function (listview,doc) {
		console.log("ONLOAD",doc);
		
		listview.page.add_menu_item(__('Create Multiple'), function () {
			create_multiple_dialog(listview);
		});
	}
};

var create_multiple_dialog = function (listview) {
	var dialog = new frappe.ui.Dialog({
		title: 'Create Multiple Lab Tests',
		width: 100,
		fields: [
			{ fieldtype: 'Link', label: 'Patient', fieldname: 'patient', options: 'Patient', reqd: 1 },
			{
				fieldtype: 'Select', label: 'Invoice / Patient Encounter', fieldname: 'doctype',
				options: '\nSales Invoice\nPatient Encounter', reqd: 1
			},
			{
				fieldtype: 'Dynamic Link', fieldname: 'docname', options: 'doctype', reqd: 1,
				get_query: function () {
					return {
						filters: {
							'patient': dialog.get_value('patient'),
							'docstatus': 1
						}
					};
				}
			}
		],
		primary_action_label: __('Create'),
		primary_action: function () {
			frappe.call({
				method: 'healthcare.healthcare.doctype.lab_test.lab_test.create_multiple',
				args: {
					'doctype': dialog.get_value('doctype'),
					'docname': dialog.get_value('docname')
				},
				callback: function (data) {
					if (!data.exc) {
						if (!data.message) {
							frappe.msgprint(__('No Lab Tests created'));
						}
						listview.refresh();
					}
				},
				freeze: true,
				freeze_message: __('Creating Lab Tests...')
			});
			dialog.hide();
		}
	});

	dialog.show();
};