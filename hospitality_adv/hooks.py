app_name = "hospitality_adv"
app_title = "Hospitality ADV"
app_publisher = "Hospitality ADV"
app_description = "Backend DocTypes and APIs for Hospitality ADV."
app_email = "admin@example.com"
app_license = "MIT"

fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Hotel Operations Manager", "Front Desk Agent", "Housekeeping Supervisor", "Security Operator"]]]},
]

doc_events = {
    "Hospitality ADV Guest Message": {
        "after_insert": "hospitality_adv.api.create_task_from_guest_message"
    }
}
