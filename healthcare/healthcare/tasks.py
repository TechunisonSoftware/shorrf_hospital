import frappe
from frappe.utils import now
from frappe.core.doctype.communication.email import make


# def create_scheduled_job_type():
#     if not frappe.db.exists("Scheduled Job Type", "healthcare.tasks.run_hourly_task"):
#         frappe.get_doc({
#             "doctype": "Scheduled Job Type",
#             "method": "healthcare.tasks.run_hourly_task",
#             "frequency": "Hourly",  # or adjust as needed (e.g., Daily, Weekly)
#             "is_standard": 0
#         }).insert()

# def run_hourly_task():
#     frappe.log("Running hourly task")
    
#     try:
       
#         if not frappe.db.exists("Scheduled Job Type", "healthcare.tasks.run_hourly_task"):
#             frappe.get_doc({
#                 "doctype": "Scheduled Job Type",
#                 "frequency": "Hourly",
#                 "method":"healthcare.tasks.run_hourly_task",
#                 "status": "Complete",
#                 "is_standard": 0,
#                 "scheduled_job_type": "tasks.run_hourly_task",
#             }).insert()
        
#         # Your task logic here
#         frappe.logger().info("Hourly task executed.")
        
#         # Custom log in Scheduled Job Log
#         log = frappe.get_doc({
#             "doctype": "Scheduled Job Log",
#             "method": "healthcare.healthcare.tasks.run_hourly_task",
#             "status": "Complete",
#             "scheduled_job_type": "tasks.run_hourly_task",
#             "details": "Task completed successfully.",
#             "scheduled_time": now(),
#         })
#         log.insert()
#     except Exception as e:
#         frappe.logger().error(f"Error in hourly task: {str(e)}")
        
#         # Custom log for failure
#         log = frappe.get_doc({
#             "doctype": "Scheduled Job Log",
#             "status": "Complete",
#             "scheduled_job_type": "tasks.run_hourly_task",
#             "details": str(e),
#             "scheduled_time": now(),
#         })
#         log.insert()
#         raise
# frappe.log_error("Scheduled Job Log created", "Debug")

def send_scheduled_job_log_emails():
        
    # Fetch donors with valid email addresses
    logs = frappe.get_all(
        "Donor",
        filters={
            "email": ["is", "set"],  # Ensure the email field is not empty
        },
        fields=["name", "donor_name","email"]  # Fetch required fields
    )

    if logs:
        print("---------------------------")
        for log in logs:
            # Extract name and email for each donor
            recipient_name = log['donor_name']
            recipient_email = log['email']

            # Construct email content for each donor
            message = f"""
                Dear {recipient_name},<br><br>
                
                We are deeply grateful for your generous contributions to our mission of providing values-based education, quality healthcare, and nutrition to those in need. Your support continues to make a meaningful impact on the lives of countless individuals, and we are honored to have you as a partner in this noble cause.<br><br>
                
                Recent Updates:<br>
                We’ve been able to expand our efforts and reach even more individuals this quarter. Some highlights include:<br>
                <a href="https://www.saiaarogya.hospital/events">https://www.saiaarogya.hospital/events</a><br><br>
                
                We encourage you to explore these updates through the links above to see how your support is directly benefiting those in need.<br><br>
                
                Your continued partnership is invaluable, and we look forward to the continued success of our shared efforts. Thank you for being a vital part of our mission.<br><br>
                
                With heartfelt appreciation,<br>
                Sri Sathya Sai Sujala Sravanthi Trust
            
            """

            subject = "Heartfelt Thanks for Your Continued Support"

            # Send email to the individual donor
            frappe.sendmail(
                recipients=[recipient_email],  # Send email to the specific recipient
                subject=subject,
                message=message
            )
            print(f"Email sent successfully to {recipient_name} ({recipient_email})!")

    else:
        print("No valid email addresses found in logs.")


def new_email_method():
        
    # Fetch donors with valid email addresses
    logs = frappe.get_all(
        "Donor",
        filters={
            "email": ["is", "set"],  # Ensure the email field is not empty
        },
        fields=["name", "donor_name","email"]  # Fetch required fields
    )

    if logs:
        print("---------------------------")
        for log in logs:
            # Extract name and email for each donor
            recipient_name = log['donor_name']
            recipient_email = log['email']

            # Construct email content for each donor
            message = f"""
                Dear {recipient_name},<br><br>
                
                We are deeply grateful for your generous contributions to our mission of providing values-based education, quality healthcare, and nutrition to those in need. Your support continues to make a meaningful impact on the lives of countless individuals, and we are honored to have you as a partner in this noble cause.<br><br>
                
                Recent Updates:<br>
                We’ve been able to expand our efforts and reach even more individuals this quarter. Some highlights include:<br>
                <a href="https://www.saiaarogya.hospital/events">https://www.saiaarogya.hospital/events</a><br><br>
                
                We encourage you to explore these updates through the links above to see how your support is directly benefiting those in need.<br><br>
                
                Your continued partnership is invaluable, and we look forward to the continued success of our shared efforts. Thank you for being a vital part of our mission.<br><br>
                
                With heartfelt appreciation,<br>
                Sri Sathya Sai Sujala Sravanthi Trust
            
            """

            subject = "Heartfelt Thanks for Your Continued Support"

            # Send email to the individual donor
            frappe.sendmail(
                recipients=[recipient_email],  # Send email to the specific recipient
                subject=subject,
                message=message
            )
            print(f"Email sent successfully to {recipient_name} ({recipient_email})!")

    else:
        print("No valid email addresses found in logs.")