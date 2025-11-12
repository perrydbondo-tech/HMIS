from odoo import models, fields

class HospitalVitalSign(models.Model):
    _name = 'hospital.vital.sign'
    _description = 'Vital Sign Record'

    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True)
    date = fields.Date(string="Date", default=fields.Date.today)
    temperature = fields.Float(string="Temperature (°C)")
    pulse = fields.Integer(string="Pulse")
    respiration_rate = fields.Integer(string="Respiration Rate")
    blood_pressure = fields.Char(string="Blood Pressure")

    def action_save_vital(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patient Vitals',
            'res_model': 'hospital.vital.sign',
            'view_mode': 'list,form',
            'target': 'current',
        }
