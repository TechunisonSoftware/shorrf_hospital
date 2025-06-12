
frappe.ui.form.on('Pharmacy Prescription', {
    onload(frm) {
        prevent_row_modification(frm);
        
        bind_medication_request_data(frm); 
          frm.disable_save()
        
           
    },   
    refresh(frm) {
        frm.disable_save()
        disable_processed_rows(frm)    
        let button = frm.add_custom_button(__('Dispense Medication'), function () {
            process_medication(frm, button);
        })        
        update_button_state(frm)          
       
    },  
})



function disable_processed_rows(frm) {
   

    frm.fields_dict["drug_prescription"].grid.grid_rows.forEach(grid_row => {    
        if (grid_row.doc.medication_status === "Dispensed") {
            $(grid_row.wrapper).find('input, select, textarea, button').prop('disabled', true); 
            $(grid_row.wrapper).find('.grid-row-check').hide();          
        } else {
            $(grid_row.wrapper).find('input, select, textarea, button').prop('disabled', false);   
            $(grid_row.wrapper).find('.grid-row-check').show();         
        }
    });

    
}


function prevent_row_modification(frm) {
    frm.set_df_property('drug_prescription', 'cannot_add_rows', true);
    frm.set_df_property('drug_prescription', 'cannot_delete_rows', true);
    frm.refresh_field('drug_prescription');
}


function remove_select_all_checkbox(frm) {
    let grid = frm.fields_dict['drug_prescription'].grid;
    if (grid) {
        $(grid.wrapper).find('.grid-heading-row .grid-row-check').remove();
        $(grid.wrapper).find('.grid-heading-row').off('click', '.grid-row-check');
    }
}


function bind_medication_request_data(frm) {
    if (!frm.doc.patient_encounter) return;
    frappe.call({
        method: 'healthcare.healthcare.doctype.pharmacy_prescription.pharmacy_prescription.get_medication_requests',
        args: { patient_encounter: frm.doc.patient_encounter },
        callback(r) {
            if (r.message) {
                let medication_requests = r.message;
                frm.doc.drug_prescription.forEach(row => {
                    let request = medication_requests.find(req => req.medication_item === row.medication);
                    if (request) {
                        frappe.model.set_value(row.doctype, row.name, 'medication_request', request.name);
                        
                        // Fetch and bind quantity
                        frappe.call({
                            method: 'healthcare.healthcare.doctype.pharmacy_prescription.pharmacy_prescription.get_medication_quantity',
                            args: { order_group: frm.doc.patient_encounter, medication_item: row.medication },
                            callback(quantity_response) {
                                if (quantity_response.message) {
                                    frappe.model.set_value(row.doctype, row.name, 'qty', quantity_response.message);
                                }
                            }
                        });

                        // Check and update status if already processed
                        if (row.is_processed) {
                            frappe.call({
                                method: 'healthcare.healthcare.doctype.pharmacy_prescription.pharmacy_prescription.update_medication_request_status',
                                args: { medication_request_name: request.name },
                                callback(response) {
                                    if (response.message) {                                        
                                        // Handle response if needed
                                    }
                                }
                            });
                        }
                }
                });

                frm.refresh_field('drug_prescription');
            }
        }
    });
}



function process_medication(frm, button) {   
    let selected_rows = frm.fields_dict['drug_prescription'].grid.get_selected_children();

    if (!selected_rows || selected_rows.length === 0) {
        frappe.msgprint(__('Please select at least one row to dispense medication.'));
        return;
    }

    let unprocessed_rows = selected_rows.filter(row => row.medication_status !== "Dispensed");

    if (unprocessed_rows.length === 0) {
        frappe.msgprint(__('All selected rows are already processed.'));
        return;
    }

    let selected_items = [];
    let fetch_quantity_promises = unprocessed_rows.map(row => {
        return new Promise((resolve) => {
            // frappe.call({
            //     method: 'healthcare.healthcare.doctype.pharmacy_prescription.pharmacy_prescription.get_medication_quantity',
            //     args: { order_group: frm.doc.patient_encounter, medication_item: row.medication },
            //     callback(r) {
            //         selected_items.push({
            //             item: row.medication,
            //             source_warehouse: 'Pharmacy Counter - T',
            //             target_warehouse: 'Dispensed to Patient - T',
            //             quantity: row.dispensed_amount || r.message || 0,
            //             // available_stock: 0,
            //             row_name: row.name,
            //             medication_request: row.medication_request  
            //         });
            //         resolve();
            //     }
            // });
            frappe.call({
                method: 'healthcare.healthcare.doctype.pharmacy_prescription.pharmacy_prescription.get_medication_quantity',
                args: { 
                    order_group: frm.doc.patient_encounter, 
                    medication_item: row.medication 
                },
                callback(r) {
                    let company_abbreviation = frm.doc.company_abbreviation || "T";  // Fallback to 'T' if not available
            
                    selected_items.push({
                        item: row.medication,
                        source_warehouse: `Pharmacy Counter - ${company_abbreviation}`,
                        target_warehouse: `Dispensed to Patient - ${company_abbreviation}`,
                        quantity: row.dispensed_amount || r.message || 0,
                        available_stock: r.message,
                        row_name: row.name,
                        rate:row.rate,
                        medication_request: row.medication_request  
                    });
                    resolve();
                }
            });
        });
    });

    Promise.all(fetch_quantity_promises).then(() => {
        if (selected_items.length === 0) {
            frappe.msgprint(__('No valid medications to dispense.'));
            return;
        }

        let fields = selected_items.map((item , index)=> [
            { fieldtype: 'Section Break', label: `Medication: ${item.item}` },
            { fieldtype: 'Link', fieldname: `item_${item.row_name}`, label: 'Item', options: 'Item', reqd: 1, default: item.item},
            { fieldtype: 'Column Break' },
            {
                fieldtype: 'Link', fieldname: `source_warehouse_${item.row_name}`, label: 'Source Warehouse',
                options: 'Warehouse', reqd: 1, default: item.source_warehouse,
                change: function () {
                    let warehouse = dialog.get_value(`source_warehouse_${item.row_name}`);
                    fetch_available_stock(item.item, warehouse, item.row_name);
                }
            },
            // { fieldtype: 'Column Break' },
            { fieldtype: 'Link', fieldname: `target_warehouse_${item.row_name}`, label: 'Target Warehouse', options: 'Warehouse',reqd: 1, default: item.target_warehouse },
            { fieldtype: 'Column Break' },
            { fieldtype: 'Float', fieldname: `quantity_${item.row_name}`, label: 'Quantity', reqd: 1,default: item.quantity ,change: () => {
                let qty = dialog.get_value(`quantity_${item.row_name}`);
                fetch_item_rate(item.item, item.row_name, qty, index);
            }},
            
            { fieldtype: 'Column Break' },
            { fieldtype: 'Currency', fieldname: `rate_${item.row_name}`, label: 'Rate (as per)', default: item.rate, read_only: 1 },
            { fieldtype: 'Column Break' },
            { fieldtype: 'Currency', fieldname: `total_${item.row_name}`, label: 'Total', default: item.total, read_only: 1  },
            { fieldtype: 'Column Break' },
            { fieldtype: 'Read Only', fieldname: `available_stock_${item.row_name}`, label: 'Available Stock', default: item.available_stock },
        ]).flat();
        fields.push(
            { fieldtype: 'Section Break' },
            { fieldtype: 'Currency', fieldname: 'grand_total', label: 'Grand Total', read_only: 1, default: 0 }
        );
 
 
        let dialog = new frappe.ui.Dialog({
            title: 'Dispense Medication',
            fields: fields,
            primary_action_label: 'Submit',
            primary_action() {
                let data = dialog.get_values();
                if (data) {
                    let stock_issue = false;
                    let stock_messages = [];
            
                    selected_items.forEach(item => {
                        let entered_quantity = data[`quantity_${item.row_name}`];
                        let available_stock = data[`available_stock_${item.row_name}`];

                        if (entered_quantity > available_stock) {
                            stock_issue = true;
                            stock_messages.push(`Stock for ${item.item} is only ${available_stock}, but you are trying to dispense ${entered_quantity}.`);
                        }

                        let already_dispensed = item.quantity || 0;
                        let new_dispensed_amount = already_dispensed - entered_quantity;

                        if (new_dispensed_amount < 0) {
                            stock_issue = true;
                            stock_messages.push(`Dispensed amount cannot be allowed excess quantity.`);
                        }
                    });

                    if (stock_issue) {
                        frappe.msgprint({
                            title: __('Invalid Quantity'),
                            message: stock_messages.join("<br>"),
                            indicator: 'red'
                        });
                        return;
                    }

                    let update_dispense_promises = selected_items.map(item => {
                        return new Promise((resolve) => {
                            let already_dispensed = item.quantity || 0;
                            let new_dispensed_amount = already_dispensed - data[`quantity_${item.row_name}`];
                            let remaining_quantity = new_dispensed_amount;
                            let new_status = "Booked"; 
                    
                            if (remaining_quantity === 0) {
                                new_status = "Dispensed"; // Fully dispensed
                            } else if (remaining_quantity < item.quantity) {
                                new_status = "Partially Dispensed"; // Partially dispensed
                            }

                            frappe.call({
                                method: 'healthcare.healthcare.doctype.pharmacy_prescription.pharmacy_prescription.create_stock_entry',
                                args: {
                                    prescription_name: frm.doc.name,
                                    item: data[`item_${item.row_name}`],
                                    source_warehouse: data[`source_warehouse_${item.row_name}`],
                                    target_warehouse: data[`target_warehouse_${item.row_name}`],
                                    quantity: data[`quantity_${item.row_name}`]
                                },
                                callback(response) {
                                    if (response.message) { 
                                        frappe.model.set_value('Pharmacy Drug Prescription', item.row_name, 'dispensed_amount', new_dispensed_amount);
                                        frappe.model.set_value('Pharmacy Drug Prescription', item.row_name, 'remaining_quantity', remaining_quantity);
                                        frappe.model.set_value('Pharmacy Drug Prescription', item.row_name, 'medication_status', new_status);
                                        resolve();
                                    }
                                }
                            });
                        });
                    });

                    Promise.all(update_dispense_promises).then(() => {
                        update_prescription_status(frm);
                        frm.refresh_field('drug_prescription'); 
                        frm.dirty(); // Mark document as changed
                        frm.save().then(() => {
                            frm.refresh(); // Refresh the page after saving
                        });
                        dialog.hide();
                    });
                }
            }
        });

        dialog.show();

        selected_items.forEach((item , index)=> {
            console.log(`Calling fetch for item ${index}: ${item.item}`);
            
            dialog.set_value(`quantity_${item.row_name}`, item.quantity);
            fetch_item_rate(item.item, item.row_name, item.quantity, index);
            fetch_available_stock(item.item, item.source_warehouse, item.row_name);
        });

        function fetch_available_stock(item_code, warehouse, row_name) {
            if (!warehouse) return;
            frappe.call({
                method: 'erpnext.stock.utils.get_latest_stock_qty',
                args: {
                    item_code: item_code,
                    warehouse: warehouse
                },
                callback(r) {
                    dialog.set_value(`available_stock_${row_name}`, r.message || 0);
                }
            });
        }
        // Initialize an array to hold totals for each item, length = selected_items.length
        let totalsArray = new Array(selected_items.length).fill(0);
 
        function fetch_item_rate(item_code, row_name, quantity, index) {
            frappe.call({
                method: 'healthcare.healthcare.doctype.pharmacy_prescription.pharmacy_prescription.get_item_rate',
                args: { item_code },
                callback(rate_response) {
                    let rate = rate_response.message || 0;
                    dialog.set_value(`rate_${row_name}`, rate);
 
                    let total = rate * quantity;
                    dialog.set_value(`total_${row_name}`, total);
 
                    // Store total in array at correct index
                    totalsArray[index] = total;
 
                    // Now calculate grand total by summing the array
                    let grand_total = totalsArray.reduce((acc, val) => acc + val, 0);
                    dialog.set_value('grand_total', grand_total);
 
                    console.log(`Updated grand total: ${grand_total}`);
                }
            });
        }
    });
}




function update_prescription_status(frm) { 
    let total_rows = frm.doc.drug_prescription.length;  
    let fully_dispensed = frm.doc.drug_prescription.filter(row => row.medication_status === "Dispensed").length;
    let partially_dispensed = frm.doc.drug_prescription.filter(row => row.medication_status === "Partially Dispensed").length;

    let new_status = "Booked"; // Default status

    if (fully_dispensed === total_rows) {
        new_status = "Dispensed";
    } else if (partially_dispensed > 0 || fully_dispensed > 0) {
        new_status = "Partially Dispensed"; // Ensure this updates when required
    }

    frappe.model.set_value(frm.doctype, frm.doc.name, 'status', new_status);
}



function update_button_state(frm) {  
    if(frm.doc.status === "Dispensed"){
        frm.custom_buttons['Dispense Medication'].hide()
         
    }  
   
}










