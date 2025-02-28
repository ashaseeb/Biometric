import frappe
import pandas as pd
from frappe.utils.file_manager import save_file
from io import BytesIO

@frappe.whitelist(allow_guest=True)
def upload_employee_checkin():
    try:
        uploaded_file = frappe.request.files.get("file")

        if not uploaded_file:
            return {"error": "File is required."}
        
        file_content = uploaded_file.read()

        file_doc = save_file(
            uploaded_file.filename, 
            file_content, 
            "Employee Checkin", 
            "Employee Checkin Upload",  
            is_private=1
        )

        file_stream = BytesIO(file_content)
        df = pd.read_excel(file_stream, engine="openpyxl")

        required_columns = ["USERID", "InOutDateTime", "DeviceInOut","UserName"]

        if not all(col in df.columns for col in required_columns):
            return {"error": f"Missing required columns: {', '.join(required_columns)}"}

        skipped_entries = []
        created_entries = []

        for _, row in df.iterrows():
            employee_id = str(row["USERID"]).strip()
            checkin_time = row["InOutDateTime"]
            in_out = str(row["DeviceInOut"]).strip().upper()
            employee=row.get("UserName")

            if in_out not in ["IN", "OUT"]:
                skipped_entries.append(f"Invalid log type for USERID {employee_id} at {checkin_time}: {in_out}")
                continue  

            existing_checkin = frappe.get_value("Employee Checkin", 
                {"employee": employee_id, "time": checkin_time}, "name"
            )

            if existing_checkin:
                skipped_entries.append(f"Duplicate check-in skipped for {employee_id} at {checkin_time}")
                continue  

            checkin_doc = frappe.get_doc({
                "doctype": "Employee Checkin",
                "employee": employee,
                "time": checkin_time,
                "log_type": in_out,
            })
            checkin_doc.insert(ignore_permissions=True)
            created_entries.append(f"Check-in added for {employee_id} at {checkin_time}")

        frappe.db.commit()

        response = {
            "message": "Employee Checkin data uploaded successfully",
            "file_url": file_doc.file_url,
            "created_entries": created_entries
        }

        if skipped_entries:
            response["skipped_entries"] = skipped_entries  

        return response

    except Exception as e:
        frappe.log_error(f"Excel upload error: {str(e)[:100]}")
        return {"error": "Internal Server Error", "details": str(e)[:100]}
