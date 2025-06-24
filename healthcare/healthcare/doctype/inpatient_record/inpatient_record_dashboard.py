from frappe import _
 
 
def get_data():
    return {
        "fieldname": "encounter",
        "non_standard_fieldnames": {    
            "Service Request": "inpatient_record",          
        },
        "transactions": [
            
            {               
                "items": [                  
                    "Service Request",                  
                ],
            },
        ],
        "disable_create_buttons": ["Service Request"],
    }