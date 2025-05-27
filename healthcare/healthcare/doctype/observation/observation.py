# Copyright (c) 2023, healthcare and contributors
# For license information, please see license.txt

import json
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.workflow import get_workflow_name, get_workflow_state_field
from frappe.utils import now_datetime
from frappe.utils.password import get_decrypted_password

from erpnext.setup.doctype.terms_and_conditions.terms_and_conditions import (
	get_terms_and_conditions,
)
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth


class Observation(Document):
	def validate(self):
		self.set_age()
		self.set_result_time()
		self.set_status()
		self.reference = get_observation_reference(self)
		self.validate_input()

	def on_update(self):
		set_diagnostic_report_status(self)

	def before_insert(self):
		set_observation_idx(self)

	def on_submit(self):
		# print("____________________________________________________________________________")
		if self.service_request:
			frappe.db.set_value(
				"Service Request", self.service_request, "status", "completed-Request Status"
			)
		# print("Before if")			
		if self.observation_category == "Imaging":
			# print("inside if")
			required_fields = ['patient_uid','patient_name','gender','practitioner_name','practitioner_department','observation_template','name','patient','patient_dob','posting_datetime','reference_docname','service_request','practitioner_mobile','preferred_display_name']
			specific_fields = {field: self.as_dict().get(field) for field in required_fields}			
			patient_uid = specific_fields.get("patient_uid")				
			patient = specific_fields.get("patient")
			patient_name = specific_fields.get("patient_name")
			dob = specific_fields.get("patient_dob")
			gender = specific_fields.get("gender") 
			patient_encounter_id = specific_fields.get("reference_docname")
			patientAddress = ""
			service_unit_value = ""
			service_unit = ""
			if patient_uid:		
				patient_address = frappe.get_all(
				"Address",
				filters={
					"link_doctype": "Patient",
					"link_name": patient
				},
				fields=["address_line1","address_line2","city","state","country","pincode"]		)	
				print(patient_address)	
				if patient_address:				
					formatted_address = format_patient_address(patient_address)				
					patientAddress = formatted_address		
				patient_data = {
					"patientId":patient_uid,
					"patientName":patient_name,
					"dob":dob,
					"gender":gender,
					"patientAddress":patientAddress 
				}			
				order_number = specific_fields.get("name")
				order_datetime = specific_fields.get("posting_datetime")
				modality = specific_fields.get("preferred_display_name")
				service_request_id = specific_fields.get("service_request")
				datetime_obj = datetime.strptime(order_datetime, "%Y-%m-%d %H:%M:%S.%f")
				formatted_datetime = datetime_obj.strftime("%Y%m%d%H%M")             
				doctor_name = specific_fields.get("practitioner_name")
				doctor_department = specific_fields.get("practitioner_department")
				call_back_number = specific_fields.get('practitioner_mobile')
				datetime_of_order = formatted_datetime
				observation_template = specific_fields.get("observation_template")
				patient_encounter = frappe.get_doc("Patient Encounter", patient_encounter_id)
				inpatient_record_id = patient_encounter.inpatient_record
				patient_appointment_id = patient_encounter.appointment			
				scheduled_procedure =""			
				if inpatient_record_id:			
					inpatient_record = frappe.get_doc("Inpatient Record", inpatient_record_id)				
					for occupancy in inpatient_record.inpatient_occupancies:
							
						healthcare_service_unit = occupancy.service_unit
						healthcare_service_unit_doc = frappe.get_doc("Healthcare Service Unit", healthcare_service_unit)
						parent_service_unit = healthcare_service_unit_doc.parent_healthcare_service_unit
							
						if parent_service_unit == "General Ward":
							service_unit = "GW"	
						elif parent_service_unit == "ICU Ward":
							service_unit = "ICU"	
						elif parent_service_unit == "Special Ward":
							service_unit = "SPl"	
						elif parent_service_unit == "NICU Ward":
							service_unit = "NIC"
						elif parent_service_unit == "Emergency Ward":
							service_unit = "EMW"
						else:
							service_unit = "IP"
				else:
					patient_appointment_service_unit = frappe.db.get_value(
						"Patient Appointment", 
						filters={"name": patient_appointment_id}, 
						fieldname=["service_unit"]
					)				
					service_unit_value = patient_appointment_service_unit
					if service_unit_value:
						service_unit = "OP"			
				
				for radiology in patient_encounter.radiology:
					if radiology.service_request == service_request_id:            
						scheduled_procedure= radiology.schedule_procedure
				
				request_body = {
					"patient" : patient_data,
					"patientClass" : service_unit,
					"treatingDoctor" : doctor_name,
					"referringDoctor" : doctor_name,
					"treatingDepartment":doctor_department,
					"orderNumber":order_number,
					"dateTimeofOrder":datetime_of_order,
					"callBackPhoneNumber":call_back_number,
					"modality":modality,
					"scheduledProcedure":scheduled_procedure

				}
				# print(request_body)
				# print("**********************************************************************************")
				request_to_modality(request_body,self)	

	def on_cancel(self):
		if self.service_request:
			frappe.db.set_value("Service Request", self.service_request, "status", "active-Request Status")

	def set_age(self):
		patient_doc = frappe.get_doc("Patient", self.patient)
		if patient_doc.dob:
			self.age = patient_doc.calculate_age().get("age_in_string")
			self.days = patient_doc.calculate_age().get("age_in_days")

	def set_status(self):
		if self.status not in ["Approved", "Disapproved"]:
			if self.has_result() and self.status != "Final":
				self.status = "Preliminary"
			elif self.amended_from and self.status not in ["Amended", "Corrected"]:
				self.status = "Amended"
			elif self.status not in ["Final", "Cancelled", "Entered in Error", "Unknown"]:
				self.status = "Registered"

	def set_result_time(self):
		if not self.time_of_result:
			if self.has_result():
				self.time_of_result = now_datetime()
			else:
				self.time_of_result = ""

		if self.status == "Final" and not self.time_of_approval:
			self.time_of_approval = now_datetime()
		else:
			self.time_of_approval = ""

	def has_result(self):
		result_fields = [
			"result_attach",
			"result_boolean",
			"result_data",
			"result_text",
			"result_float",
			"result_select",
		]
		for field in result_fields:
			if self.get(field, None):
				return True

		# TODO: handle fields defaulting to now
		# "result_datetime",
		# "result_time",
		# "result_period_from",
		# "result_period_to",

		return False

	def validate_input(self):
		if self.permitted_data_type in ["Quantity", "Numeric"]:
			if self.result_data and not is_numbers_with_exceptions(self.result_data):
				frappe.throw(
					_("Non numeric result {0} is not allowed for Permitted Data Type {1}").format(
						frappe.bold(self.result_data), frappe.bold(self.permitted_data_type)
					)
				)


@frappe.whitelist()
def get_observation_details(docname):
	reference = frappe.get_value(
		"Diagnostic Report", docname, ["docname", "ref_doctype"], as_dict=True
	)
	observation = []

	if reference.get("ref_doctype") == "Sales Invoice":
		observation = frappe.get_list(
			"Observation",
			fields=["*"],
			filters={
				"sales_invoice": reference.get("docname"),
				"parent_observation": "",
				"status": ["!=", "Cancelled"],
				"docstatus": ["!=", 2],
			},
			order_by="creation",
		)
	elif reference.get("ref_doctype") == "Patient Encounter":
		service_requests = frappe.get_all(
			"Service Request",
			filters={
				"source_doc": reference.get("ref_doctype"),
				"order_group": reference.get("docname"),
				"status": ["!=", "revoked-Request Status"],
				"docstatus": ["!=", 2],
			},
			order_by="creation",
			pluck="name",
		)
		observation = frappe.get_list(
			"Observation",
			fields=["*"],
			filters={
				"service_request": ["in", service_requests],
				"parent_observation": "",
				"status": ["!=", "Cancelled"],
				"docstatus": ["!=", 2],
			},
			order_by="creation",
		)

	out_data, obs_length = aggregate_and_return_observation_data(observation)

	return out_data, obs_length


def aggregate_and_return_observation_data(observations):
	out_data = []
	obs_length = 0

	for obs in observations:

		if not obs.get("has_component"):
			if obs.get("permitted_data_type"):
				obs_length += 1

			if obs.get("permitted_data_type") == "Select" and obs.get("options"):
				obs["options_list"] = obs.get("options").split("\n")

			if obs.get("observation_template") and obs.get("specimen"):
				obs["received_time"] = frappe.get_value("Specimen", obs.get("specimen"), "received_time")

			out_data.append({"observation": obs})

		else:
			child_observations = get_child_observations(obs)
			obs_dict = return_child_observation_data_as_dict(child_observations, obs, obs_length)

			if len(obs_dict) > 0:
				out_data.append(obs_dict)

	return out_data, obs_length


def get_child_observations(obs):
	return frappe.get_list(
		"Observation",
		fields=["*"],
		filters={
			"parent_observation": obs.get("name"),
			"status": ["!=", "Cancelled"],
			"docstatus": ["!=", 2],
		},
		order_by="observation_idx",
	)


def return_child_observation_data_as_dict(child_observations, obs, obs_length):
	obs_list = []
	has_result = False
	obs_approved = False

	for child in child_observations:
		if child.get("permitted_data_type"):
			obs_length += 1
		if child.get("permitted_data_type") == "Select" and child.get("options"):
			child["options_list"] = child.get("options").split("\n")
		if child.get("specimen"):
			child["received_time"] = frappe.get_value("Specimen", child.get("specimen"), "received_time")
		observation_data = {"observation": child}
		obs_list.append(observation_data)

		if (
			child.get("result_data")
			or child.get("result_text")
			or child.get("result_select") not in [None, "", "Null"]
		):
			has_result = True
		if child.get("status") == "Approved":
			obs_approved = True

	obs_dict = {
		"has_component": True,
		"observation": obs.get("name"),
		obs.get("name"): obs_list,
		"display_name": obs.get("observation_template"),
		"practitioner_name": obs.get("practitioner_name"),
		"healthcare_practitioner": obs.get("healthcare_practitioner"),
		"description": obs.get("description"),
		"has_result": has_result,
		"obs_approved": obs_approved,
	}

	return obs_dict


def get_observation_reference(doc):
	template_doc = frappe.get_doc("Observation Template", doc.observation_template)
	display_reference = ""

	for child in template_doc.observation_reference_range:
		if not child.applies_to == "All":
			if not child.applies_to == doc.gender:
				continue
		if child.age == "Range":
			day_from = day_to = 0
			if child.from_age_type == "Months":
				day_from = float(child.age_from) * 30.436875
			elif child.from_age_type == "Years":
				day_from = float(child.age_from) * 365.2425
			elif child.from_age_type == "Days":
				day_from = float(child.age_from)

			if child.to_age_type == "Months":
				day_to = float(child.age_to) * 30.436875
			elif child.to_age_type == "Years":
				day_to = float(child.age_to) * 365.2425
			elif child.to_age_type == "Days":
				day_to = float(child.age_to)

			if doc.days and float(day_from) <= float(doc.days) <= float(day_to):
				display_reference += set_reference_string(child)

		elif child.age == "All" or not doc.days:
			display_reference += set_reference_string(child)

	return display_reference


def set_reference_string(child):
	display_reference = ""
	if (child.reference_from and child.reference_to) or child.conditions:
		if child.reference_from and child.reference_to:
			display_reference = f"{str(child.reference_from)} - {str(child.reference_to)}"
		elif child.conditions:
			display_reference = f"{str(child.conditions)}"

		if child.short_interpretation:
			display_reference = f"{display_reference}: {str(child.short_interpretation)}<br>"

	elif child.short_interpretation or child.long_interpretation:
		display_reference = f"{(child.short_interpretation if child.short_interpretation else child.long_interpretation)}<br>"

	return display_reference


@frappe.whitelist()
def edit_observation(observation, data_type, result):
	observation_doc = frappe.get_doc("Observation", observation)
	if data_type in ["Range", "Ratio", "Quantity", "Numeric"]:
		observation_doc.result_data = result
	# elif data_type in ["Quantity", "Numeric"]:
	# 	observation_doc.result_float = result
	elif data_type == "Text":
		observation_doc.result_text = result
	observation_doc.save()


@frappe.whitelist()
def add_observation(**args):
	observation_doc = frappe.new_doc("Observation")
	observation_doc.posting_datetime = now_datetime()
	observation_doc.patient = args.get("patient")
	observation_doc.observation_template = args.get("template")
	observation_doc.permitted_data_type = args.get("data_type")
	observation_doc.reference_doctype = args.get("doc")
	observation_doc.reference_docname = args.get("docname")
	observation_doc.sales_invoice = args.get("invoice")
	observation_doc.healthcare_practitioner = args.get("practitioner")
	observation_doc.specimen = args.get("specimen")
	if args.get("data_type") in ["Range", "Ratio", "Quantity", "Numeric"]:
		observation_doc.result_data = args.get("result")
	# elif data_type in ["Quantity", "Numeric"]:
	# 	observation_doc.result_float = result
	elif args.get("data_type") == "Text":
		observation_doc.result_text = args.get("result")
	if args.get("parent"):
		observation_doc.parent_observation = args.get("parent")
	observation_doc.sales_invoice_item = args.get("child") if args.get("child") else ""
	observation_doc.insert(ignore_permissions=True)
	return observation_doc.name


@frappe.whitelist()
def record_observation_result(values):
	values = json.loads(values)
	if values:
		values = [dict(t) for t in {tuple(d.items()) for d in values}]
		for val in values:
			if not val.get("observation"):
				return
			observation_doc = frappe.get_doc("Observation", val["observation"])
			if observation_doc.get("permitted_data_type") in [
				"Range",
				"Ratio",
				"Quantity",
				"Numeric",
			]:
				if (
					observation_doc.get("permitted_data_type")
					in [
						"Quantity",
						"Numeric",
					]
					and val.get("result")
					and not is_numbers_with_exceptions(val.get("result"))
				):
					frappe.msgprint(
						_("Non numeric result {0} is not allowed for Permitted Type {1}").format(
							frappe.bold(val.get("result")),
							frappe.bold(observation_doc.get("permitted_data_type")),
						),
						indicator="orange",
						alert=True,
					)
					return

				if val.get("result") != observation_doc.get("result_data"):
					if val.get("result"):
						observation_doc.result_data = val.get("result")
					if val.get("note"):
						observation_doc.note = val.get("note")
					if observation_doc.docstatus == 0:
						observation_doc.save()
					elif observation_doc.docstatus == 1:
						observation_doc.save("Update")
			elif observation_doc.get("permitted_data_type") == "Text":
				if val.get("result") != observation_doc.get("result_text"):
					if val.get("result"):
						observation_doc.result_text = val.get("result")
					if val.get("note"):
						observation_doc.note = val.get("note")
					if observation_doc.docstatus == 0:
						observation_doc.save()
					elif observation_doc.docstatus == 1:
						observation_doc.save("Update")
			elif observation_doc.get("permitted_data_type") == "Select":
				if val.get("result") != observation_doc.get("result_select"):
					if val.get("result"):
						observation_doc.result_select = val.get("result")
					if val.get("note"):
						observation_doc.note = val.get("note")
					if observation_doc.docstatus == 0:
						observation_doc.save()
					elif observation_doc.docstatus == 1:
						observation_doc.save("Update")

			if observation_doc.get("observation_category") == "Imaging":
				if val.get("result"):
					observation_doc.result_text = val.get("result")
				if val.get("interpretation"):
					observation_doc.result_interpretation = val.get("interpretation")
				if val.get("result") or val.get("interpretation"):
					if val.get("note"):
						observation_doc.note = val.get("note")
					if observation_doc.docstatus == 0:
						observation_doc.save()
					elif observation_doc.docstatus == 1:
						observation_doc.save("Update")

			if not val.get("result") and val.get("note"):
				observation_doc.note = val.get("note")
				if observation_doc.docstatus == 0:
					observation_doc.save()
				elif observation_doc.docstatus == 1:
					observation_doc.save("Update")


@frappe.whitelist()
def add_note(note, observation):
	if note and observation:
		frappe.db.set_value("Observation", observation, "note", note)


def set_observation_idx(doc):
	if doc.parent_observation:
		parent_template = frappe.db.get_value(
			"Observation", doc.parent_observation, "observation_template"
		)
		idx = frappe.db.get_value(
			"Observation Component",
			{"parent": parent_template, "observation_template": doc.observation_template},
			"idx",
		)
		if idx:
			doc.observation_idx = idx


def is_numbers_with_exceptions(value):
	pattern = r"^[0-9{}]+$".format(re.escape(".<>"))
	return re.match(pattern, value) is not None


@frappe.whitelist()
def get_observation_result_template(template_name, observation):
	if observation:
		observation_doc = frappe.get_doc("Observation", observation)
		patient_doc = frappe.get_doc("Patient", observation_doc.get("patient"))
		observation_doc = json.loads(observation_doc.as_json())
		patient_doc = json.loads(patient_doc.as_json())
		# merged_dict = {"patient": patient_doc, "observation":observation_doc}
		merged_dict = {**observation_doc, **patient_doc}
		terms = get_terms_and_conditions(template_name, merged_dict)
	return terms


@frappe.whitelist()
def set_observation_status(observation, status, reason=None):
	observation_doc = frappe.get_doc("Observation", observation)
	if observation_doc.has_result():
		observation_doc.status = status
		if reason:
			observation_doc.disapproval_reason = reason
		if status == "Approved":
			observation_doc.submit()
		if status == "Disapproved":
			new_doc = frappe.copy_doc(observation_doc)
			new_doc.status = ""
			new_doc.insert()
			observation_doc.cancel()
	else:
		frappe.throw(_("Please enter result to Approve."))


def set_diagnostic_report_status(doc):
	if doc.has_result() and doc.sales_invoice and not doc.has_component and doc.sales_invoice:
		observations = frappe.db.get_all(
			"Observation",
			{
				"sales_invoice": doc.sales_invoice,
				"docstatus": 0,
				"status": ["!=", "Approved"],
				"has_component": 0,
			},
		)
		diagnostic_report = frappe.db.get_value(
			"Diagnostic Report",
			{"ref_doctype": "Sales Invoice", "docname": doc.sales_invoice},
			["name"],
			as_dict=True,
		)
		if diagnostic_report:
			workflow_name = get_workflow_name("Diagnostic Report")
			workflow_state_field = get_workflow_state_field(workflow_name)
			if observations and len(observations) > 0:
				set_status = "Partially Approved"
			else:
				set_status = "Approved"
			set_value_dict = {"status": set_status}
			if workflow_state_field:
				set_value_dict[workflow_state_field] = set_status
			frappe.db.set_value(
				"Diagnostic Report", diagnostic_report.get("name"), set_value_dict, update_modified=False
			)


def format_patient_address(address_list):
    if not address_list:
        return   
    
    address = address_list[0]   
    
    patient_address = " ".join(
        str(address.get(key, "")).strip() for key in [
            "address_line1", "address_line2", "city", "state", "country", "pincode"
        ] if address.get(key)
    )
    return patient_address

def request_to_modality(request_body, self):
    credentials = frappe.get_doc("Radiology Setting")
    url = credentials.mirth_connect_url
    username = credentials.authenticate_user
    password = get_decrypted_password("Radiology Setting", credentials.name, "authenticate_password")
    headers = {"Content-Type": "application/json"}
    api_url = f"{url}/mwlserver/"
    

    try:
        response = requests.post(
            api_url,
            json=request_body,
            headers=headers,
            auth=HTTPBasicAuth(username, password)
        )

        if response.status_code == 200:
            frappe.logger().info("API Request successful")
            frappe.msgprint(_("Radiology order sent successfully"))
            create_radiology_report_entry(self, request_body)  # Fixed indentation
            return response.json()
        else:
            
            frappe.logger().error(f"API Request failed with status code {response.status_code}")
            frappe.logger().error(f"Response: {response.text}")
            frappe.msgprint(_(f"API Request failed with status code {response.status_code}"))
            return None
    except requests.exceptions.RequestException as e:
        frappe.logger().error(f"An error occurred during the API request: {e}")
        frappe.msgprint(_(f"An error occurred during the API request: {e}"))
        return None

	
def create_radiology_report_entry(doc,request_body):
   
    existing_radiology_report = frappe.get_all(
        "Radiology Result Entry",
        filters={"observation": doc.name},
        limit=1
    ) 
   
    if not existing_radiology_report:      
        radiology_result_entry_doc = frappe.get_doc({
            "doctype": "Radiology Result Entry",
            "observation": doc.name,  
            "observation_template": doc.observation_template,        
            "observation_category": doc.observation_category,
            "schedule_procedure":request_body["scheduledProcedure"],
            "age":doc.age,
            "company":doc.company,
            "posting_datetime": doc.posting_datetime,
            "status": 'Open',               
            "medical_department": doc.medical_department, 
            "patient": doc.patient, 
            "referred_practitioner": doc.healthcare_practitioner,                   
			# "reference_doctype":doc.reference_doctype,
            "patient_encounter":doc.reference_docname,
            "service_request":doc.service_request,
            "docstatus": 0 
		})     
     
        radiology_result_entry_doc.insert(ignore_permissions=True,ignore_mandatory=True)
        frappe.db.commit()