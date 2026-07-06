class MainPresenter:
    def __init__(self, view, main_app, current_user):
        self.view = view
        self.main_app = main_app
        self.current_user = current_user
        
        self._connect_signals()
        
    def _connect_signals(self):
        self.view.form_dashboard_requested.connect(self.main_app.open_dashboard_form)
        self.view.form_members_requested.connect(self.main_app.open_members_form)
        self.view.form_attendance_requested.connect(self.main_app.open_attendance_form)
        self.view.form_payments_requested.connect(self.main_app.open_payments_form)
        self.view.form_memberships_requested.connect(self.main_app.open_memberships_form)
        self.view.form_classes_requested.connect(self.main_app.open_classes_form)
        self.view.form_settings_requested.connect(self.main_app.open_settings_form)
        self.view.form_instructors_requested.connect(self.main_app.open_instructors_form)
        self.view.form_equipment_requested.connect(self.main_app.open_equipment_form)
        self.view.form_reports_requested.connect(self.main_app.open_reports_form)
        self.view.logout_requested.connect(self.main_app.logout)