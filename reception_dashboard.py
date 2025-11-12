from odoo import models

class ReceptionDashboard(models.TransientModel):
    _name = 'reception.dashboard'
    _description = 'Reception Dashboard'
    def open_patient_registration(self):
        return self.env.ref('hospital_management_system.action_patient').read()[0]

    def open_vital_signs(self):
        return self.env.ref('hospital_management_system.action_vital_sign').read()[0]

    def open_appointments(self):
        return self.env.ref('hospital_management_system.action_appointment').read()[0]
