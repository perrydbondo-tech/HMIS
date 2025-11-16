# Odoo Python Tutorial: Building Employee App from Scratch


## 1. Employee App Foundation

### Basic Employee Model Extension

```python
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class CustomEmployee(models.Model):
    _name = 'custom.employee'
    _description = 'Custom Employee Management'
    _inherit = ['hr.employee', 'mail.thread', 'mail.activity.mixin']
    
    # Additional Fields
    employee_code = fields.Char(string='Employee ID', required=True, copy=False, readonly=True,
                              default=lambda self: self._generate_employee_code())
    nickname = fields.Char(string='Preferred Name')
    personal_email = fields.Char(string='Personal Email')
    emergency_contact_name = fields.Char(string='Emergency Contact Name')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')
    emergency_contact_relation = fields.Char(string='Relationship')
    
    # Employment Details
    employment_type = fields.Selection([
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
        ('probation', 'Probation')
    ], string='Employment Type', default='full_time', tracking=True)
    
    probation_end_date = fields.Date(string='Probation End Date')
    notice_period = fields.Integer(string='Notice Period (Days)', default=30)
    retirement_date = fields.Date(string='Planned Retirement Date', compute='_compute_retirement_date', store=True)
    
    # Skills and Qualifications
    skills_ids = fields.Many2many('employee.skill', string='Skills')
    certifications = fields.Text(string='Certifications')
    languages = fields.Text(string='Languages Spoken')
    
    # Equipment and Assets
    assigned_equipment_ids = fields.One2many('employee.equipment', 'employee_id', string='Assigned Equipment')
    
    # Computed Fields
    @api.depends('birthday')
    def _compute_retirement_date(self):
        for employee in self:
            if employee.birthday:
                retirement_age = 65  # Default retirement age
                retirement_date = employee.birthday.replace(year=employee.birthday.year + retirement_age)
                employee.retirement_date = retirement_date
            else:
                employee.retirement_date = False
    
    # Constraints
    @api.constrains('probation_end_date')
    def _check_probation_end_date(self):
        for employee in self:
            if employee.probation_end_date and employee.probation_end_date < fields.Date.today():
                raise ValidationError("Probation end date cannot be in the past!")
    
    # Sequence Generation
    @api.model
    def _generate_employee_code(self):
        sequence = self.env['ir.sequence'].next_by_code('custom.employee.code') or 'EMP'
        return sequence
    
    # Override Create Method
    @api.model
    def create(self, vals):
        if vals.get('employee_code', 'New') == 'New':
            vals['employee_code'] = self.env['ir.sequence'].next_by_code('custom.employee.code') or 'New'
        
        # Set work email if not provided
        if not vals.get('work_email') and vals.get('personal_email'):
            vals['work_email'] = vals['personal_email']
        
        employee = super().create(vals)
        
        # Create welcome activity
        employee.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=f'Welcome {employee.name}',
            note=f'New employee onboarding process started for {employee.name}',
            user_id=employee.parent_id.user_id.id if employee.parent_id else self.env.user.id
        )
        
        return employee
    
    # Action Methods
    def action_send_welcome_email(self):
        """Send welcome email to new employee"""
        self.ensure_one()
        template = self.env.ref('employee_app.email_template_employee_welcome')
        template.send_mail(self.id, force_send=False)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Welcome Email Sent',
                'message': f'Welcome email sent to {self.name}',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_view_equipment(self):
        """View assigned equipment"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.name} - Assigned Equipment',
            'res_model': 'employee.equipment',
            'domain': [('employee_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_employee_id': self.id}
        }
```

## 2. Employee Skills and Competencies Model

```python
class EmployeeSkill(models.Model):
    _name = 'employee.skill'
    _description = 'Employee Skills'
    
    name = fields.Char(string='Skill Name', required=True)
    category = fields.Selection([
        ('technical', 'Technical'),
        ('soft', 'Soft Skills'),
        ('language', 'Language'),
        ('certification', 'Certification')
    ], string='Category', required=True)
    level = fields.Selection([
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ], string='Proficiency Level')
    description = fields.Text(string='Description')

class EmployeeSkillRecord(models.Model):
    _name = 'employee.skill.record'
    _description = 'Employee Skill Records'
    
    employee_id = fields.Many2one('custom.employee', string='Employee', required=True)
    skill_id = fields.Many2one('employee.skill', string='Skill', required=True)
    proficiency_level = fields.Selection([
        ('1', 'Basic Awareness'),
        ('2', 'Novice'),
        ('3', 'Intermediate'),
        ('4', 'Advanced'),
        ('5', 'Expert')
    ], string='Proficiency Level', required=True)
    date_acquired = fields.Date(string='Date Acquired')
    certified = fields.Boolean(string='Certified')
    certification_date = fields.Date(string='Certification Date')
    verified_by = fields.Many2one('custom.employee', string='Verified By')
    
    # Computed field
    skill_score = fields.Integer(string='Skill Score', compute='_compute_skill_score')
    
    @api.depends('proficiency_level')
    def _compute_skill_score(self):
        for record in self:
            record.skill_score = int(record.proficiency_level) * 20
```

## 3. Equipment and Asset Management

```python
class EmployeeEquipment(models.Model):
    _name = 'employee.equipment'
    _description = 'Employee Equipment Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Equipment Name', required=True)
    equipment_code = fields.Char(string='Asset ID', required=True, copy=False, readonly=True,
                               default=lambda self: 'New')
    employee_id = fields.Many2one('custom.employee', string='Assigned To', required=True, tracking=True)
    category = fields.Selection([
        ('laptop', 'Laptop'),
        ('mobile', 'Mobile Phone'),
        ('tablet', 'Tablet'),
        ('monitor', 'Monitor'),
        ('accessory', 'Accessory'),
        ('other', 'Other')
    ], string='Category', required=True)
    
    # Equipment Details
    brand = fields.Char(string='Brand')
    model = fields.Char(string='Model')
    serial_number = fields.Char(string='Serial Number')
    purchase_date = fields.Date(string='Purchase Date')
    warranty_end_date = fields.Date(string='Warranty End Date')
    purchase_cost = fields.Float(string='Purchase Cost')
    
    # Assignment Details
    assignment_date = fields.Date(string='Assignment Date', default=fields.Date.today)
    expected_return_date = fields.Date(string='Expected Return Date')
    actual_return_date = fields.Date(string='Actual Return Date')
    
    # Status
    state = fields.Selection([
        ('assigned', 'Assigned'),
        ('returned', 'Returned'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged')
    ], string='Status', default='assigned', tracking=True)
    
    condition_notes = fields.Text(string='Condition Notes')
    
    @api.model
    def create(self, vals):
        if vals.get('equipment_code', 'New') == 'New':
            vals['equipment_code'] = self.env['ir.sequence'].next_by_code('employee.equipment.code') or 'New'
        return super().create(vals)
    
    def action_return_equipment(self):
        """Mark equipment as returned"""
        for equipment in self:
            equipment.write({
                'state': 'returned',
                'actual_return_date': fields.Date.today()
            })
            
            # Notify IT department
            equipment.message_post(
                body=f"Equipment {equipment.name} returned by {equipment.employee_id.name}",
                subject="Equipment Returned"
            )
    
    def action_send_maintenance_alert(self):
        """Send maintenance alert for equipment"""
        for equipment in self:
            if equipment.warranty_end_date and equipment.warranty_end_date < fields.Date.today():
                equipment.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary='Equipment Maintenance Required',
                    note=f'Equipment {equipment.name} warranty has expired. Schedule maintenance.',
                    user_id=self.env.user.id
                )
```

## 4. Server Actions for Employee Management

### Automated Onboarding Server Action

```python
# Server Action: Employee Onboarding Process
def employee_onboarding_process(records):
    """
    Automated onboarding process for new employees
    """
    try:
        for employee in records:
            # Create equipment assignment request
            equipment_vals = {
                'employee_id': employee.id,
                'name': 'Standard Laptop Setup',
                'category': 'laptop',
                'assignment_date': fields.Date.today(),
                'state': 'assigned'
            }
            env['employee.equipment'].create(equipment_vals)
            
            # Create onboarding checklist
            checklist_items = [
                'HR Documentation',
                'System Access Setup',
                'Email Configuration',
                'Security Training',
                'Team Introduction'
            ]
            
            for item in checklist_items:
                employee.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=f'Onboarding: {item}',
                    note=f'Complete {item} for {employee.name}',
                    user_id=employee.department_id.manager_id.user_id.id if employee.department_id.manager_id else env.user.id
                )
            
            # Send welcome package notification
            employee.message_post(
                body=f"""
                <p>Welcome to the team, {employee.name}!</p>
                <p>Your onboarding process has been initiated.</p>
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Complete HR documentation</li>
                    <li>Attend orientation session</li>
                    <li>Meet with your manager</li>
                    <li>Set up your workstation</li>
                </ul>
                """,
                subject=f"Welcome to the Company - {employee.name}"
            )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Onboarding Initiated',
                'message': f'Onboarding process started for {len(records)} employees',
                'type': 'success',
                'sticky': False,
            }
        }
        
    except Exception as e:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Onboarding Failed',
                'message': f'Error: {str(e)}',
                'type': 'danger',
                'sticky': True,
            }
        }
```

### Bulk Equipment Assignment Server Action

```python
# Server Action: Bulk Equipment Assignment
def bulk_equipment_assignment(records):
    """
    Assign standard equipment package to multiple employees
    """
    try:
        Equipment = env['employee.equipment']
        assigned_count = 0
        
        standard_equipment = [
            {'name': 'Dell Laptop', 'category': 'laptop'},
            {'name': '24-inch Monitor', 'category': 'monitor'},
            {'name': 'Wireless Keyboard/Mouse', 'category': 'accessory'},
            {'name': 'Company Mobile', 'category': 'mobile'}
        ]
        
        for employee in records:
            for item in standard_equipment:
                equipment_vals = {
                    'employee_id': employee.id,
                    'name': item['name'],
                    'category': item['category'],
                    'assignment_date': fields.Date.today(),
                    'state': 'assigned'
                }
                Equipment.create(equipment_vals)
                assigned_count += 1
            
            # Notify employee
            employee.message_post(
                body="Standard equipment package has been assigned to you.",
                subject="Equipment Assignment"
            )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Equipment Assigned',
                'message': f'Assigned {assigned_count} equipment items to {len(records)} employees',
                'type': 'success',
                'sticky': False,
            }
        }
        
    except Exception as e:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Assignment Failed',
                'message': f'Error: {str(e)}',
                'type': 'danger',
                'sticky': True,
            }
        }
```

## 5. Scheduled Actions (Automated Actions)

### Automated Probation Review

```python
class EmployeeAutomatedTasks(models.Model):
    _name = 'employee.automated.tasks'
    _description = 'Automated Employee Management Tasks'
    
    def auto_probation_review(self):
        """
        Scheduled Action: Automatically check for probation endings
        Runs daily to identify employees whose probation ends in 7 days
        """
        try:
            review_date = fields.Date.today() + timedelta(days=7)
            
            # Find employees with probation ending in 7 days
            probation_employees = self.env['custom.employee'].search([
                ('probation_end_date', '=', review_date),
                ('employment_type', '=', 'probation')
            ])
            
            review_count = 0
            for employee in probation_employees:
                # Create probation review activity for manager
                if employee.parent_id:
                    employee.activity_schedule(
                        'mail.mail_activity_data_todo',
                        review_date,
                        summary=f'Probation Review: {employee.name}',
                        note=f'Probation period ends on {employee.probation_end_date}. Schedule review meeting.',
                        user_id=employee.parent_id.user_id.id
                    )
                    review_count += 1
            
            _logger.info(f"Scheduled {review_count} probation reviews")
            return review_count
            
        except Exception as e:
            _logger.error(f"Probation review scheduling failed: {str(e)}")
            return 0
    
    def auto_equipment_maintenance_check(self):
        """
        Scheduled Action: Check equipment warranty and maintenance
        Runs weekly to identify equipment needing maintenance
        """
        try:
            today = fields.Date.today()
            next_month = today + timedelta(days=30)
            
            # Find equipment with warranty ending in next 30 days
            expiring_equipment = self.env['employee.equipment'].search([
                ('warranty_end_date', '>=', today),
                ('warranty_end_date', '<=', next_month),
                ('state', '=', 'assigned')
            ])
            
            maintenance_count = 0
            for equipment in expiring_equipment:
                # Create maintenance alert
                equipment.activity_schedule(
                    'mail.mail_activity_data_todo',
                    equipment.warranty_end_date,
                    summary=f'Equipment Maintenance: {equipment.name}',
                    note=f'Warranty for {equipment.name} expires on {equipment.warranty_end_date}. Schedule maintenance.',
                    user_id=self.env.user.id
                )
                maintenance_count += 1
            
            _logger.info(f"Scheduled {maintenance_count} equipment maintenance alerts")
            return maintenance_count
            
        except Exception as e:
            _logger.error(f"Equipment maintenance check failed: {str(e)}")
            return 0
    
    def auto_birthday_announcements(self):
        """
        Scheduled Action: Send birthday announcements
        Runs daily to celebrate employee birthdays
        """
        try:
            today = fields.Date.today()
            
            # Find employees with birthday today
            birthday_employees = self.env['custom.employee'].search([
                ('birthday', '!=', False)
            ])
            
            birthday_celebrations = 0
            for employee in birthday_employees:
                if employee.birthday.month == today.month and employee.birthday.day == today.day:
                    # Post birthday message to employee's chatter
                    employee.message_post(
                        body=f"🎉 Happy Birthday, {employee.name}! 🎂",
                        subject="Happy Birthday!",
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment'
                    )
                    
                    # Send to company-wide channel if configured
                    birthday_channel = self.env.ref('employee_app.channel_birthdays', False)
                    if birthday_channel:
                        birthday_channel.message_post(
                            body=f"🎉 Let's wish {employee.name} a Happy Birthday today! 🎂",
                            subject="Birthday Celebration",
                            message_type='comment'
                        )
                    
                    birthday_celebrations += 1
            
            _logger.info(f"Celebrated {birthday_celebrations} birthdays")
            return birthday_celebrations
            
        except Exception as e:
            _logger.error(f"Birthday announcements failed: {str(e)}")
            return 0
    
    def auto_work_anniversary_celebrations(self):
        """
        Scheduled Action: Celebrate work anniversaries
        Runs daily to recognize employee work anniversaries
        """
        try:
            today = fields.Date.today()
            
            # Find employees with work anniversary today
            anniversary_employees = self.env['custom.employee'].search([
                ('create_date', '!=', False)
            ])
            
            anniversary_count = 0
            for employee in anniversary_employees:
                create_date = fields.Date.from_string(employee.create_date)
                if create_date.month == today.month and create_date.day == today.day:
                    years_with_company = today.year - create_date.year
                    
                    # Post anniversary message
                    employee.message_post(
                        body=f"🎊 Congratulations {employee.name} on {years_with_company} year{'s' if years_with_company > 1 else ''} with the company! 🎊",
                        subject="Work Anniversary",
                        message_type='comment'
                    )
                    
                    anniversary_count += 1
            
            _logger.info(f"Celebrated {anniversary_count} work anniversaries")
            return anniversary_count
            
        except Exception as e:
            _logger.error(f"Work anniversary celebrations failed: {str(e)}")
            return 0
```

## 6. Employee Performance and Reviews

```python
class EmployeeReview(models.Model):
    _name = 'employee.review'
    _description = 'Employee Performance Reviews'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Review Title', required=True)
    employee_id = fields.Many2one('custom.employee', string='Employee', required=True)
    reviewer_id = fields.Many2one('custom.employee', string='Reviewer', required=True)
    review_date = fields.Date(string='Review Date', default=fields.Date.today)
    review_period_start = fields.Date(string='Review Period Start', required=True)
    review_period_end = fields.Date(string='Review Period End', required=True)
    
    # Review Components
    technical_skills = fields.Selection([
        ('1', 'Needs Improvement'),
        ('2', 'Meets Expectations'),
        ('3', 'Exceeds Expectations'),
        ('4', 'Outstanding')
    ], string='Technical Skills')
    
    communication_skills = fields.Selection([
        ('1', 'Needs Improvement'),
        ('2', 'Meets Expectations'),
        ('3', 'Exceeds Expectations'),
        ('4', 'Outstanding')
    ], string='Communication Skills')
    
    teamwork = fields.Selection([
        ('1', 'Needs Improvement'),
        ('2', 'Meets Expectations'),
        ('3', 'Exceeds Expectations'),
        ('4', 'Outstanding')
    ], string='Teamwork')
    
    # Overall Rating
    overall_rating = fields.Float(string='Overall Rating', compute='_compute_overall_rating', store=True)
    review_summary = fields.Text(string='Review Summary')
    goals = fields.Text(string='Future Goals')
    employee_comments = fields.Text(string='Employee Comments')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('acknowledged', 'Acknowledged')
    ], string='Status', default='draft', tracking=True)
    
    @api.depends('technical_skills', 'communication_skills', 'teamwork')
    def _compute_overall_rating(self):
        for review in self:
            ratings = []
            if review.technical_skills:
                ratings.append(int(review.technical_skills))
            if review.communication_skills:
                ratings.append(int(review.communication_skills))
            if review.teamwork:
                ratings.append(int(review.teamwork))
            
            if ratings:
                review.overall_rating = sum(ratings) / len(ratings)
            else:
                review.overall_rating = 0
    
    def action_start_review(self):
        """Start the review process"""
        for review in self:
            review.state = 'in_progress'
            # Notify employee
            review.employee_id.message_post(
                body=f"Your performance review has been scheduled with {review.reviewer_id.name}",
                subject="Performance Review Scheduled"
            )
    
    def action_complete_review(self):
        """Complete the review"""
        for review in self:
            review.state = 'completed'
            # Schedule follow-up meeting
            review.activity_schedule(
                'mail.mail_activity_data_meeting',
                fields.Date.today() + timedelta(days=30),
                summary='Follow-up: Performance Review',
                note=f'Follow-up discussion for performance review with {review.employee_id.name}',
                user_id=review.reviewer_id.user_id.id
            )
```

## 7. Employee Dashboard and Reporting

```python
class EmployeeDashboard(models.Model):
    _name = 'employee.dashboard'
    _description = 'Employee Management Dashboard'
    
    def get_employee_statistics(self):
        """Get comprehensive employee statistics"""
        employees = self.env['custom.employee'].search([])
        
        stats = {
            'total_employees': len(employees),
            'by_department': {},
            'by_employment_type': {},
            'by_location': {},
            'recent_joiners': [],
            'upcoming_probations': []
        }
        
        # Department breakdown
        departments = self.env['hr.department'].search([])
        for dept in departments:
            dept_employees = employees.filtered(lambda e: e.department_id == dept)
            stats['by_department'][dept.name] = len(dept_employees)
        
        # Employment type breakdown
        employment_types = set(employees.mapped('employment_type'))
        for emp_type in employment_types:
            type_employees = employees.filtered(lambda e: e.employment_type == emp_type)
            stats['by_employment_type'][emp_type] = len(type_employees)
        
        # Recent joiners (last 30 days)
        thirty_days_ago = fields.Date.today() - timedelta(days=30)
        recent_joiners = employees.filtered(
            lambda e: e.create_date and fields.Date.from_string(e.create_date) >= thirty_days_ago
        )
        stats['recent_joiners'] = [{
            'name': emp.name,
            'department': emp.department_id.name if emp.department_id else 'N/A',
            'join_date': emp.create_date
        } for emp in recent_joiners[:5]]  # Limit to 5 most recent
        
        # Upcoming probation endings
        next_week = fields.Date.today() + timedelta(days=7)
        upcoming_probations = employees.filtered(
            lambda e: e.probation_end_date and e.probation_end_date <= next_week
        )
        stats['upcoming_probations'] = [{
            'name': emp.name,
            'probation_end_date': emp.probation_end_date,
            'manager': emp.parent_id.name if emp.parent_id else 'N/A'
        } for emp in upcoming_probations]
        
        return stats
    
    def get_equipment_report(self):
        """Generate equipment assignment report"""
        equipment = self.env['employee.equipment'].search([])
        
        report = {
            'total_equipment': len(equipment),
            'by_category': {},
            'by_status': {},
            'warranty_expiring': []
        }
        
        # Category breakdown
        categories = set(equipment.mapped('category'))
        for category in categories:
            category_equipment = equipment.filtered(lambda e: e.category == category)
            report['by_category'][category] = len(category_equipment)
        
        # Status breakdown
        statuses = set(equipment.mapped('state'))
        for status in statuses:
            status_equipment = equipment.filtered(lambda e: e.state == status)
            report['by_status'][status] = len(status_equipment)
        
        # Warranty expiring in next 30 days
        next_month = fields.Date.today() + timedelta(days=30)
        expiring_equipment = equipment.filtered(
            lambda e: e.warranty_end_date and e.warranty_end_date <= next_month
        )
        report['warranty_expiring'] = [{
            'name': eq.name,
            'assigned_to': eq.employee_id.name,
            'warranty_end_date': eq.warranty_end_date
        } for eq in expiring_equipment]
        
        return report
```

## 8. Security and Access Control

```python
class EmployeeSecurity(models.Model):
    _inherit = 'res.users'
    
    def check_employee_access(self, operation='read'):
        """Check user access rights for employee data"""
        # Managers can read/write their department's employees
        if self.has_group('hr.group_hr_manager'):
            return True
        
        # Employees can read their own data
        if operation == 'read' and self.employee_ids:
            return True
        
        # Department managers can manage their department
        if self.employee_ids and self.employee_ids[0].department_id and \
           self.employee_ids[0].department_id.manager_id == self.employee_ids[0]:
            return True
        
        return False

# Record Rules (to be added in XML data file)
"""
<record id="employee_rule_department_manager" model="ir.rule">
    <field name="name">Department Manager Employee Access</field>
    <field name="model_id" ref="model_custom_employee"/>
    <field name="domain_force">
        ['|', ('department_id.manager_id', '=', user.employee_ids.id), ('id', '=', user.employee_ids.id)]
    </field>
    <field name="groups" eval="[(4, ref('hr.group_hr_user'))]"/>
</record>
"""
```

## 9. Integration with Odoo Online

### Configuration for Odoo Online

```python
class EmployeeAppConfiguration(models.Model):
    _name = 'employee.app.config'
    _description = 'Employee App Configuration'
    
    # Odoo Online specific settings
    enable_online_features = fields.Boolean(string='Enable Online Features', default=True)
    auto_backup_enabled = fields.Boolean(string='Auto Backup', default=True)
    external_api_access = fields.Boolean(string='External API Access', default=False)
    
    # Notification settings
    email_notifications = fields.Boolean(string='Email Notifications', default=True)
    push_notifications = fields.Boolean(string='Push Notifications', default=False)
    
    def test_online_connection(self):
        """Test connection to Odoo Online services"""
        try:
            # Test database connection
            self.env.cr.execute("SELECT 1")
            
            # Test email configuration
            self.env['mail.mail'].create({
                'email_to': self.env.user.email,
                'subject': 'Employee App Test',
                'body_html': '<p>This is a test email from your Employee App.</p>'
            }).send()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Test Successful',
                    'message': 'All services are working properly',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Test Failed',
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
```

