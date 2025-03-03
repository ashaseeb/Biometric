import frappe

@frappe.whitelist(allow_guest=True)
def single_record_upload():
    try:
        employee_name = "majd"
        checkin_time = "16:8:16"
        log_type = "IN"
        user_id = 112

        if log_type not in ["IN", "OUT"]:
            return {"error": f"Invalid log type: {log_type}. Allowed values: IN, OUT"}

        created_entries = []

        employee_id = frappe.get_value("Employee", {"employee_name": employee_name}, "name")

        if not employee_id:
            new_employee = frappe.get_doc({
                "doctype": "Employee",
                "employee_name": employee_name,
                "status": "Active",
                "attendance_device_id": user_id,
                "company": frappe.defaults.get_defaults().get("company"),
            })
            new_employee.insert(ignore_permissions=True)
            frappe.db.commit()
            employee_id = new_employee.name  
            created_entries.append(f"New employee created: {employee_name} ({employee_id})")

        existing_checkin = frappe.get_value("Employee Checkin", 
            {"employee": employee_id, "time": checkin_time}, "name"
        )

        if existing_checkin:
            return {"error": f"Duplicate check-in skipped for {employee_id} at {checkin_time}"}

        checkin_doc = frappe.get_doc({
            "doctype": "Employee Checkin",
            "employee": employee_id,  
            "time": checkin_time,
            "log_type": log_type,
        })
        checkin_doc.insert(ignore_permissions=True)
        created_entries.append(f"Check-in added for {employee_id} at {checkin_time}")

        frappe.db.commit()

        return {
            "message": "Employee Checkin data uploaded successfully",
            "created_entries": created_entries
        }

    except Exception as e:
        frappe.log_error(f"Error processing check-in: {str(e)[:100]}")
        return {"error": "Internal Server Error", "details": str(e)[:100]}
