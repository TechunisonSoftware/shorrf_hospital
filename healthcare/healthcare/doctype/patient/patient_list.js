frappe.listview_settings['Patient'] = {
    hide_name_column: true,
    onload: function(listview) {       
        listview.page.fields_dict["name"]?.$wrapper?.hide();     
     
    }
};