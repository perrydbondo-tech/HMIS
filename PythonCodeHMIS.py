# Odoo Python Tutorial for HMIS (Hospital Management Information System)


## 1. HMIS Core Models Structure

### Patient Management Model

```python
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class HMISPatient(models.Model):
    _name = 'hmis.patient'
    _description = 'Hospital Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Personal Information
    name = fields.Char(string='Patient Name', required=True, tracking=True)
    patient_id = fields.Char(string='Patient ID', required=True, copy=False, readonly=True, 
                           default=lambda self: self._generate_patient_id())
    date_of_birth = fields.Date(string='Date of Birth', required=True, tracking=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', required=True, tracking=True)
    blood_type = fields.Selection([
        ('a_positive', 'A+'),
        ('a_negative', 'A-'),
        ('b_positive', 'B+'),
        ('b_negative', 'B-'),
        ('ab_positive', 'AB+'),
        ('ab_negative', 'AB-'),
        ('o_positive', 'O+'),
        ('o_negative', 'O-')
    ], string='Blood Type', tracking=True)
    
    # Contact Information
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    emergency_contact = fields.Char(string='Emergency Contact')
    emergency_phone = fields.Char(string='Emergency Phone')
    
    # Medical Information
    medical_history = fields.Text(string='Medical History')
    allergies = fields.Text(string='Allergies')
    current_medications = fields.Text(string='Current Medications')
    insurance_id = fields.Char(string='Insurance ID')
    insurance_provider = fields.Char(string='Insurance Provider')
    
    # Status
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('deceased', 'Deceased')
    ], string='Status', default='active', tracking=True)
    
    # Relationships
    appointment_ids = fields.One2many('hmis.appointment', 'patient_id', string='Appointments')
    admission_ids = fields.One2many('hmis.admission', 'patient_id', string='Admissions')
    prescription_ids = fields.One2many('hmis.prescription', 'patient_id', string='Prescriptions')
    
    # Computed fields
    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.today()
        for patient in self:
            if patient.date_of_birth:
                delta = today - patient.date_of_birth
                patient.age = delta.days // 365
            else:
                patient.age = 0
    
    # Constraints
    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for patient in self:
            if patient.date_of_birth > fields.Date.today():
                raise ValidationError("Date of birth cannot be in the future!")
    
    # Sequence generation
    @api.model
    def _generate_patient_id(self):
        sequence = self.env['ir.sequence'].next_by_code('hmis.patient.id') or 'NEW'
        return sequence
```

### Appointment Management Model

```python
class HMISAppointment(models.Model):
    _name = 'hmis.appointment'
    _description = 'Medical Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date desc'
    
    name = fields.Char(string='Appointment Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: 'New')
    patient_id = fields.Many2one('hmis.patient', string='Patient', required=True, tracking=True)
    doctor_id = fields.Many2one('hr.employee', string='Doctor', required=True, 
                               domain=[('is_doctor', '=', True)])
    appointment_date = fields.Datetime(string='Appointment Date', required=True, tracking=True)
    appointment_end = fields.Datetime(string='Appointment End', compute='_compute_appointment_end', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='doctor_id.department_id')
    reason = fields.Text(string='Reason for Visit', required=True)
    symptoms = fields.Text(string='Symptoms')
    diagnosis = fields.Text(string='Diagnosis')
    notes = fields.Text(string='Doctor Notes')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_consultation', 'In Consultation'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    priority = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency')
    ], string='Priority', default='normal')
    
    duration = fields.Float(string='Duration (hours)', default=0.5)
    
    # Computed fields
    @api.depends('appointment_date', 'duration')
    def _compute_appointment_end(self):
        for appointment in self:
            if appointment.appointment_date and appointment.duration:
                start_time = fields.Datetime.from_string(appointment.appointment_date)
                end_time = start_time + timedelta(hours=appointment.duration)
                appointment.appointment_end = end_time
            else:
                appointment.appointment_end = False
    
    # Override create to generate sequence
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hmis.appointment') or 'New'
        return super().create(vals)
    
    # Action methods
    def action_confirm(self):
        for appointment in self:
            if appointment.state == 'draft':
                appointment.state = 'confirmed'
                # Send confirmation notification
                appointment._send_appointment_confirmation()
    
    def action_start_consultation(self):
        for appointment in self:
            if appointment.state == 'confirmed':
                appointment.state = 'in_consultation'
    
    def action_complete(self):
        for appointment in self:
            if appointment.state == 'in_consultation':
                appointment.state = 'done'
                # Create medical record
                self._create_medical_record()
    
    def action_cancel(self):
        for appointment in self:
            if appointment.state in ['draft', 'confirmed']:
                appointment.state = 'cancelled'
    
    # Notification methods
    def _send_appointment_confirmation(self):
        """Send appointment confirmation to patient"""
        try:
            template = self.env.ref('hmis.email_template_appointment_confirmation')
            for appointment in self:
                template.send_mail(appointment.id, force_send=False)
        except Exception as e:
            _logger.error(f"Failed to send appointment confirmation: {str(e)}")
    
    def _create_medical_record(self):
        """Create medical record after consultation"""
        medical_record_model = self.env['hmis.medical.record']
        for appointment in self:
            medical_record_model.create({
                'patient_id': appointment.patient_id.id,
                'appointment_id': appointment.id,
                'doctor_id': appointment.doctor_id.id,
                'visit_date': appointment.appointment_date,
                'symptoms': appointment.symptoms,
                'diagnosis': appointment.diagnosis,
                'notes': appointment.notes,
            })
```

## 2. HMIS Server Actions

### Automated Patient Registration Server Action

```python
# Server Action: Auto Register Patient from Web Form
def auto_register_patient(records):
    """
    Server action to automatically register new patients
    """
    Patient = env['hmis.patient']
    
    for record in records:
        try:
            # Validate required fields
            if not record.get('name') or not record.get('date_of_birth'):
                raise UserError("Name and Date of Birth are required")
            
            # Create patient record
            patient_vals = {
                'name': record.get('name'),
                'date_of_birth': record.get('date_of_birth'),
                'gender': record.get('gender', 'other'),
                'phone': record.get('phone'),
                'email': record.get('email'),
                'address': record.get('address'),
                'medical_history': record.get('medical_history'),
                'allergies': record.get('allergies'),
            }
            
            patient = Patient.create(patient_vals)
            
            # Create welcome activity
            patient.activity_schedule(
                act_type_xmlid='mail.mail_activity_data_todo',
                summary=f'Welcome {patient.name}',
                note=f'New patient registered. Patient ID: {patient.patient_id}',
                user_id=env.uid
            )
            
            # Return success with patient info
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Patient Registered',
                    'message': f'Patient {patient.name} registered successfully with ID: {patient.patient_id}',
                    'type': 'success',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            # Return error message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Registration Failed',
                    'message': f'Failed to register patient: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
```

### Appointment Management Server Action

```python
# Server Action: Bulk Confirm Appointments
def bulk_confirm_appointments(records):
    """
    Server action to confirm multiple appointments and send notifications
    """
    try:
        confirmed_count = 0
        for appointment in records:
            if appointment.state == 'draft':
                # Confirm appointment
                appointment.action_confirm()
                
                # Schedule reminder activity
                appointment_date = fields.Datetime.from_string(appointment.appointment_date)
                reminder_date = appointment_date - timedelta(days=1)
                
                appointment.activity_schedule(
                    'mail.mail_activity_data_todo',
                    appointment.appointment_date,
                    summary=f'Appointment Reminder: {appointment.patient_id.name}',
                    note=f'Appointment with {appointment.patient_id.name} at {appointment.appointment_date}',
                    user_id=appointment.doctor_id.user_id.id
                )
                
                confirmed_count += 1
        
        # Return summary
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Appointments Confirmed',
                'message': f'Successfully confirmed {confirmed_count} appointments',
                'type': 'success',
                'sticky': False,
            }
        }
        
    except Exception as e:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Confirmation Failed',
                'message': f'Error: {str(e)}',
                'type': 'danger',
                'sticky': True,
            }
        }
```

## 3. HMIS Automated Actions (Scheduled)

### Automated Patient Follow-up System

```python
class HMISAutomatedTasks(models.Model):
    _name = 'hmis.automated.tasks'
    _description = 'HMIS Automated Tasks'
    
    def auto_follow_up_patients(self):
        """
        Automated action: Follow up with patients who had appointments 7 days ago
        """
        try:
            follow_up_date = fields.Datetime.now() - timedelta(days=7)
            
            # Find completed appointments from 7 days ago
            appointments = self.env['hmis.appointment'].search([
                ('state', '=', 'done'),
                ('appointment_date', '>=', follow_up_date - timedelta(days=1)),
                ('appointment_date', '<=', follow_up_date),
                ('patient_id.status', '=', 'active')
            ])
            
            follow_up_count = 0
            for appointment in appointments:
                # Create follow-up activity
                appointment.patient_id.activity_schedule(
                    'mail.mail_activity_data_call',
                    summary='Patient Follow-up',
                    note=f'Follow up with {appointment.patient_id.name} regarding appointment on {appointment.appointment_date}',
                    user_id=appointment.doctor_id.user_id.id
                )
                follow_up_count += 1
            
            _logger.info(f"Created {follow_up_count} patient follow-up activities")
            return follow_up_count
            
        except Exception as e:
            _logger.error(f"Auto follow-up failed: {str(e)}")
            return 0
    
    def auto_generate_monthly_reports(self):
        """
        Automated action: Generate monthly HMIS reports
        """
        try:
            # Calculate date range for last month
            today = fields.Date.today()
            first_day_last_month = today.replace(day=1) - timedelta(days=1)
            first_day_last_month = first_day_last_month.replace(day=1)
            last_day_last_month = today.replace(day=1) - timedelta(days=1)
            
            report_data = {
                'period': f"{first_day_last_month.strftime('%B %Y')}",
                'total_patients': self.env['hmis.patient'].search_count([]),
                'new_patients': self.env['hmis.patient'].search_count([
                    ('create_date', '>=', first_day_last_month),
                    ('create_date', '<=', last_day_last_month)
                ]),
                'total_appointments': self.env['hmis.appointment'].search_count([
                    ('appointment_date', '>=', first_day_last_month),
                    ('appointment_date', '<=', last_day_last_month)
                ]),
                'completed_appointments': self.env['hmis.appointment'].search_count([
                    ('state', '=', 'done'),
                    ('appointment_date', '>=', first_day_last_month),
                    ('appointment_date', '<=', last_day_last_month)
                ]),
            }
            
            # Log report data
            _logger.info(f"Monthly HMIS Report: {report_data}")
            
            # Create activity for hospital administrator
            admin_group = self.env.ref('hmis.group_hospital_admin')
            admin_users = self.env['res.users'].search([('groups_id', 'in', admin_group.ids)])
            
            for user in admin_users:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': f"Monthly HMIS Report - {report_data['period']}",
                    'note': f"""
                    Monthly Hospital Statistics:
                    - Total Patients: {report_data['total_patients']}
                    - New Patients: {report_data['new_patients']}
                    - Total Appointments: {report_data['total_appointments']}
                    - Completed Appointments: {report_data['completed_appointments']}
                    """,
                    'user_id': user.id,
                    'date_deadline': fields.Date.today()
                })
            
            return report_data
            
        except Exception as e:
            _logger.error(f"Monthly report generation failed: {str(e)}")
            return {}
```

## 4. Pharmacy and Prescription Management

```python
class HMISPrescription(models.Model):
    _name = 'hmis.prescription'
    _description = 'Medical Prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Prescription ID', required=True, readonly=True, default='New')
    patient_id = fields.Many2one('hmis.patient', string='Patient', required=True)
    doctor_id = fields.Many2one('hr.employee', string='Prescribing Doctor', required=True)
    appointment_id = fields.Many2one('hmis.appointment', string='Related Appointment')
    prescription_date = fields.Datetime(string='Prescription Date', default=fields.Datetime.now)
    
    prescription_line_ids = fields.One2many('hmis.prescription.line', 'prescription_id', string='Medicines')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('dispensed', 'Dispensed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    notes = fields.Text(string='Doctor Instructions')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hmis.prescription') or 'New'
        return super().create(vals)
    
    def action_confirm_prescription(self):
        """Confirm prescription and check drug availability"""
        for prescription in self:
            # Check stock availability for all medicines
            for line in prescription.prescription_line_ids:
                if line.medicine_id.qty_available < line.quantity:
                    raise UserError(
                        f"Insufficient stock for {line.medicine_id.name}. "
                        f"Available: {line.medicine_id.qty_available}, Required: {line.quantity}"
                    )
            
            prescription.state = 'confirmed'
    
    def action_dispense_medicines(self):
        """Dispense medicines and update inventory"""
        for prescription in self:
            if prescription.state == 'confirmed':
                # Update stock for each medicine
                for line in prescription.prescription_line_ids:
                    line.medicine_id.qty_available -= line.quantity
                
                prescription.state = 'dispensed'

class HMISPrescriptionLine(models.Model):
    _name = 'hmis.prescription.line'
    _description = 'Prescription Line'
    
    prescription_id = fields.Many2one('hmis.prescription', string='Prescription')
    medicine_id = fields.Many2one('hmis.medicine', string='Medicine', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    dosage = fields.Char(string='Dosage Instructions')
    duration = fields.Char(string='Duration')
    notes = fields.Char(string='Notes')
```

## 5. Emergency Room Management

```python
class HMISEmergency(models.Model):
    _name = 'hmis.emergency'
    _description = 'Emergency Room Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Emergency Case ID', readonly=True, default='New')
    patient_id = fields.Many2one('hmis.patient', string='Patient', required=True)
    triage_level = fields.Selection([
        ('resuscitation', 'Resuscitation (Immediate)'),
        ('emergent', 'Emergent (< 15 mins)'),
        ('urgent', 'Urgent (< 60 mins)'),
        ('less_urgent', 'Less Urgent (< 120 mins)'),
        ('non_urgent', 'Non Urgent (> 120 mins)')
    ], string='Triage Level', required=True)
    
    chief_complaint = fields.Text(string='Chief Complaint', required=True)
    vital_signs = fields.Text(string='Vital Signs')
    initial_assessment = fields.Text(string='Initial Assessment')
    treatment_given = fields.Text(string='Treatment Given')
    
    assigned_doctor_id = fields.Many2one('hr.employee', string='Assigned Doctor')
    nurse_id = fields.Many2one('hr.employee', string='Attending Nurse')
    
    arrival_time = fields.Datetime(string='Arrival Time', default=fields.Datetime.now)
    treatment_start_time = fields.Datetime(string='Treatment Start Time')
    discharge_time = fields.Datetime(string='Discharge Time')
    
    state = fields.Selection([
        ('arrived', 'Arrived'),
        ('triaged', 'Triaged'),
        ('in_treatment', 'In Treatment'),
        ('admitted', 'Admitted to Ward'),
        ('discharged', 'Discharged'),
        ('transferred', 'Transferred')
    ], string='Status', default='arrived')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hmis.emergency') or 'New'
        return super().create(vals)
    
    def action_start_treatment(self):
        """Start treatment and notify relevant staff"""
        for emergency in self:
            emergency.write({
                'state': 'in_treatment',
                'treatment_start_time': fields.Datetime.now()
            })
            
            # Notify assigned doctor
            if emergency.assigned_doctor_id.user_id:
                emergency.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=f'Emergency Case: {emergency.patient_id.name}',
                    note=f'Patient requires immediate attention. Triage Level: {emergency.triage_level}',
                    user_id=emergency.assigned_doctor_id.user_id.id
                )
```

## 6. HMIS Reporting and Analytics

```python
class HMISReporting(models.Model):
    _name = 'hmis.reporting'
    _description = 'HMIS Reporting and Analytics'
    
    def get_daily_census_report(self):
        """Generate daily hospital census report"""
        current_date = fields.Date.today()
        
        report_data = {
            'report_date': current_date,
            'total_patients': self.env['hmis.patient'].search_count([]),
            'active_appointments': self.env['hmis.appointment'].search_count([
                ('appointment_date', '>=', current_date),
                ('appointment_date', '<', current_date + timedelta(days=1)),
                ('state', 'in', ['confirmed', 'in_consultation'])
            ]),
            'emergency_cases': self.env['hmis.emergency'].search_count([
                ('arrival_time', '>=', current_date),
                ('arrival_time', '<', current_date + timedelta(days=1))
            ]),
            'new_prescriptions': self.env['hmis.prescription'].search_count([
                ('prescription_date', '>=', current_date),
                ('prescription_date', '<', current_date + timedelta(days=1))
            ]),
        }
        
        return report_data
    
    def get_doctor_performance_report(self, start_date, end_date):
        """Generate doctor performance report"""
        doctors = self.env['hr.employee'].search([('is_doctor', '=', True)])
        
        performance_data = []
        for doctor in doctors:
            appointments = self.env['hmis.appointment'].search([
                ('doctor_id', '=', doctor.id),
                ('appointment_date', '>=', start_date),
                ('appointment_date', '<=', end_date)
            ])
            
            completed_appointments = appointments.filtered(lambda a: a.state == 'done')
            
            performance_data.append({
                'doctor_name': doctor.name,
                'department': doctor.department_id.name if doctor.department_id else 'N/A',
                'total_appointments': len(appointments),
                'completed_appointments': len(completed_appointments),
                'completion_rate': (len(completed_appointments) / len(appointments)) * 100 if appointments else 0,
                'average_duration': sum(appointment.duration for appointment in completed_appointments) / len(completed_appointments) if completed_appointments else 0
            })
        
        return performance_data
```

## 7. HMIS Security and Access Control

```python
class HMISCustomSecurity(models.Model):
    _inherit = 'res.users'
    
    def check_hmis_access_rights(self, model_name, operation='read'):
        """
        Custom access control for HMIS modules
        """
        # Define role-based access matrix
        access_matrix = {
            'hmis.patient': {
                'receptionist': ['read', 'create'],
                'nurse': ['read', 'write'],
                'doctor': ['read', 'write', 'create'],
                'admin': ['read', 'write', 'create', 'unlink']
            },
            'hmis.prescription': {
                'doctor': ['read', 'write', 'create'],
                'pharmacist': ['read', 'write'],
                'admin': ['read', 'write', 'create', 'unlink']
            }
        }
        
        user_groups = self.groups_id.mapped('name')
        model_access = access_matrix.get(model_name, {})
        
        for group in user_groups:
            if group in model_access and operation in model_access[group]:
                return True
        


