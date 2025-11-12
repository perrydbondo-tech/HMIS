import re
from datetime import date, timedelta, datetime
from pytz import timezone, UTC

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Patient(models.Model):
    _name = 'hospital.patient'
    _description = 'Hospital Management'

    patient_id = fields.Char(string="Patient ID", required=True, copy=False, readonly=True, default='New')
    date_of_birth = fields.Date(string='Date of Birth')
    registration_date = fields.Datetime(string='Registration Date')  # Timezone-sensitive
    name = fields.Char(string="Name", required=True)

    state_id = fields.Many2one(
        'res.country.state',
        string="State",
        domain="[('country_id.code', '=', 'IN')]"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('admitted', 'Admitted'),
        ('discharged', 'Discharged')
    ], string="Status", default='draft')

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others')
    ], string='Gender')

    age = fields.Char(string='Age', compute='_compute_age_display')
    contact_number = fields.Char(string="Contact Number", size=10)

    blood_group = fields.Selection([
        ('a+', 'A+'),
        ('a-', 'A-'),
        ('b+', 'B+'),
        ('b-', 'B-'),
        ('ab+', 'AB+'),
        ('ab-', 'AB-'),
        ('o+', 'O+'),
        ('o-', 'O-'),
    ], string='Blood Group')

    martial_statu = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorce', 'Divorce')
    ])
    address = fields.Text(string="Address")
    case_description = fields.Text(string='Case Description')

    registration_day_label = fields.Char(
        string="Registration Day",
        compute="_compute_registration_day_label",
        store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        contact_number = vals_list.get('contact_number')
        if contact_number:
            existing_patient = self.env['hospital.patient'].sudo().search([
                ('contact_number', '=', contact_number)
            ], limit=1)
            if existing_patient:
                raise ValidationError(
                    f"A patient with contact number {contact_number} already exists: {existing_patient.name}.")

        if not vals_list.get('registration_date'):
            vals_list['registration_date'] = fields.Datetime.now()

        sequence = self.env['ir.sequence'].sudo().search([('code', '=', 'hospital.patient')], limit=1)
        if not sequence:
            sequence = self.env['ir.sequence'].sudo().create({
                'name': 'Patient ID',
                'code': 'hospital.patient',
                'prefix': 'PAT',
                'padding': 4,
                'number_next': 1,
                'number_increment': 1,
            })

        if not self.env['hospital.patient'].sudo().search([]):
            sequence.number_next = 1

        if vals_list.get('patient_id', 'New') == 'New':
            vals_list['patient_id'] = self.env['ir.sequence'].next_by_code('hospital.patient') or 'New'

        return super(Patient, self).create(vals_list)

    @api.depends('date_of_birth')
    def _compute_age_display(self):
        for record in self:
            if record.date_of_birth:
                today = date.today()
                dob = record.date_of_birth

                if dob <= today:
                    delta_years = today.year - dob.year
                    delta_months = today.month - dob.month
                    delta_days = today.day - dob.day

                    if delta_days < 0:
                        delta_months -= 1
                        prev_month = (today.month - 1) or 12
                        prev_month_year = today.year if today.month != 1 else today.year - 1
                        days_in_prev_month = (
                            date(prev_month_year, prev_month + 1, 1) - date(prev_month_year, prev_month, 1)
                        ).days
                        delta_days += days_in_prev_month

                    if delta_months < 0:
                        delta_years -= 1
                        delta_months += 12

                    record.age = f"{delta_years} year(s), {delta_months} month(s), {delta_days} day(s) old"
                else:
                    delta = dob - today
                    record.age = f"Will be born in {delta.days} day(s)"
            else:
                record.age = "Date of birth not set"

    # @api.depends('registration_date')
    # def _compute_registration_day_label(self):
    #     for rec in self:
    #         if rec.registration_date:
    #             local_dt = fields.Datetime.context_timestamp(rec, rec.registration_date)
    #             local_date = local_dt.date()
    #             user_today = fields.Datetime.context_timestamp(rec, fields.Datetime.now()).date()
    #             user_yesterday = user_today - timedelta(days=1)

    #             if local_date == user_today:
    #                 rec.registration_day_label = "Today"
    #             elif local_date == user_yesterday:
    #                 rec.registration_day_label = "Yesterday"
    #             else:
    #                 rec.registration_day_label = local_date.strftime("%b %d, %Y")
    #         else:
    #             rec.registration_day_label = "Unknown"

    # def get_registrations_within_date_range_tz_aware(self, start_date_local, end_date_local):
    #     """Returns registrations within user's local date range, converted to UTC."""
    #     user_tz = self.env.user.tz or 'UTC'
    #     tz = timezone(user_tz)

    #     start_localized = tz.localize(start_date_local).astimezone(UTC)
    #     end_localized = tz.localize(end_date_local).astimezone(UTC)

    #     domain = [
    #         ('registration_date', '>=', start_localized),
    #         ('registration_date', '<=', end_localized)
    #     ]
    #     return self.search(domain)

    def action_save_patient(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patients',
            'res_model': 'hospital.patient',
            'view_mode': 'list,form',
            'target': 'current',
        }
