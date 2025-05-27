# -*- coding: utf-8 -*-
# Copyright (c) 2015, ESS and contributors
# For license information, please see license.txt


import json

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from healthcare.healthcare.doctype.observation.observation import add_observation
from healthcare.healthcare.doctype.observation_template.observation_template import (
	get_observation_template_details,
)


class SampleCollection(Document):
    def after_insert(self):
		
        if self.observation_sample_collection:
            for obs in self.observation_sample_collection:
                if obs.get("has_component"):
                    data = set_component_observation_data(obs.get("observation_template"))
                    if data and len(data) > 0:
                        frappe.db.set_value(
                            "Observation Sample Collection",
                            obs.get("name"),
                            {
                                "component_observations": json.dumps(data),
                            },
                        )

    def validate(self):
        if self.observation_sample_collection:
            for obs in self.observation_sample_collection:
                if obs.get("has_component") and obs.get("component_observations"):
                    component_observations = json.loads(obs.get("component_observations"))
                    if not any((comp["status"] == "Open") for comp in component_observations):
                        obs.status = "Collected"

        if not any((obs.get("status") == "Open") for obs in self.observation_sample_collection):
            self.status = "Collected"
        else:
            self.status = "Partly Collected"

    def on_submit(self):
        # self.status = "Completed"
        # doc.save(ignore_permissions=True)

        if self.observation_sample_collection:
            for obs in self.observation_sample_collection:
                if obs.get("service_request"):
                    frappe.db.set_value(
                        "Service Request", obs.get("service_request"), "status", "completed-Request Status")
                    
               
        if self.observation_sample_collection:
            for obs in self.observation_sample_collection:
                if obs.get("observation_template"):  
                    frappe.db.set_value(
                        "Observation Sample Collection",
                        obs.get("observation_template"),
                        "status",
                        "Collected"
                    )
     
        frappe.db.commit()

  
			
    def on_cancel(self):
        if self.observation_sample_collection:
            for obs in self.observation_sample_collection:
                if obs.get("service_request"):
                    frappe.db.set_value(
                        "Service Request", obs.get("service_request"), "status", "active-Request Status"
                    )

        exist_diagnostic_report = frappe.db.exists(
            "Diagnostic Report",
            {"sample_collection": self.name},
        )
        if exist_diagnostic_report:
            frappe.delete_doc("Diagnostic Report", exist_diagnostic_report)


@frappe.whitelist()
def create_observation(selected, sample_collection, component_observations=None, child_name=None, patient=None):
    frappe.enqueue(
        "healthcare.healthcare.doctype.sample_collection.sample_collection.insert_observation",
        selected=selected,
        sample_collection=sample_collection,
        component_observations=component_observations,
        child_name=child_name,
    )

    if not sample_collection:
        frappe.throw(("Sample Collection is not specified"))

    try:
        lab_tests = frappe.get_all(
            "Lab Test",
            filters={"sample": sample_collection, "status": ["in", ["Draft", "Collection", "Result Entry"]]},
            fields=["name"]
        )

        if not lab_tests:
            return "No Lab Test records found for the specified patient"

        for lab_test in lab_tests:
            lab_test_doc = frappe.get_doc("Lab Test", lab_test["name"])
            lab_test_doc.lab_status = "Acknowledge"
            lab_test_doc.save()
        
        frappe.db.commit()
        return "success"

    except Exception as e:
        frappe.log_error(f"Error updating Lab Test status for patient {sample_collection}: {str(e)}", "Update Lab Test Status")
        return "error"
def create_specimen(patient, selected, component_observations):
    groups = {}
    # Grouping data
    for sel in selected:
        if not sel.get("has_component") or sel.get("has_component") == 0:
            key = (sel.get("medical_department"), sel.get("sample"), sel.get("container_closure_color"))
            groups.setdefault(key, []).append(sel)
        elif sel.get("component_observations"):
            comp_observations = json.loads(sel.get("component_observations"))
            for comp in comp_observations:
                comp["name"] = sel.get("name")
                key = (comp.get("medical_department"), comp.get("sample"), comp.get("container_closure_color"))
                groups.setdefault(key, []).append(comp)

    obs_ref = {}
    specimen_docs = []
    for gr, group_items in groups.items():
        # Create specimen document only once for each group
        specimen = frappe.new_doc("Specimen")
        specimen.received_time = now_datetime()
        specimen.patient = patient
        specimen.specimen_type = group_items[0].get("sample_type")
        specimen_docs.append(specimen)

        # Map observation reference to the specimen
        for sub_grp in group_items:
            key = sub_grp.get("name") if not component_observations else sub_grp.get("idx")
            obs_ref[key] = specimen.name

    # Bulk save specimens
    frappe.get_doc({"doctype": "Bulk Create", "documents": specimen_docs}).insert(ignore_permissions=True)
    return obs_ref


def update_specimen_text_in_parent(sample_collection):
    print(f"Called for Sample Collection: {sample_collection}")

    specimens = frappe.get_all(
        "Observation Sample Collection",
        filters={"parent": sample_collection},
        fields=["specimen"]
    )
    print("Fetched specimens:", specimens)

    lab_test = frappe.get_all(
        "Lab Test",
        filters={"sample": sample_collection},
        fields=["name"]
    )

    # Extract non-empty specimen values
    specimen_values = [row["specimen"] for row in specimens if row.get("specimen")]
    print("Non-empty specimen values:", specimen_values)

    specimen_text = ", ".join(specimen_values)

    # Ensure the field name is correct
    if specimen_text:
        print("Updating Sample Collection with:", specimen_text)
        frappe.db.set_value("Sample Collection", sample_collection, "specimen", specimen_text)
        frappe.db.set_value("Lab Test", lab_test, "specimen", specimen_text)
    else:
        print("No specimen values to update.")




    # print(sample_collection,"///////////////////////////////////////////////////////////?")
    # """Update the specimen text field in Sample Collection from child table"""
    # specimens = frappe.db.get_all(
    #     "Observation Sample Collection",
    #     filters={"parent": sample_collection},
    #     fields=["specimen"],
    #     pluck="specimen",
    #     distinct=True
    # )

    # print(specimens,"specimans...............????????????????????????????????????????????????????????????????????????????////")
    
    # specimen_text = ", ".join(filter(None, specimens)) if specimens else ""
    # print(specimen_text,"specimen_text............................................!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # frappe.db.set_value(
    #     "Sample Collection",
    #     sample_collection,
    #     "specimen",
    #     specimen_text
    # )

def insert_observation(selected, sample_collection, component_observations=None, child_name=None):
    try:
        if not frappe.has_permission("Sample Collection", "write"):
            frappe.throw("You do not have permission to update Sample Collection")
        sample_col_doc = frappe.db.get_value(
            "Sample Collection",
            sample_collection,
            ["reference_name", "patient", "referring_practitioner"],
            as_dict=1,
        )
        selected = json.loads(selected)
        if component_observations and len(component_observations) > 0:
            component_observations = json.loads(component_observations)

        comp_obs_ref = create_specimen(
            sample_col_doc.get("patient"), selected, component_observations
        )
        
        child_db_set_dict = {"component_observations": json.dumps(component_observations, default=str)}
        update_data = []
        for obs in selected:
            parent_observation = obs.get("component_observation_parent")

            if child_name:
                parent_observation = frappe.db.get_value(
                    "Observation Sample Collection", child_name, "component_observation_parent"
                )

            if obs.get("status") == "Open":
                if not obs.get("has_component") or obs.get("has_component") == 0:
                    # Add observation logic
                    observation = add_observation(
                        patient=sample_col_doc.get("patient"),
                        template=obs.get("observation_template"),
                        doc="Sample Collection",
                        docname=sample_collection,
                        parent=parent_observation,
                        specimen=comp_obs_ref.get(obs.get("name"))
                        or comp_obs_ref.get(obs.get("idx")),
                        invoice=sample_col_doc.get("reference_name")
                        if sample_col_doc.reference_doc == "Sales Invoice"
                        else None,
                        practitioner=sample_col_doc.get("referring_practitioner"),
                        child=obs.get("reference_child") if obs.get("reference_child") else "",
                        service_request=obs.get("service_request"),
                    )
                    if observation:
                        update_data.append({
                            "name": obs.get("name"),
                            "status": "Collected",
                            "collection_date_time": now_datetime(),
                            "specimen": comp_obs_ref.get(obs.get("name")),
                        })
                else:
                    # Logic for handling component observations
                    if obs.get("component_observations"):
                        component_observations = json.loads(obs.get("component_observations"))
                        for j, comp in enumerate(component_observations):
                            add_observation(
                                patient=sample_col_doc.get("patient"),
                                template=comp.get("observation_template"),
                                doc="Sample Collection",
                                docname=sample_collection,
                                parent=obs.get("component_observation_parent"),
                                specimen=comp_obs_ref.get(j + 1) or comp_obs_ref.get(obs.get("name")),
                                invoice=sample_col_doc.get("reference_name"),
                                practitioner=sample_col_doc.get("referring_practitioner"),
                                child=obs.get("reference_child") if obs.get("reference_child") else "",
                                service_request=obs.get("service_request"),
                            )
                            comp["status"] = "Collected"
                            comp["collection_date_time"] = now_datetime()
                            comp["specimen"] = comp_obs_ref.get(j + 1) or comp_obs_ref.get(obs.get("name"))

                        update_data.append({
                            "name": obs.get("name"),
                            "collection_date_time": now_datetime(),
                            "component_observations": json.dumps(component_observations, default=str),
                            "status": "Collected",
                            "specimen": comp_obs_ref.get(j + 1) or comp_obs_ref.get(obs.get("name")),
                        })

        # Bulk update observation sample collection
        if update_data:
            for data in update_data:
                frappe.db.set_value("Observation Sample Collection", data["name"], data)
            print(f"➡️ Updating specimen_text for: {sample_collection}")
            update_specimen_text_in_parent(sample_collection)
            print(f"✅ specimen_text updated for: {sample_collection}")

        # if sample_collection:
        #     non_collected_samples = frappe.db.get_all(
        #         "Observation Sample Collection", {"parent": sample_collection, "status": ["!=", "Collected"]}
        #     )
        #     set_status = "Partly Collected" if non_collected_samples else "Collected"
        #     frappe.db.set_value("Sample Collection", sample_collection, "status", set_status)
        if sample_collection:
            frappe.reload_doc("Sample Collection", sample_collection)
            non_collected_samples = frappe.db.get_all(
                "Observation Sample Collection", 
                {"parent": sample_collection, "status": ["!=", "Collected"]}
            )
            if non_collected_samples:
                set_status = "Partly Collected"
            else:
                set_status = "Collected"

            frappe.db.set_value("Sample Collection", sample_collection, "status", set_status)
        
            child_db_set_dict["status"] = "Collected"
        if child_name:
            frappe.reload_doc("Observation Sample Collection", child_name)
            frappe.db.set_value(
                "Observation Sample Collection",
                child_name,
                child_db_set_dict,
            )
        return "success"

    except Exception as e:
        frappe.log_error(message=e, title="Failed to mark Collected!")
        

    frappe.publish_realtime(
        event="observation_creation_progress",
        message="Completed",
        doctype="Sample Collection",
        docname=sample_collection,
    )    

# def insert_observation(selected, sample_collection, component_observations=None, child_name=None):
# 	try:
# 		sample_col_doc = frappe.db.get_value(
# 			"Sample Collection",
# 			sample_collection,
# 			["reference_name", "patient", "referring_practitioner"],
# 			as_dict=1,
# 		)
# 		selected = json.loads(selected)
# 		if component_observations and len(component_observations) > 0:
# 			component_observations = json.loads(component_observations)
# 		comp_obs_ref = create_specimen(sample_col_doc.get("patient"), selected, component_observations)
# 		for i, obs in enumerate(selected):
# 			parent_observation = obs.get("component_observation_parent")

# 			if child_name:
# 				parent_observation = frappe.db.get_value(
# 					"Observation Sample Collection", child_name, "component_observation_parent"
# 				)

# 			if obs.get("status") == "Open":
# 				# non has_component templates
# 				if not obs.get("has_component") or obs.get("has_component") == 0:
# 					observation = add_observation(
# 						patient=sample_col_doc.get("patient"),
# 						template=obs.get("observation_template"),
# 						doc="Sample Collection",
# 						docname=sample_collection,
# 						parent=parent_observation,
# 						specimen=comp_obs_ref.get(obs.get("name"))
# 						or comp_obs_ref.get(i + 1)
# 						or comp_obs_ref.get(obs.get("idx")),
# 						invoice=sample_col_doc.get("reference_name")
# 						if sample_col_doc.reference_doc == "Sales Invoice"
# 						else None,
# 						practitioner=sample_col_doc.get("referring_practitioner"),
# 						child=obs.get("reference_child") if obs.get("reference_child") else "",
# 						service_request=obs.get("service_request"),
# 					)
# 					if observation:
# 						frappe.db.set_value(
# 							"Observation Sample Collection",
# 							obs.get("name"),
# 							{
# 								"status": "Collected",
# 								"collection_date_time": now_datetime(),
# 								"specimen": comp_obs_ref.get(obs.get("name")),
# 							},
# 						)
# 				else:
# 					# to deal the component template checked from main table and collected
# 					if obs.get("component_observations"):
# 						component_observations = json.loads(obs.get("component_observations"))
# 						for j, comp in enumerate(component_observations):
# 							observation = add_observation(
# 								patient=sample_col_doc.get("patient"),
# 								template=comp.get("observation_template"),
# 								doc="Sample Collection",
# 								docname=sample_collection,
# 								parent=obs.get("component_observation_parent"),
# 								specimen=comp_obs_ref.get(j + 1) or comp_obs_ref.get(obs.get("name")),
# 								invoice=sample_col_doc.get("reference_name"),
# 								practitioner=sample_col_doc.get("referring_practitioner"),
# 								child=obs.get("reference_child") if obs.get("reference_child") else "",
# 								service_request=obs.get("service_request"),
# 							)
# 							if observation:
# 								comp["status"] = "Collected"
# 								comp["collection_date_time"] = now_datetime()
# 								comp["specimen"] = comp_obs_ref.get(j + 1) or comp_obs_ref.get(obs.get("name"))

# 						frappe.db.set_value(
# 							"Observation Sample Collection",
# 							obs.get("name"),
# 							{
# 								"collection_date_time": now_datetime(),
# 								"component_observations": json.dumps(component_observations, default=str),
# 								"status": "Collected",
# 								"specimen": comp_obs_ref.get(j + 1) or comp_obs_ref.get(obs.get("name")),
# 							},
# 						)
# 			# to deal individually checked from component dialog
# 			if component_observations:
# 				for j, comp in enumerate(component_observations):
# 					if comp.get("observation_template") == obs.get("observation_template"):
# 						comp["status"] = "Collected"
# 						comp["collection_date_time"] = now_datetime()
# 						comp["specimen"] = comp_obs_ref.get(j + 1)

# 		child_db_set_dict = {"component_observations": json.dumps(component_observations, default=str)}
# 		# to set child table status Collected if all childs are Collected
# 		if component_observations and not any(
# 			(comp["status"] == "Open") for comp in component_observations
# 		):
# 			child_db_set_dict["status"] = "Collected"

# 		if child_name:
# 			frappe.db.set_value(
# 				"Observation Sample Collection",
# 				child_name,
# 				child_db_set_dict,
# 			)
# 		if sample_collection:
# 			non_collected_samples = frappe.db.get_all(
# 				"Observation Sample Collection", {"parent": sample_collection, "status": ["!=", "Collected"]}
# 			)
# 			if non_collected_samples and len(non_collected_samples) > 0:
# 				set_status = "Partly Collected"
# 			else:
# 				set_status = "Collected"

# 			frappe.db.set_value("Sample Collection", sample_collection, "status", set_status)

# 	except Exception as e:
# 		frappe.log_error(message=e, title="Failed to mark Collected!")

# 	frappe.publish_realtime(
# 		event="observation_creation_progress",
# 		message="Completed",
# 		doctype="Sample Collection",
# 		docname=sample_collection,
# 	)


def create_specimen(patient, selected, component_observations):
	groups = {}
	# to group by
	for sel in selected:
		if not sel.get("has_component") or sel.get("has_component") == 0:
			key = (sel.get("medical_department"), sel.get("sample"), sel.get("container_closure_color"))
			if key in groups:
				groups[key].append(sel)
			else:
				groups[key] = [sel]
		else:
			if sel.get("component_observations"):
				comp_observations = json.loads(sel.get("component_observations"))
				for comp in comp_observations:
					comp["name"] = sel.get("name")
					key = (
						comp.get("medical_department"),
						comp.get("sample"),
						comp.get("container_closure_color"),
					)
					if key in groups:
						groups[key].append(comp)
					else:
						groups[key] = [comp]
	obs_ref = {}
	for gr in groups:
		specimen = frappe.new_doc("Specimen")
		specimen.received_time = now_datetime()
		specimen.patient = patient
		specimen.specimen_type = groups[gr][0].get("sample_type")
		specimen.save()
		for sub_grp in groups[gr]:
			if component_observations:
				obs_ref[sub_grp.get("idx")] = specimen.name
			else:
				obs_ref[sub_grp.get("name")] = specimen.name

	return obs_ref


def set_component_observation_data(observation_template):
	sample_reqd_component_obs, non_sample_reqd_component_obs = get_observation_template_details(
		observation_template
	)
	data = []
	for d in sample_reqd_component_obs:
		obs_temp = frappe.get_value(
			"Observation Template",
			d,
			[
				"sample_type",
				"sample",
				"medical_department",
				"container_closure_color",
				"name as observation_template",
				"sample_qty",
			],
			as_dict=True,
		)
		obs_temp["status"] = "Open"
		data.append(obs_temp)
	return data




@frappe.whitelist()
def get_templates(lab_test):
    observation_templates = frappe.get_all(
    'Observation Template',
    filters={'lab_test': lab_test},
    fields=['name','sample']
)
    return observation_templates