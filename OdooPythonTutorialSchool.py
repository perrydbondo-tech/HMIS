# Odoo Python Tutorial for School Management Information System (SMIS)

## 1. SMIS Core Models Structure

### Student Management Model

```python
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class SchoolStudent(models.Model):
    _name = 'school.student'
    _description = 'Student Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    
    # Student Identification
    student_id = fields.Char(string='Student ID', required=True, copy=False, readonly=True,
                           default=lambda self: self._generate_student_id())
    first_name = fields.Char(string='First Name', required=True, tracking=True)
    last_name = fields.Char(string='Last Name', required=True, tracking=True)
    display_name = fields.Char(string='Student Name', compute='_compute_display_name', store=True)
    date_of_birth = fields.Date(string='Date of Birth', required=True, tracking=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', required=True, tracking=True)
    
    # Academic Information
    class_id = fields.Many2one('school.class', string='Class', tracking=True)
    section_id = fields.Many2one('school.section', string='Section')
    academic_year_id = fields.Many2one('school.academic.year', string='Academic Year', required=True)
    roll_number = fields.Integer(string='Roll Number')
    enrollment_date = fields.Date(string='Enrollment Date', default=fields.Date.today)
    
    # Contact Information
    parent_id = fields.Many2one('school.parent', string='Parent/Guardian')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    emergency_contact = fields.Char(string='Emergency Contact')
    emergency_phone = fields.Char(string='Emergency Phone')
    
    # Medical Information
    blood_group = fields.Selection([
        ('a_positive', 'A+'),
        ('a_negative', 'A-'),
        ('b_positive', 'B+'),
        ('b_negative', 'B-'),
        ('ab_positive', 'AB+'),
        ('ab_negative', 'AB-'),
        ('o_positive', 'O+'),
        ('o_negative', 'O-')
    ], string='Blood Group')
    medical_conditions = fields.Text(string='Medical Conditions')
    allergies = fields.Text(string='Allergies')
    
    # Status
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('transferred', 'Transferred')
    ], string='Status', default='active', tracking=True)
    
    # Relationships
    attendance_ids = fields.One2many('school.attendance', 'student_id', string='Attendance Records')
    grade_ids = fields.One2many('school.grade', 'student_id', string='Grades')
    fee_ids = fields.One2many('school.fee', 'student_id', string='Fee Records')
    
    # Computed fields
    @api.depends('first_name', 'last_name')
    def _compute_display_name(self):
        for student in self:
            student.display_name = f"{student.first_name} {student.last_name}"
    
    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.today()
        for student in self:
            if student.date_of_birth:
                delta = today - student.date_of_birth
                student.age = delta.days // 365
            else:
                student.age = 0
    
    # Constraints
    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for student in self:
            if student.date_of_birth > fields.Date.today():
                raise ValidationError("Date of birth cannot be in the future!")
    
    @api.constrains('roll_number')
    def _check_roll_number_unique(self):
        for student in self:
            if student.roll_number:
                existing = self.search([
                    ('class_id', '=', student.class_id.id),
                    ('roll_number', '=', student.roll_number),
                    ('id', '!=', student.id)
                ])
                if existing:
                    raise ValidationError("Roll number must be unique within the same class!")
    
    # Sequence generation
    @api.model
    def _generate_student_id(self):
        sequence = self.env['ir.sequence'].next_by_code('school.student.id') or 'NEW'
        return sequence
    
    # Action methods
    def action_generate_id_card(self):
        """Generate student ID card"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/school/student/{self.id}/id_card',
            'target': 'new'
        }
    
    def action_view_attendance(self):
        """View student attendance records"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.display_name} - Attendance',
            'res_model': 'school.attendance',
            'domain': [('student_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_student_id': self.id}
        }
```

### Class and Section Management

```python
class SchoolClass(models.Model):
    _name = 'school.class'
    _description = 'School Class'
    
    name = fields.Char(string='Class Name', required=True)
    code = fields.Char(string='Class Code', required=True)
    class_teacher_id = fields.Many2one('school.teacher', string='Class Teacher')
    capacity = fields.Integer(string='Maximum Capacity', default=30)
    current_students = fields.Integer(string='Current Students', compute='_compute_current_students')
    section_ids = fields.One2many('school.section', 'class_id', string='Sections')
    subject_ids = fields.Many2many('school.subject', string='Subjects')
    
    @api.depends('section_ids.student_ids')
    def _compute_current_students(self):
        for class_rec in self:
            total_students = 0
            for section in class_rec.section_ids:
                total_students += len(section.student_ids)
            class_rec.current_students = total_students

class SchoolSection(models.Model):
    _name = 'school.section'
    _description = 'Class Section'
    
    name = fields.Char(string='Section Name', required=True)
    class_id = fields.Many2one('school.class', string='Class', required=True)
    class_teacher_id = fields.Many2one('school.teacher', string='Section Teacher')
    student_ids = fields.One2many('school.student', 'section_id', string='Students')
    room_number = fields.Char(string='Room Number')
```

### Teacher Management Model

```python
class SchoolTeacher(models.Model):
    _name = 'school.teacher'
    _description = 'Teacher Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    teacher_id = fields.Char(string='Teacher ID', required=True, copy=False, readonly=True,
                           default=lambda self: 'New')
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    display_name = fields.Char(string='Teacher Name', compute='_compute_display_name', store=True)
    
    # Professional Information
    qualification = fields.Selection([
        ('bachelor', 'Bachelor Degree'),
        ('master', 'Master Degree'),
        ('phd', 'PhD'),
        ('other', 'Other')
    ], string='Highest Qualification')
    specialization = fields.Char(string='Specialization')
    joining_date = fields.Date(string='Joining Date', default=fields.Date.today)
    experience_years = fields.Integer(string='Years of Experience')
    
    # Employment Details
    department_id = fields.Many2one('school.department', string='Department')
    subjects_ids = fields.Many2many('school.subject', string='Subjects')
    is_class_teacher = fields.Boolean(string='Is Class Teacher')
    class_id = fields.Many2one('school.class', string='Assigned Class')
    section_id = fields.Many2one('school.section', string='Assigned Section')
    
    # Contact Information
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    
    # Status
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave')
    ], string='Status', default='active')
    
    # Relationships
    timetable_ids = fields.One2many('school.timetable', 'teacher_id', string='Timetable')
    
    @api.depends('first_name', 'last_name')
    def _compute_display_name(self):
        for teacher in self:
            teacher.display_name = f"{teacher.first_name} {teacher.last_name}"
    
    @api.model
    def create(self, vals):
        if vals.get('teacher_id', 'New') == 'New':
            vals['teacher_id'] = self.env['ir.sequence'].next_by_code('school.teacher.id') or 'New'
        return super().create(vals)
```

## 2. SMIS Server Actions

### Automated Student Registration Server Action

```python
# Server Action: Auto Register Student with Validation
def auto_register_student(records):
    """
    Server action to automatically register new students with comprehensive validation
    """
    Student = env['school.student']
    AcademicYear = env['school.academic.year']
    
    try:
        registered_students = []
        
        for record in records:
            # Validate required fields
            if not record.get('first_name') or not record.get('last_name'):
                raise UserError("First name and Last name are required")
            
            # Get current academic year
            current_year = AcademicYear.search([('is_current', '=', True)], limit=1)
            if not current_year:
                raise UserError("No current academic year found! Please set up academic years first.")
            
            # Generate roll number automatically
            class_id = record.get('class_id')
            if class_id:
                existing_students = Student.search([('class_id', '=', class_id)])
                next_roll = max([s.roll_number for s in existing_students] or [0]) + 1
            else:
                next_roll = 1
            
            # Create student record
            student_vals = {
                'first_name': record.get('first_name'),
                'last_name': record.get('last_name'),
                'date_of_birth': record.get('date_of_birth'),
                'gender': record.get('gender', 'other'),
                'class_id': class_id,
                'section_id': record.get('section_id'),
                'academic_year_id': current_year.id,
                'roll_number': next_roll,
                'parent_id': record.get('parent_id'),
                'phone': record.get('phone'),
                'email': record.get('email'),
                'address': record.get('address'),
            }
            
            student = Student.create(student_vals)
            registered_students.append(student.display_name)
            
            # Create welcome activity for class teacher
            if student.class_id and student.class_id.class_teacher_id:
                student.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=f'New Student: {student.display_name}',
                    note=f'New student {student.display_name} has been assigned to your class.',
                    user_id=student.class_id.class_teacher_id.user_id.id
                )
            
            # Auto-generate fee record
            if record.get('auto_generate_fee', True):
                student._generate_initial_fee()
        
        # Return success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Student Registration Successful',
                'message': f'Successfully registered {len(registered_students)} students: {", ".join(registered_students)}',
                'type': 'success',
                'sticky': True,
            }
        }
        
    except Exception as e:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Registration Failed',
                'message': f'Failed to register student: {str(e)}',
                'type': 'danger',
                'sticky': True,
            }
        }
```

### Bulk Attendance Management Server Action

```python
# Server Action: Mark Bulk Attendance
def mark_bulk_attendance(records):
    """
    Server action to mark attendance for multiple students
    """
    Attendance = env['school.attendance']
    
    try:
        today = fields.Date.today()
        attendance_count = 0
        
        for record in records:
            # Check if attendance already exists for today
            existing_attendance = Attendance.search([
                ('student_id', '=', record.id),
                ('date', '=', today)
            ])
            
            if not existing_attendance:
                # Create attendance record
                attendance_vals = {
                    'student_id': record.id,
                    'date': today,
                    'status': 'present',  # Default status
                    'class_id': record.class_id.id,
                    'section_id': record.section_id.id,
                }
                Attendance.create(attendance_vals)
                attendance_count += 1
        
        # Return summary
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Attendance Marked',
                'message': f'Attendance marked for {attendance_count} students for {today}',
                'type': 'success',
                'sticky': False,
            }
        }
        
    except Exception as e:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Attendance Failed',
                'message': f'Error marking attendance: {str(e)}',
                'type': 'danger',
                'sticky': True,
            }
        }
```

## 3. SMIS Automated Actions (Scheduled)

### Automated Attendance System

```python
class SMISAutomatedTasks(models.Model):
    _name = 'smis.automated.tasks'
    _description = 'SMIS Automated Tasks'
    
    def auto_generate_daily_attendance(self):
        """
        Automated action: Generate daily attendance records for all active students
        """
        try:
            today = fields.Date.today()
            Attendance = self.env['school.attendance']
            
            # Get all active students
            active_students = self.env['school.student'].search([
                ('status', '=', 'active')
            ])
            
            generated_count = 0
            for student in active_students:
                # Check if attendance already exists for today
                existing = Attendance.search([
                    ('student_id', '=', student.id),
                    ('date', '=', today)
                ])
                
                if not existing:
                    # Create attendance record with 'absent' as default
                    Attendance.create({
                        'student_id': student.id,
                        'date': today,
                        'status': 'absent',  # Default to absent, to be updated by teachers
                        'class_id': student.class_id.id,
                        'section_id': student.section_id.id,
                    })
                    generated_count += 1
            
            _logger.info(f"Generated {generated_count} daily attendance records for {today}")
            return generated_count
            
        except Exception as e:
            _logger.error(f"Daily attendance generation failed: {str(e)}")
            return 0
    
    def auto_send_attendance_report_to_parents(self):
        """
        Automated action: Send weekly attendance report to parents
        """
        try:
            # Calculate last week dates
            today = fields.Date.today()
            start_of_week = today - timedelta(days=today.weekday() + 7)
            end_of_week = start_of_week + timedelta(days=6)
            
            # Get students with poor attendance (< 75%)
            students = self.env['school.student'].search([('status', '=', 'active')])
            
            report_count = 0
            for student in students:
                # Calculate attendance for the week
                weekly_attendance = self.env['school.attendance'].search([
                    ('student_id', '=', student.id),
                    ('date', '>=', start_of_week),
                    ('date', '<=', end_of_week)
                ])
                
                if weekly_attendance:
                    present_days = len(weekly_attendance.filtered(lambda a: a.status == 'present'))
                    total_days = len(weekly_attendance)
                    attendance_percentage = (present_days / total_days) * 100 if total_days > 0 else 0
                    
                    # Send report if attendance is below 75%
                    if attendance_percentage < 75 and student.parent_id and student.parent_id.email:
                        # Send email to parent
                        template = self.env.ref('school_management.email_template_attendance_report')
                        template.send_mail(student.id, force_send=False)
                        report_count += 1
            
            _logger.info(f"Sent {report_count} attendance reports to parents")
            return report_count
            
        except Exception as e:
            _logger.error(f"Attendance report sending failed: {str(e)}")
            return 0
    
    def auto_promote_students(self):
        """
        Automated action: Promote students to next class at end of academic year
        """
        try:
            current_year = self.env['school.academic.year'].search([('is_current', '=', True)], limit=1)
            if not current_year or fields.Date.today() < current_year.end_date:
                return 0  # Not yet time for promotion
            
            # Find students to promote
            students_to_promote = self.env['school.student'].search([
                ('status', '=', 'active'),
                ('academic_year_id', '=', current_year.id)
            ])
            
            promoted_count = 0
            for student in students_to_promote:
                # Get next class logic (you might have your own promotion rules)
                next_class = self._get_next_class(student.class_id)
                if next_class:
                    student.write({
                        'class_id': next_class.id,
                        'roll_number': 0,  # Reset roll number for new class
                    })
                    promoted_count += 1
            
            _logger.info(f"Automatically promoted {promoted_count} students")
            return promoted_count
            
        except Exception as e:
            _logger.error(f"Student promotion failed: {str(e)}")
            return 0
    
    def _get_next_class(self, current_class):
        """Determine next class based on current class"""
        # Example: Simple increment-based promotion
        # You might want to implement more complex logic
        if current_class:
            next_class_code = self._increment_class_code(current_class.code)
            return self.env['school.class'].search([('code', '=', next_class_code)], limit=1)
        return False
    
    def _increment_class_code(self, code):
        """Increment class code (e.g., '1A' -> '2A')"""
        try:
            numeric_part = ''.join(filter(str.isdigit, code))
            non_numeric_part = ''.join(filter(str.isalpha, code))
            if numeric_part:
                new_numeric = str(int(numeric_part) + 1)
                return new_numeric + non_numeric_part
        except:
            pass
        return code
```

## 4. Fee Management System

```python
class SchoolFee(models.Model):
    _name = 'school.fee'
    _description = 'Student Fee Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Fee Reference', readonly=True, default='New')
    student_id = fields.Many2one('school.student', string='Student', required=True)
    academic_year_id = fields.Many2one('school.academic.year', string='Academic Year', required=True)
    fee_type_id = fields.Many2one('school.fee.type', string='Fee Type', required=True)
    amount = fields.Float(string='Amount', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    payment_date = fields.Date(string='Payment Date')
    paid_amount = fields.Float(string='Paid Amount')
    balance = fields.Float(string='Balance', compute='_compute_balance')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('due', 'Due'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue')
    ], string='Status', default='draft', tracking=True)
    
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment')
    ], string='Payment Method')
    
    @api.depends('amount', 'paid_amount')
    def _compute_balance(self):
        for fee in self:
            fee.balance = fee.amount - fee.paid_amount
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('school.fee') or 'New'
        return super().create(vals)
    
    def action_mark_paid(self):
        """Mark fee as fully paid"""
        for fee in self:
            fee.write({
                'paid_amount': fee.amount,
                'payment_date': fields.Date.today(),
                'state': 'paid'
            })
    
    def action_send_reminder(self):
        """Send fee reminder to parent"""
        for fee in self:
            if fee.student_id.parent_id and fee.student_id.parent_id.email:
                template = self.env.ref('school_management.email_template_fee_reminder')
                template.send_mail(fee.id, force_send=False)

class SchoolFeeType(models.Model):
    _name = 'school.fee.type'
    _description = 'Fee Type'
    
    name = fields.Char(string='Fee Type', required=True)
    code = fields.Char(string='Code', required=True)
    amount = fields.Float(string='Default Amount', required=True)
    description = fields.Text(string='Description')
    is_recurring = fields.Boolean(string='Is Recurring')
    recurrence = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Recurrence')
```

## 5. Timetable Management

```python
class SchoolTimetable(models.Model):
    _name = 'school.timetable'
    _description = 'School Timetable'
    
    name = fields.Char(string='Period', compute='_compute_period_name')
    class_id = fields.Many2one('school.class', string='Class', required=True)
    section_id = fields.Many2one('school.section', string='Section')
    subject_id = fields.Many2one('school.subject', string='Subject', required=True)
    teacher_id = fields.Many2one('school.teacher', string='Teacher', required=True)
    day_of_week = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday')
    ], string='Day', required=True)
    start_time = fields.Float(string='Start Time', required=True)
    end_time = fields.Float(string='End Time', required=True)
    room_id = fields.Many2one('school.room', string='Room')
    
    @api.depends('day_of_week', 'start_time', 'subject_id')
    def _compute_period_name(self):
        for timetable in self:
            day = dict(timetable._fields['day_of_week'].selection).get(timetable.day_of_week)
            start = self._float_to_time(timetable.start_time)
            timetable.name = f"{day} - {start} - {timetable.subject_id.name}"
    
    def _float_to_time(self, float_time):
        """Convert float time to readable time format"""
        hours = int(float_time)
        minutes = int((float_time - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
```

## 6. Grading and Assessment System

```python
class SchoolGrade(models.Model):
    _name = 'school.grade'
    _description = 'Student Grades'
    
    student_id = fields.Many2one('school.student', string='Student', required=True)
    subject_id = fields.Many2one('school.subject', string='Subject', required=True)
    academic_year_id = fields.Many2one('school.academic.year', string='Academic Year', required=True)
    exam_type = fields.Selection([
        ('quarterly', 'Quarterly Exam'),
        ('half_yearly', 'Half Yearly Exam'),
        ('final', 'Final Exam'),
        ('assignment', 'Assignment'),
        ('project', 'Project')
    ], string='Exam Type', required=True)
    
    marks_obtained = fields.Float(string='Marks Obtained')
    total_marks = fields.Float(string='Total Marks', default=100)
    percentage = fields.Float(string='Percentage', compute='_compute_percentage', store=True)
    grade = fields.Char(string='Grade', compute='_compute_grade', store=True)
    
    @api.depends('marks_obtained', 'total_marks')
    def _compute_percentage(self):
        for grade in self:
            if grade.total_marks > 0:
                grade.percentage = (grade.marks_obtained / grade.total_marks) * 100
            else:
                grade.percentage = 0
    
    @api.depends('percentage')
    def _compute_grade(self):
        for grade in self:
            percentage = grade.percentage
            if percentage >= 90:
                grade.grade = 'A+'
            elif percentage >= 80:
                grade.grade = 'A'
            elif percentage >= 70:
                grade.grade = 'B'
            elif percentage >= 60:
                grade.grade = 'C'
            elif percentage >= 50:
                grade.grade = 'D'
            else:
                grade.grade = 'F'
```

## 7. SMIS Reporting and Analytics

```python
class SMISReporting(models.Model):
    _name = 'smis.reporting'
    _description = 'SMIS Reporting and Analytics'
    
    def get_daily_school_report(self):
        """Generate daily school report"""
        current_date = fields.Date.today()
        
        report_data = {
            'report_date': current_date,
            'total_students': self.env['school.student'].search_count([('status', '=', 'active')]),
            'total_teachers': self.env['school.teacher'].search_count([('status', '=', 'active')]),
            'attendance_today': self.env['school.attendance'].search_count([
                ('date', '=', current_date),
                ('status', '=', 'present')
            ]),
            'absent_today': self.env['school.attendance'].search_count([
                ('date', '=', current_date),
                ('status', '=', 'absent')
            ]),
            'fee_collection_today': sum(
                self.env['school.fee'].search([
                    ('payment_date', '=', current_date),
                    ('state', '=', 'paid')
                ]).mapped('paid_amount')
            ),
        }
        
        return report_data
    
    def get_class_wise_performance(self, academic_year_id, exam_type):
        """Generate class-wise performance report"""
        classes = self.env['school.class'].search([])
        
        performance_data = []
        for class_rec in classes:
            # Get all students in this class
            students = self.env['school.student'].search([
                ('class_id', '=', class_rec.id),
                ('academic_year_id', '=', academic_year_id)
            ])
            
            if students:
                # Calculate average percentage for the class
                grades = self.env['school.grade'].search([
                    ('student_id', 'in', students.ids),
                    ('academic_year_id', '=', academic_year_id),
                    ('exam_type', '=', exam_type)
                ])
                
                if grades:
                    avg_percentage = sum(grades.mapped('percentage')) / len(grades)
                    
                    performance_data.append({
                        'class_name': class_rec.name,
                        'total_students': len(students),
                        'average_percentage': round(avg_percentage, 2),
                        'class_teacher': class_rec.class_teacher_id.display_name if class_rec.class_teacher_id else 'N/A'
                    })
        
        return performance_data
```

## 8. SMIS Security and Access Control

```python
class SMISCustomSecurity(models.Model):
    _inherit = 'res.users'
    
    def check_smis_access_rights(self, model_name, operation='read'):
        """
        Custom access control for SMIS modules
        """
        # Define role-based access matrix
        access_matrix = {
            'school.student': {
                'teacher': ['read'],
                'class_teacher': ['read', 'write'],
                'admin': ['read', 'write', 'create', 'unlink']
            },
            'school.grade': {
                'teacher': ['read', 'write', 'create'],
                'class_teacher': ['read', 'write', 'create'],
                'admin': ['read', 'write', 'create', 'unlink']
            },
            'school.fee': {
                'accountant': ['read', 'write', 'create'],
                'admin': ['read', 'write', 'create', 'unlink']
            }
        }
        
        user_groups = self.groups_id.mapped('name')
        model_access = access_matrix.get(model_name, {})
        
        for group in user_groups:
            if group in model_access and operation in model_access[group]:
                return True
        
   