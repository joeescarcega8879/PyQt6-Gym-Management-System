class MainPresenter:
    def __init__(self, view, main_app, current_user):
        self.view = view
        self.main_app = main_app
        self.current_user = current_user
        
        self._connect_signals()
        
    def _connect_signals(self):
        self.view.form_members_requested.connect(self.main_app.open_members_form)