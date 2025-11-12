from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource
import base64


class HospitalICUBed(models.Model):
    _name = 'hospital.icu.bed'
    _description = 'ICU Bed'
    _order = 'name'







    patient_id = fields.Many2one('hospital.patient', string="Assigned Patient")
    assigned_date = fields.Datetime(string="Assigned Date")

    def _get_default_image(self):
        image_path = get_module_resource('hospital_management_system', 'static/description', 'bed1.png')
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read())

    @api.depends('status')
    def _compute_availability(self):
        for bed in self:
            bed.is_available = bed.status == 'available'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = vals.get('name')
            if not name or name.isnumeric():
                raise ValidationError("Invalid ICU Bed name. Please use names like 'ICU Bed A1'.")
            if self.env['hospital.icu.bed'].search([('name', '=', name)]):
                raise ValidationError(f"ICU Bed with name '{name}' already exists.")
        return super().create(vals_list)

    def unlink(self):
        for bed in self:
            if bed.status == 'booked':
                raise ValidationError("You cannot delete a bed that is marked as 'Booked'.")
        return super().unlink()

    def action_save_icu_bed_save(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'ICU Bed',
            'res_model': 'hospital.icu.bed',
            'view_mode': 'kanban,list,form',
            'target': 'current',
        }
