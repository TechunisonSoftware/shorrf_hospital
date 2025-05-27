frappe.listview_settings['Patient'] = {
    onload: function(listview) {       
        listview.page.fields_dict["name"]?.$wrapper?.hide();     
     
    }
};