# from odoo import models, fields
# from odoo.exceptions import UserError
# class ReceptionLogin(models.TransientModel):
#     _name = 'reception.login'
#     _description = 'Reception Login Form'
#
#     email = fields.Char(string='Email', required=True)
#     password = fields.Char(string='Password', required=True)
#
#     def action_redirect_reception(self):
#         if self.email == "com" and self.password == "123":
#             # Redirect to Reception Dashboard via menu-bound action
#             menu = self.env.ref('hospital_management_system.reception_home', raise_if_not_found=False)
#
#             if menu:
#                 return {
#                     'type': 'ir.actions.client',
#                     'tag': 'reload',  # Force menu to reload correctly
#                     'params': {'menu_id': menu.id},
#                 }
#             else:
#                 return {'type': 'ir.actions.act_window_close'}
#         else:
#             raise UserError('Invalid credentials!')
#
