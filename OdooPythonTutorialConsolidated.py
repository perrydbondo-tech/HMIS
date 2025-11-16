# Odoo Python Tutorial for Consolidated School Management Information System (22 High Schools)

## 1. Multi-School Architecture Core Models

### Central School Management Model

```python
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging
import hashlib

_logger = logging.getLogger(__name__)

class ConsolidatedSchool(models.Model):
    _name = 'consolidated.school'
    _description = 'Consolidated School Management'
    _rec_name = 'display_name'
    
    # School Identification
    school_id = fields.Char(string='School ID', required=True, copy=False, readonly=True,
                          default=lambda self: self._generate_school_id())
    display_name = fields.Char(string='School Name', compute='_compute_display_name', store=True)
    name = fields.Char(string='School Name', required=True, tracking=True)
    code = fields.Char(string='School Code', required=True, size=10)
    
    # School Information
    school_type = fields.Selection([
        ('public', 'Public High School'),
        ('private', 'Private High School'),
        ('charter', 'Charter School')
    ], string='School Type', required=True)
    
    address = fields.Text(string='Address', required=True)
    city = fields.Char(string='City', required=True)
    state = fields.Char(string='State', required=True)
    zip_code = fields.Char(string='ZIP Code')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    principal_name = fields.Char(string='Principal Name')
    principal_email = fields.Char(string='Principal Email')
    
    # Academic Information
    establishment_year = fields.Integer(string='Establishment Year')
    total_capacity = fields.Integer(string='Total Capacity', default=1000)
    current_enrollment = fields.Integer(string='Current Enrollment', compute='_compute_current_enrollment')
    
    # System Configuration
    is_active = fields.Boolean(string='Active', default=True)
    database_name = fields.Char(string='Database Identifier', compute='_compute_database_name')
    school_domain = fields.Char(string='School Domain', compute='_compute_school_domain')
    
    # Login Information
    admin_user_id = fields.Many2one('res.users', string='School Admin User')
    login_url = fields.Char(string='School Login URL', compute='_compute_login_url')
    
    # Relationships
    student_ids = fields.One2many('consolidated.student', 'school_id', string='Students')
    teacher_ids = fields.One2many('consolidated.teacher', 'school_id', string='Teachers')
    class_ids = fields.One2many('consolidated.class', 'school_id', string='Classes')
    
    # Computed fields
    @api.depends('name', 'code')
    def _compute_display_name(self):
        for school in self:
            school.display_name = f"{school.code} - {school.name}"
    
    @api.depends('student_ids')
    def _compute_current_enrollment(self):
        for school in self:
            school.current_enrollment = len(school.student_ids.filtered(lambda s: s.status == 'active'))
    
    @api.depends('code')
    def _compute_database_name(self):
        for school in self:
            school.database_name = f"school_{school.code.lower()}"
    
    @api.depends('code')
    def _compute_school_domain(self):
        for school in self:
            school.school_domain = f"[('school_id', '=', {school.id})]"
    
    @api.depends('code')
    def _compute_login_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for school in self:
            school.login_url = f"{base_url}/school/{school.code}"
    
    # Constraints
    @api.constrains('code')
    def _check_school_code_unique(self):
        for school in self:
            if self.search([('code', '=', school.code), ('id', '!=', school.id)]):
                raise ValidationError("School code must be unique!")
    
    # Sequence generation
    @api.model
    def _generate_school_id(self):
        sequence = self.env['ir.sequence'].next_by_code('consolidated.school.id') or 'SCH'
        return sequence
    
    # Action methods
    def action_create_school_admin(self):
        """Create school-specific admin user"""
        for school in self:
            if not school.admin_user_id:
                # Create user group for this school
                group_name = f"school_{school.code}_admin"
                group = self.env['res.groups'].create({
                    'name': f"{school.code} Administrator",
                    'users': [(6, 0, [])]
                })
                
                # Create admin user
                user_vals = {
                    'name': f"{school.name} Administrator",
                    'login': f"admin_{school.code.lower()}",
                    'password': self._generate_initial_password(school.code),
                    'groups_id': [(4, group.id)],
                    'school_id': school.id,
                }
                admin_user = self.env['res.users'].create(user_vals)
                school.admin_user_id = admin_user.id
    
    def _generate_initial_password(self, school_code):
        """Generate initial password for school admin"""
        base_string = f"{school_code}_{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(base_string.encode()).hexdigest()[:8]
    
    def action_generate_school_report(self):
        """Generate comprehensive school report"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.name} - Comprehensive Report',
            'res_model': 'consolidated.school.report',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_school_id': self.id}
        }
```

### Multi-School Aware Student Model

```python
class ConsolidatedStudent(models.Model):
    _name = 'consolidated.student'
    _description = 'Multi-School Student Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # School Association
    school_id = fields.Many2one('consolidated.school', string='School', required=True, 
                               default=lambda self: self._get_default_school())
    
    # Student Identification
    student_id = fields.Char(string='Student ID', required=True, copy=False, readonly=True,
                           compute='_compute_student_id', store=True)
    global_student_id = fields.Char(string='Global Student ID', readonly=True,
                                  default=lambda self: self._generate_global_id())
    
    first_name = fields.Char(string='First Name', required=True, tracking=True)
    last_name = fields.Char(string='Last Name', required=True, tracking=True)
    display_name = fields.Char(string='Student Name', compute='_compute_display_name', store=True)
    
    # Academic Information
    class_id = fields.Many2one('consolidated.class', string='Class', 
                              domain="[('school_id', '=', school_id)]")
    section_id = fields.Many2one('consolidated.section', string='Section',
                                domain="[('class_id.school_id', '=', school_id)]")
    academic_year_id = fields.Many2one('consolidated.academic.year', string='Academic Year')
    
    # School-specific fields
    school_roll_number = fields.Integer(string='School Roll Number')
    house_system = fields.Selection([
        ('red', 'Red House'),
        ('blue', 'Blue House'),
        ('green', 'Green House'),
        ('yellow', 'Yellow House')
    ], string='House System')
    
    @api.depends('school_id', 'school_roll_number')
    def _compute_student_id(self):
        for student in self:
            if student.school_id and student.school_roll_number:
                student.student_id = f"{student.school_id.code}-{student.school_roll_number:04d}"
            else:
                student.student_id = "Pending"
    
    @api.model
    def _get_default_school(self):
        """Get default school from context or user"""
        if self.env.context.get('default_school_id'):
            return self.env.context.get('default_school_id')
        
        # Get school from current user
        if hasattr(self.env.user, 'school_id') and self.env.user.school_id:
            return self.env.user.school_id.id
        
        return False
    
    @api.model
    def _generate_global_id(self):
        """Generate global unique student ID"""
        sequence = self.env['ir.sequence'].next_by_code('consolidated.student.global.id') or 'GS'
        return sequence
    
    # Security rules implementation
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Override search to respect school boundaries"""
        # Add school filter if user is school-specific
        if hasattr(self.env.user, 'school_id') and self.env.user.school_id:
            args = expression.AND([args, [('school_id', '=', self.env.user.school_id.id)]])
        
        return super().search(args, offset, limit, order, count)
```

## 2. Multi-School Security and Access Control

### School-Aware User Model

```python
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    school_id = fields.Many2one('consolidated.school', string='Assigned School')
    is_school_user = fields.Boolean(string='Is School User', compute='_compute_is_school_user')
    school_role = fields.Selection([
        ('admin', 'School Administrator'),
        ('principal', 'Principal'),
        ('teacher', 'Teacher'),
        ('staff', 'Staff'),
        ('parent', 'Parent')
    ], string='School Role')
    
    @api.depends('school_id')
    def _compute_is_school_user(self):
        for user in self:
            user.is_school_user = bool(user.school_id)
    
    @api.model
    def _login(self, db, login, password, user_agent_env):
        """Override login to handle school-specific authentication"""
        result = super()._login(db, login, password, user_agent_env)
        
        # Set school context for school users
        user = self.search([('id', '=', result)])
        if user.school_id:
            self.env.context = dict(self.env.context, default_school_id=user.school_id.id)
        
        return result

class ConsolidatedSecurityRules(models.Model):
    _name = 'consolidated.security.rules'
    _description = 'Multi-School Security Rules'
    
    @api.model
    def _get_school_based_domain(self, model_name):
        """Generate domain based on user's school"""
        domains = {
            'consolidated.student': "[('school_id', '=', user.school_id.id)]",
            'consolidated.teacher': "[('school_id', '=', user.school_id.id)]",
            'consolidated.class': "[('school_id', '=', user.school_id.id)]",
            'consolidated.attendance': "[('school_id', '=', user.school_id.id)]",
        }
        return domains.get(model_name, "[]")
```

### Record Rules for Data Separation

```xml
<!-- XML data file for record rules -->
<record id="school_student_rule" model="ir.rule">
    <field name="name">School Student Access</field>
    <field name="model_id" ref="model_consolidated_student"/>
    <field name="domain_force">[('school_id','=',user.school_id.id)]</field>
    <field name="groups" eval="[(4, ref('school_management.group_school_user'))]"/>
</record>

<record id="school_teacher_rule" model="ir.rule">
    <field name="name">School Teacher Access</field>
    <field name="model_id" ref="model_consolidated_teacher"/>
    <field name="domain_force">[('school_id','=',user.school_id.id)]</field>
    <field name="groups" eval="[(4, ref('school_management.group_school_user'))]"/>
</record>
```

## 3. Centralized Automated Actions

### Multi-School Automated Tasks

```python
class ConsolidatedAutomatedTasks(models.Model):
    _name = 'consolidated.automated.tasks'
    _description = 'Centralized Automated Tasks for All Schools'
    
    def execute_all_schools_operation(self, method_name, *args, **kwargs):
        """Execute a method for all active schools"""
        active_schools = self.env['consolidated.school'].search([('is_active', '=', True)])
        
        results = {}
        for school in active_schools:
            try:
                # Switch context to school
                school_env = self.with_context(default_school_id=school.id)
                
                # Execute method
                if hasattr(school_env, method_name):
                    method = getattr(school_env, method_name)
                    results[school.code] = method(*args, **kwargs)
                else:
                    results[school.code] = f"Method {method_name} not found"
                    
            except Exception as e:
                results[school.code] = f"Error: {str(e)}"
                _logger.error(f"Failed to execute {method_name} for school {school.code}: {str(e)}")
        
        return results
    
    def auto_generate_daily_attendance_all_schools(self):
        """Generate daily attendance for all schools"""
        return self.execute_all_schools_operation('_auto_generate_daily_attendance')
    
    def _auto_generate_daily_attendance(self):
        """Generate daily attendance for current school"""
        today = fields.Date.today()
        school_id = self.env.context.get('default_school_id')
        
        if not school_id:
            return "No school context"
        
        Attendance = self.env['consolidated.attendance']
        students = self.env['consolidated.student'].search([
            ('school_id', '=', school_id),
            ('status', '=', 'active')
        ])
        
        generated_count = 0
        for student in students:
            existing = Attendance.search([
                ('student_id', '=', student.id),
                ('date', '=', today)
            ])
            
            if not existing:
                Attendance.create({
                    'student_id': student.id,
                    'school_id': school_id,
                    'date': today,
                    'status': 'absent',
                    'class_id': student.class_id.id,
                })
                generated_count += 1
        
        return f"Generated {generated_count} attendance records"
    
    def auto_send_weekly_reports_all_schools(self):
        """Send weekly reports for all schools"""
        return self.execute_all_schools_operation('_auto_send_weekly_reports')
    
    def _auto_send_weekly_reports(self):
        """Send weekly reports for current school"""
        school_id = self.env.context.get('default_school_id')
        school = self.env['consolidated.school'].browse(school_id)
        
        # Generate various reports
        reports = {
            'attendance': self._generate_attendance_report(school),
            'academic': self._generate_academic_report(school),
            'financial': self._generate_financial_report(school),
        }
        
        # Send to school principal
        if school.principal_email:
            template = self.env.ref('consolidated_smis.email_template_weekly_report')
            template.with_context(reports=reports).send_mail(school.id, force_send=False)
        
        return f"Sent weekly reports to {school.principal_email}"
    
    def auto_sync_school_data_to_central(self):
        """Sync all school data to central database for reporting"""
        central_data = {
            'sync_time': fields.Datetime.now(),
            'schools': {}
        }
        
        active_schools = self.env['consolidated.school'].search([('is_active', '=', True)])
        
        for school in active_schools:
            school_data = self._collect_school_data(school)
            central_data['schools'][school.code] = school_data
        
        # Store in central reporting model
        self.env['consolidated.central.report'].create({
            'name': f"Data Sync {fields.Datetime.now()}",
            'sync_data': central_data
        })
        
        return f"Synced data for {len(active_schools)} schools"
    
    def _collect_school_data(self, school):
        """Collect data for a specific school"""
        return {
            'school_info': {
                'name': school.name,
                'enrollment': school.current_enrollment,
                'teachers': len(school.teacher_ids),
                'classes': len(school.class_ids),
            },
            'attendance_today': self.env['consolidated.attendance'].search_count([
                ('school_id', '=', school.id),
                ('date', '=', fields.Date.today()),
                ('status', '=', 'present')
            ]),
            'financial_status': self._get_school_financial_status(school),
        }
```

## 4. Multi-School Server Actions

### Central Administration Server Actions

```python
# Server Action: Create Multiple School Users
def create_school_users(records):
    """
    Server action to create user accounts for multiple schools
    """
    try:
        created_users = []
        
        for school in records:
            # Create admin user if not exists
            if not school.admin_user_id:
                school.action_create_school_admin()
                created_users.append(f"Admin for {school.code}")
            
            # Create principal user
            if school.principal_email:
                principal_user = env['res.users'].create({
                    'name': school.principal_name or f"Principal {school.name}",
                    'login': school.principal_email,
                    'email': school.principal_email,
                    'school_id': school.id,
                    'school_role': 'principal',
                    'password': f"principal_{school.code}123",
                    'groups_id': [(6, 0, [env.ref('consolidated_smis.group_school_principal').id])]
                })
                created_users.append(f"Principal for {school.code}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Users Created',
                'message': f'Created users for {len(created_users)} schools',
                'type': 'success',
                'sticky': True,
            }
        }
        
    except Exception as e:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'User Creation Failed',
                'message': f'Error: {str(e)}',
                'type': 'danger',
                'sticky': True,
            }
        }

# Server Action: Bulk School Configuration
def configure_multiple_schools(records):
    """
    Server action to apply standard configuration to multiple schools
    """
    try:
        AcademicYear = env['consolidated.academic.year']
        current_year = AcademicYear.search([('is_current', '=', True)], limit=1)
        
        configured_schools = []
        for school in records:
            # Apply standard class structure
            self._create_standard_classes(school)
            
            # Set up default fee structure
            self._create_default_fee_structure(school)
            
            # Configure academic year
            if current_year:
                school.write({'academic_year_id': current_year.id})
            
            configured_schools.append(school.display_name)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Schools Configured',
                'message': f'Configured {len(configured_schools)} schools',
                'type': 'success',
                'sticky': True,
            }
        }
        
    except Exception as e:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Configuration Failed',
                'message': f'Error: {str(e)}',
                'type': 'danger',
                'sticky': True,
            }
        }
```

## 5. Cross-School Reporting and Analytics

```python
class ConsolidatedCentralReport(models.Model):
    _name = 'consolidated.central.report'
    _description = 'Centralized Cross-School Reporting'
    
    name = fields.Char(string='Report Name', required=True)
    report_type = fields.Selection([
        ('academic', 'Academic Performance'),
        ('attendance', 'Attendance Analysis'),
        ('financial', 'Financial Summary'),
        ('enrollment', 'Enrollment Statistics')
    ], string='Report Type', required=True)
    
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date', default=fields.Date.today)
    generated_by = fields.Many2one('res.users', string='Generated By', 
                                  default=lambda self: self.env.user)
    
    report_data = fields.Text(string='Report Data')  # JSON stored data
    school_count = fields.Integer(string='Schools Included', compute='_compute_school_count')
    
    def generate_cross_school_academic_report(self):
        """Generate academic performance report across all schools"""
        schools = self.env['consolidated.school'].search([('is_active', '=', True)])
        
        report_data = {
            'generated_date': fields.Date.today(),
            'total_schools': len(schools),
            'school_performance': []
        }
        
        for school in schools:
            performance = self._calculate_school_performance(school)
            report_data['school_performance'].append({
                'school_code': school.code,
                'school_name': school.name,
                'performance': performance
            })
        
        # Create report record
        self.create({
            'name': f"Cross-School Academic Report - {fields.Date.today()}",
            'report_type': 'academic',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'report_data': str(report_data)
        })
        
        return report_data
    
    def _calculate_school_performance(self, school):
        """Calculate performance metrics for a school"""
        students = self.env['consolidated.student'].search([
            ('school_id', '=', school.id),
            ('status', '=', 'active')
        ])
        
        if not students:
            return {}
        
        # Calculate average grades
        grades = self.env['consolidated.grade'].search([
            ('student_id', 'in', students.ids)
        ])
        
        avg_percentage = sum(grades.mapped('percentage')) / len(grades) if grades else 0
        
        # Calculate attendance rate
        attendances = self.env['consolidated.attendance'].search([
            ('student_id', 'in', students.ids),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ])
        
        present_count = len(attendances.filtered(lambda a: a.status == 'present'))
        attendance_rate = (present_count / len(attendances)) * 100 if attendances else 0
        
        return {
            'total_students': len(students),
            'average_percentage': round(avg_percentage, 2),
            'attendance_rate': round(attendance_rate, 2),
            'top_performer': self._get_top_performer(school)
        }
```

## 6. School-Specific Configuration Management

```python
class ConsolidatedSchoolConfig(models.Model):
    _name = 'consolidated.school.config'
    _description = 'School-Specific Configuration'
    
    school_id = fields.Many2one('consolidated.school', string='School', required=True)
    config_key = fields.Char(string='Configuration Key', required=True)
    config_value = fields.Text(string='Configuration Value')
    config_type = fields.Selection([
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON')
    ], string='Configuration Type', default='string')
    
    is_active = fields.Boolean(string='Active', default=True)
    
    @api.model
    def get_school_config(self, school_id, key, default=None):
        """Get school-specific configuration value"""
        config = self.search([
            ('school_id', '=', school_id),
            ('config_key', '=', key),
            ('is_active', '=', True)
        ], limit=1)
        
        if config:
            return self._parse_config_value(config.config_value, config.config_type)
        return default
    
    def _parse_config_value(self, value, config_type):
        """Parse configuration value based on type"""
        if config_type == 'integer':
            return int(value) if value else 0
        elif config_type == 'boolean':
            return value.lower() == 'true' if value else False
        elif config_type == 'json':
            return eval(value) if value else {}
        else:
            return value

class ConsolidatedSchoolTemplate(models.Model):
    _name = 'consolidated.school.template'
    _description = 'School Configuration Templates'
    
    name = fields.Char(string='Template Name', required=True)
    template_type = fields.Selection([
        ('academic', 'Academic Structure'),
        ('financial', 'Fee Structure'),
        ('timetable', 'Timetable Structure')
    ], string='Template Type', required=True)
    
    configuration_data = fields.Text(string='Configuration Data')  # JSON data
    
    def apply_template_to_school(self, school_id):
        """Apply template configuration to a school"""
        school = self.env['consolidated.school'].browse(school_id)
        config_data = eval(self.configuration_data) if self.configuration_data else {}
        
        # Apply template-specific configurations
        if self.template_type == 'academic':
            self._apply_academic_template(school, config_data)
        elif self.template_type == 'financial':
            self._apply_financial_template(school, config_data)
        
        return True
```

## 7. Bulk Data Operations for Multiple Schools

```python
class ConsolidatedBulkOperations(models.Model):
    _name = 'consolidated.bulk.operations'
    _description = 'Bulk Operations for Multiple Schools'
    
    def bulk_create_students(self, student_data_list):
        """Bulk create students across multiple schools"""
        results = {
            'successful': [],
            'failed': []
        }
        
        for student_data in student_data_list:
            try:
                school_code = student_data.get('school_code')
                school = self.env['consolidated.school'].search([('code', '=', school_code)], limit=1)
                
                if not school:
                    results['failed'].append({
                        'data': student_data,
                        'error': f"School {school_code} not found"
                    })
                    continue
                
                # Create student with school context
                student_vals = {
                    'school_id': school.id,
                    'first_name': student_data['first_name'],
                    'last_name': student_data['last_name'],
                    'school_roll_number': student_data.get('roll_number'),
                    'class_id': student_data.get('class_id'),
                }
                
                student = self.env['consolidated.student'].create(student_vals)
                results['successful'].append(student.display_name)
                
            except Exception as e:
                results['failed'].append({
                    'data': student_data,
                    'error': str(e)
                })
        
        return results
    
    def bulk_update_academic_year(self, new_academic_year_id):
        """Bulk update academic year for all schools"""
        schools = self.env['consolidated.school'].search([('is_active', '=', True)])
        
        updated_count = 0
        for school in schools:
            try:
                # Update school academic year
                school.write({'academic_year_id': new_academic_year_id})
                
                # Update all students in school
                students = self.env['consolidated.student'].search([
                    ('school_id', '=', school.id)
                ])
                students.write({'academic_year_id': new_academic_year_id})
                
                updated_count += 1
                
            except Exception as e:
                _logger.error(f"Failed to update academic year for school {school.code}: {str(e)}")
        
        return updated_count
```

## 8. Performance Optimization for Large Dataset

```python
class ConsolidatedPerformance(models.Model):
    _name = 'consolidated.performance'
    _description = 'Performance Optimization Utilities'
    
    def optimize_school_queries(self):
        """Optimize database queries for multi-school environment"""
        optimizations = {}
        
        # Create indexes for frequently searched fields
        index_queries = [
            "CREATE INDEX IF NOT EXISTS consolidated_student_school_id_idx ON consolidated_student (school_id)",
            "CREATE INDEX IF NOT EXISTS consolidated_teacher_school_id_idx ON consolidated_teacher (school_id)",
            "CREATE INDEX IF NOT EXISTS consolidated_attendance_date_idx ON consolidated_attendance (date)",
            "CREATE INDEX IF NOT EXISTS consolidated_grade_student_id_idx ON consolidated_grade (student_id)",
        ]
        
        for query in index_queries:
            try:
                self.env.cr.execute(query)
                optimizations[query] = "Success"
            except Exception as e:
                optimizations[query] = f"Failed: {str(e)}"
        
        return optimizations
    
    def cleanup_old_data(self, retention_days=365):
        """Clean up old data while maintaining school separation"""
        cutoff_date = fields.Date.today() - timedelta(days=retention_days)
        
        cleanup_stats = {}
        
        # Archive old attendance records
        old_attendances = self.env['consolidated.attendance'].search([
            ('date', '<', cutoff_date)
        ])
        cleanup_stats['archived_attendances'] = len(old_attendances)
        old_attendances.unlink()
        
        # Archive old fee records
        old_fees = self.env['consolidated.fee'].search([
            ('create_date', '<', cutoff_date),
            ('state', '=', 'paid')
        ])
        cleanup_stats['archived_fees'] = len(old_fees)
        old_fees.unlink()
        
        return cleanup_stats
```

## Implementation Strategy for 22 Schools:
