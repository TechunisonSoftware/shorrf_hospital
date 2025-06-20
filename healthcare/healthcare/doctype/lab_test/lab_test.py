# -*- coding: utf-8 -*-
# Copyright (c) 2015, ESS and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form, getdate, now_datetime

from healthcare.healthcare.doctype.nursing_task.nursing_task import NursingTask


class LabTest(Document):
    def validate(self):
        # Check if the document is being saved for the first time
        if not self.get("lab_status") or self.lab_status == "Draft":
            self.lab_status = "Collection"

        if not self.is_new():
            self.set_secondary_uom_result()

    def before_save(self):
        # Clear the employee field before save
        self.employee = None  # or self.employee = ""

    def on_submit(self):
        from healthcare.healthcare.utils import validate_nursing_tasks

        validate_nursing_tasks(self)
        self.validate_result_values()
        self.db_set("submitted_date", getdate())
        self.db_set("lab_status", "Completed")

        if self.service_request:
            frappe.db.set_value(
                "Service Request", self.service_request, "status", "completed-Request Status"
            )

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        if self.service_request:
            frappe.db.set_value("Service Request", self.service_request, "status", "active-Request Status")
        self.reload()

    def on_update(self):
        if self.sensitivity_test_items:
            sensitivity = sorted(self.sensitivity_test_items, key=lambda x: x.antibiotic_sensitivity)
            for i, item in enumerate(sensitivity):
                item.idx = i + 1
            self.sensitivity_test_items = sensitivity

    def after_insert(self):
        if self.service_request:
            billing_status = frappe.db.get_value("Service Request", self.service_request, "billing_status")
            if billing_status == "Invoiced":
                self.db_set("invoiced", True)

        if self.template:
            self.load_test_from_template()
            self.reload()

            # create nursing tasks
            template = frappe.db.get_value("Lab Test Template", self.template, "nursing_checklist_template")
            if template:
                NursingTask.create_nursing_tasks_from_template(template, self, start_time=now_datetime())

    def load_test_from_template(self):
        lab_test = self
        create_test_from_template(lab_test)
        self.reload()

    def set_secondary_uom_result(self):
        for item in self.normal_test_items:
            if item.result_value and item.secondary_uom and item.conversion_factor:
                try:
                    item.secondary_uom_result = float(item.result_value) * float(item.conversion_factor)
                except Exception:
                    item.secondary_uom_result = ""
                    frappe.msgprint(
                        _("Row #{0}: Result for Secondary UOM not calculated").format(item.idx), title=_("Warning")
                    )

    def validate_result_values(self):
        if self.normal_test_items:
            for item in self.normal_test_items:
                if not item.result_value and not item.allow_blank and item.require_result_value:
                    frappe.throw(
                        _("Row #{0}: Please enter the result value for {1}").format(
                            item.idx, frappe.bold(item.lab_test_name)
                        ),
                        title=_("Mandatory Results"),
                    )

        if self.descriptive_test_items:
            for item in self.descriptive_test_items:
                if not item.result_value and not item.allow_blank and item.require_result_value:
                    frappe.throw(
                        _("Row #{0}: Please enter the result value for {1}").format(
                            item.idx, frappe.bold(item.lab_test_particulars)
                        ),
                        title=_("Mandatory Results"),
                    )



	# def get_indicator(self):
        # """Customize status badges before submission"""
        # status_map = {
        #     "Draft": ("yellow", "Draft"),
        #     "Ackn": ("green", "Approved"),
        #     "Rejected": ("red", "Rejected"),
        #     "In Review": ("blue", "In Review")
        # }
        
        # # Use custom status if available, otherwise fallback to docstatus
        # if self.status in status_map:
        #     return status_map[self.status]  # (Color, Label)

        # # Default Frappe behavior
        # return ("grey", "Draft") if self.docstatus == 0 else None

					
def before_insert(self):
	if self.service_request:
		lab_test = frappe.db.exists(
			"Lab Test",
			{"service_request": self.service_request, "docstatus": ["!=", 2]},
		)
		if lab_test:
			frappe.throw(
				_("Lab Test {0} already created from service request {1}").format(
					frappe.bold(get_link_to_form("Lab Test", lab_test)),
					frappe.bold(get_link_to_form("Service Request", self.service_request)),
				),
				title=_("Already Exist"),
			)


def create_test_from_template(lab_test):
	template = frappe.get_doc("Lab Test Template", lab_test.template)
	patient = frappe.get_doc("Patient", lab_test.patient)

	lab_test.lab_test_name = template.lab_test_name
	lab_test.result_date = getdate()
	lab_test.department = template.department
	lab_test.lab_test_group = template.lab_test_group
	lab_test.legend_print_position = template.legend_print_position
	lab_test.result_legend = template.result_legend
	lab_test.worksheet_instructions = template.worksheet_instructions

	lab_test = create_sample_collection(lab_test, template, patient, None)
	load_result_format(lab_test, template, None, None)


@frappe.whitelist()
def update_status(status, name):
	if name and status:
		frappe.db.set_value("Lab Test", name, {"status": status, "approved_date": getdate()})


@frappe.whitelist()
def create_multiple(doctype, docname):
	if not doctype or not docname:
		frappe.throw(
			_("Sales Invoice or Patient Encounter is required to create Lab Tests"),
			title=_("Insufficient Data"),
		)

	lab_test_created = False
	if doctype == "Sales Invoice":
		lab_test_created = create_lab_test_from_invoice(docname)
	elif doctype == "Patient Encounter":
		lab_test_created = create_lab_test_from_encounter(docname)

	if lab_test_created:
		frappe.msgprint(
			_("Lab Test(s) {0} created successfully").format(lab_test_created), indicator="green"
		)


def create_lab_test_from_encounter(encounter):
	lab_test_created = False
	encounter = frappe.get_doc("Patient Encounter", encounter)

	if encounter:
		patient = frappe.get_doc("Patient", encounter.patient)
		service_requests = frappe.db.get_list(
			"Service Request",
			filters={
				"order_group": encounter.name,
				"status": ["!=", "completed-Request Status"],
				"template_dt": "Lab Test Template",
			},
			fields=["name"],
		)
		if service_requests:
			for service_request in service_requests:
				service_request_doc = frappe.get_doc("Service Request", service_request)
				template = get_lab_test_template(service_request_doc.template_dn)
				if template:
					lab_test = create_lab_test_doc(
						encounter.practitioner,
						patient,
						template,
						encounter.company,
						1 if service_request_doc.billing_status == "Invoiced" else 0,
					)
					lab_test.service_request = service_request_doc.name
					lab_test.save(ignore_permissions=True)
					# frappe.db.set_value("Service Request", service_request_doc.name, "status", "Scheduled")
					if not lab_test_created:
						lab_test_created = lab_test.name
					else:
						lab_test_created += ", " + lab_test.name
	return lab_test_created


def create_lab_test_from_invoice(sales_invoice):
	lab_tests_created = False
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	if invoice and invoice.patient:
		patient = frappe.get_doc("Patient", invoice.patient)
		for item in invoice.items:
			lab_test_created = 0
			if item.reference_dt == "Service Request":

				lab_test_created = (
					1 if frappe.db.exists("Lab Test", {"service_request": item.reference_dn}) else 0
				)
			elif item.reference_dt == "Lab Test":
				lab_test_created = 1
			if lab_test_created != 1:
				template = get_lab_test_template(item.item_code)
				if template:
					lab_test = create_lab_test_doc(
						invoice.ref_practitioner, patient, template, invoice.company, True, item.service_unit
					)
					if item.reference_dt == "Service Request":
						lab_test.service_request = item.reference_dn
					lab_test.save(ignore_permissions=True)
					if item.reference_dt != "Service Request":
						frappe.db.set_value(
							"Sales Invoice Item",
							item.name,
							{"reference_dt": "Lab Test", "reference_dn": lab_test.name},
						)
					if not lab_tests_created:
						lab_tests_created = lab_test.name
					else:
						lab_tests_created += ", " + lab_test.name
	return lab_tests_created


def get_lab_test_template(item):
	template_id = frappe.db.exists("Lab Test Template", {"item": item})
	if template_id:
		return frappe.get_doc("Lab Test Template", template_id)
	return False


def create_lab_test_doc(
	practitioner, patient, template, company, invoiced=False, service_unit=None
):
	lab_test = frappe.new_doc("Lab Test")
	lab_test.invoiced = invoiced
	lab_test.practitioner = practitioner
	lab_test.patient = patient.name
	lab_test.patient_age = patient.get_age()
	lab_test.patient_sex = patient.sex
	lab_test.email = patient.email
	lab_test.mobile = patient.mobile
	lab_test.report_preference = patient.report_preference
	lab_test.department = template.department
	lab_test.template = template.name
	lab_test.lab_test_group = template.lab_test_group
	lab_test.result_date = getdate()
	lab_test.company = company
	lab_test.service_unit = service_unit
	return lab_test


def create_normals(template, lab_test):
	lab_test.normal_toggle = 1
	normal = lab_test.append("normal_test_items")
	normal.lab_test_name = template.lab_test_name
	normal.lab_test_uom = template.lab_test_uom
	normal.secondary_uom = template.secondary_uom
	normal.conversion_factor = template.conversion_factor
	normal.normal_range = template.lab_test_normal_range
	normal.require_result_value = 1
	normal.allow_blank = 0
	normal.template = template.name


def create_imaging(template, lab_test):
	lab_test.imaging_toggle = 1
	lab_test.template = template.name
	lab_test.lab_test_name = template.lab_test_name
	lab_test.descriptive_result = template.descriptive_result


def create_compounds(template, lab_test, is_group):
	lab_test.normal_toggle = 1
	for normal_test_template in template.normal_test_templates:
		normal = lab_test.append("normal_test_items")
		if is_group:
			normal.lab_test_event = normal_test_template.lab_test_event
		else:
			normal.lab_test_name = normal_test_template.lab_test_event

		normal.lab_test_uom = normal_test_template.lab_test_uom
		normal.secondary_uom = normal_test_template.secondary_uom
		normal.conversion_factor = normal_test_template.conversion_factor
		normal.normal_range = normal_test_template.normal_range
		normal.require_result_value = 1
		normal.allow_blank = normal_test_template.allow_blank
		normal.template = template.name


def create_descriptives(template, lab_test):
	lab_test.descriptive_toggle = 1
	if template.sensitivity:
		lab_test.sensitivity_toggle = 1
	for descriptive_test_template in template.descriptive_test_templates:
		descriptive = lab_test.append("descriptive_test_items")
		descriptive.lab_test_particulars = descriptive_test_template.particulars
		descriptive.require_result_value = 1
		descriptive.allow_blank = descriptive_test_template.allow_blank
		descriptive.template = template.name


def create_sample_doc(template, patient, invoice, company=None, lab_test=None):  # Added lab_test as a parameter
    print(f"Debug: Lab Test - {lab_test}")
    print(f"Debug: Lab Test Name - {lab_test.name if lab_test else 'None'}")
    print(f"Debug: Lab Test Template - {lab_test.template if lab_test else 'None'}")
    print(f"Debug: Sample Template - {template.name if template else 'None'}")

    if not lab_test:
        print("Error: Lab Test is missing!")
    
    if lab_test and not hasattr(lab_test, "template"):
        print("Error: Lab Test does not have a 'template' field!")

    if template.sample:
        sample_exists = frappe.db.exists(
            {
                "doctype": "Sample Collection",
                "patient": patient.name,
                "docstatus": 0,
                "sample": template.sample,
            }
        )

        if sample_exists:
            print(f"Debug: Sample Collection Exists - {sample_exists}")
            # Update existing sample collection
            sample_collection = frappe.get_doc("Sample Collection", sample_exists)
            quantity = int(sample_collection.sample_qty) + int(template.sample_qty)

            if template.sample_details:
                sample_details = sample_collection.sample_details + "\n-\n" + _("Test :")
                sample_details += (template.get("lab_test_name") or template.get("template")) + "\n"
                sample_details += _("Collection Details:") + "\n\t" + template.sample_details
                frappe.db.set_value(
                    "Sample Collection", sample_collection.name, "sample_details", sample_details
                )

            frappe.db.set_value("Sample Collection", sample_collection.name, "sample_qty", quantity)

        else:
            print("Debug: Creating a new Sample Collection")
            # Create Sample Collection for template, copy vals from Invoice
            sample_collection = frappe.new_doc("Sample Collection")
            if invoice:
                sample_collection.invoiced = False

            sample_collection.patient = patient.name
            sample_collection.patient_age = patient.get_age()
            sample_collection.lab_test_name = template.name
            sample_collection.patient_sex = patient.sex
            sample_collection.sample = template.sample
            sample_collection.sample_uom = template.sample_uom
            sample_collection.sample_qty = template.sample_qty
            sample_collection.company = company
            sample_collection.save(ignore_permissions=True)
            print(f"Debug: Sample collection - {sample_collection.lab_test_name}")

        return sample_collection


def create_sample_collection(lab_test, template, patient, invoice):
	if frappe.get_cached_value("Healthcare Settings", None, "create_sample_collection_for_lab_test"):
		sample_collection = create_sample_doc(template, patient, invoice, lab_test.company)
		if sample_collection:
			lab_test.sample = sample_collection.name
			sample_collection_doc = get_link_to_form("Sample Collection", sample_collection.name)
			frappe.msgprint(
				_("Sample Collection {0} has been created").format(sample_collection_doc),
				title=_("Sample Collection"),
				indicator="green",
			)
	return lab_test


def create_sample_collection(lab_test, template, patient, invoice):
	if frappe.get_cached_value("Healthcare Settings", None, "create_sample_collection_for_lab_test"):
		sample_collection = create_sample_doc(template, patient, invoice, lab_test.company)
		if sample_collection:
			lab_test.sample = sample_collection.name
			sample_collection_doc = get_link_to_form("Sample Collection", sample_collection.name)
			frappe.msgprint(
				_("Sample Collection {0} has been created").format(sample_collection_doc),
				title=_("Sample Collection"),
				indicator="green",
			)
	return lab_test


def load_result_format(lab_test, template, prescription, invoice):
	if template.lab_test_template_type == "Single":
		create_normals(template, lab_test)

	elif template.lab_test_template_type == "Compound":
		create_compounds(template, lab_test, False)

	elif template.lab_test_template_type == "Descriptive":
		create_descriptives(template, lab_test)

	elif template.lab_test_template_type == "Imaging":
		create_imaging(template, lab_test)

	elif template.lab_test_template_type == "Grouped":
		# Iterate for each template in the group and create one result for all.
		for lab_test_group in template.lab_test_groups:
			# Template_in_group = None
			if lab_test_group.lab_test_template:
				template_in_group = frappe.get_doc("Lab Test Template", lab_test_group.lab_test_template)
				if template_in_group:
					if template_in_group.lab_test_template_type == "Single":
						create_normals(template_in_group, lab_test)

					elif template_in_group.lab_test_template_type == "Compound":
						normal_heading = lab_test.append("normal_test_items")
						normal_heading.lab_test_name = template_in_group.lab_test_name
						normal_heading.require_result_value = 0
						normal_heading.allow_blank = 1
						normal_heading.template = template_in_group.name
						create_compounds(template_in_group, lab_test, True)

					elif template_in_group.lab_test_template_type == "Descriptive":
						descriptive_heading = lab_test.append("descriptive_test_items")
						descriptive_heading.lab_test_name = template_in_group.lab_test_name
						descriptive_heading.require_result_value = 0
						descriptive_heading.allow_blank = 1
						descriptive_heading.template = template_in_group.name
						create_descriptives(template_in_group, lab_test)

			else:  # Lab Test Group - Add New Line
				normal = lab_test.append("normal_test_items")
				normal.lab_test_name = lab_test_group.group_event
				normal.lab_test_uom = lab_test_group.group_test_uom
				normal.secondary_uom = lab_test_group.secondary_uom
				normal.conversion_factor = lab_test_group.conversion_factor
				normal.normal_range = lab_test_group.group_test_normal_range
				normal.allow_blank = lab_test_group.allow_blank
				normal.require_result_value = 1
				normal.template = template.name

	if template.lab_test_template_type != "No Result":
		if prescription:
			lab_test.prescription = prescription
			if invoice:
				frappe.db.set_value(
					"Service Request", lab_test.service_request, "status", "completed-Request Status"
				)
		lab_test.save(ignore_permissions=True)  # Insert the result
		return lab_test

#Lab Test Without Binding Employee ID
# @frappe.whitelist()
# def get_employee_by_user_id(user_id):
# 	emp_id = frappe.db.exists("Employee", {"user_id": user_id})
# 	if emp_id:
# 		return frappe.get_doc("Employee", emp_id)
# 	return None


@frappe.whitelist()
def get_lab_test_prescribed(patient):
	hso = frappe.qb.DocType("Service Request")
	return (
		frappe.qb.from_(hso)
		.select(
			hso.template_dn, hso.order_group, hso.billing_status, hso.practitioner, hso.order_date, hso.name
		)
		.where(hso.patient == patient)
		.where(hso.status != "completed-Request Status")
		.where(hso.template_dt == "Lab Test Template")
		.orderby(hso.creation, order=frappe.qb.desc)
	).run()