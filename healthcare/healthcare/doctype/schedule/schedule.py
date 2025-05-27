# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Schedule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		create_log: DF.Check
		cron_format: DF.Data | None
		frequency: DF.Literal["All", "Hourly", "Hourly Long", "Daily", "Daily Long", "Weekly", "Weekly Long", "Monthly", "Monthly Long", "Cron", "Yearly", "Annual"]
		last_execution: DF.Datetime | None
		method: DF.Data | None
		next_execution: DF.Datetime | None
		scheduler_event: DF.Link | None
		select_doctype: DF.Link | None
		server_script: DF.Link | None
		stopped: DF.Check
	# end: auto-generated types
	pass
