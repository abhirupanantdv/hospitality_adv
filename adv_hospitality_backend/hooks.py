app_name = "adv_hospitality_backend"
app_title = "ADV Hospitality Backend"
app_publisher = "ADV Hospitality Suite"
app_description = "Backend DocTypes and APIs for ADV Hospitality Suite."
app_email = "admin@example.com"
app_license = "MIT"

after_install = "adv_hospitality_backend.install.after_install"
before_uninstall = "adv_hospitality_backend.install.before_uninstall"

fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Hotel Operations Manager", "Front Desk Agent", "Housekeeping Supervisor", "Security Operator"]]]},
]

doc_events = {
    "ADV Guest Message": {
        "after_insert": "adv_hospitality_backend.api.create_task_from_guest_message"
    }
}

