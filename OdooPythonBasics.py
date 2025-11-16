## 1. Odoo Python Basics

### Odoo Models (ORM)

```python
from odoo import models, fields, api

class CustomModel(models.Model):
    _name = 'custom.model'
    _description = 'Custom Model'
    
    name = fields.Char(string='Name', required=True)
    value = fields.Float(string='Value')
    date = fields.Date(string='Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='Status', default='draft')
    
    # Many2one relationship
    partner_id = fields.Many2one('res.partner', string='Partner')
    
    # One2many relationship
    line_ids = fields.One2many('custom.model.line', 'parent_id', string='Lines')
```

### Model Inheritance

```python
class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    
    custom_field = fields.Char(string='Custom Field')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority')
    
    @api.depends('order_line', 'priority')
    def _compute_custom_total(self):
        for record in self:
            base_total = sum(line.price_total for line in record.order_line)
            if record.priority == 'high':
                record.custom_total = base_total * 1.1  # 10% premium
            else:
                record.custom_total = base_total
    
    custom_total = fields.Float(string='Custom Total', compute='_compute_custom_total')
```

## 2. Server Actions Tutorial

### Basic Server Action

```python
# Server Action Python Code
for record in records:
    if record.state == 'draft':
        record.write({
            'state': 'confirmed',
            'confirmation_date': fields.Datetime.now()
        })
        
        # Send notification
        record.message_post(
            body=f"Order {record.name} confirmed automatically",
            subject="Auto Confirmation"
        )
```

### Advanced Server Action with Error Handling

```python
# Server Action with comprehensive logic
try:
    processed_records = []
    for record in records:
        # Validation
        if not record.partner_id:
            raise UserError(f"Partner is required for record {record.name}")
        
        # Business logic
        if record.amount_total > 10000:
            record.write({
                'requires_approval': True,
                'state': 'waiting_approval'
            })
        else:
            record.write({
                'state': 'confirmed',
                'confirmed_by': env.user.id,
                'confirmation_date': fields.Datetime.now()
            })
        
        # Create related records
        if record.create_activity:
            env['mail.activity'].create({
                'activity_type_id': env.ref('mail.mail_activity_data_todo').id,
                'summary': f'Review {record.name}',
                'note': 'Please review this record',
                'user_id': record.user_id.id,
                'res_id': record.id,
                'res_model_id': env['ir.model']._get(record._name).id
            })
        
        processed_records.append(record.name)
    
    # Return success message
    if processed_records:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Processed records: {", ".join(processed_records)}',
                'type': 'success',
                'sticky': False,
            }
        }

except Exception as e:
    # Return error message
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': 'Error',
            'message': f'Action failed: {str(e)}',
            'type': 'danger',
            'sticky': True,
        }
    }
```

## 3. Automated Actions (Scheduled Actions)

### Scheduled Action Code

```python
def auto_process_orders(self):
    """Automatically process orders that meet certain criteria"""
    orders = self.env['sale.order'].search([
        ('state', '=', 'draft'),
        ('date_order', '<', fields.Datetime.now()),
        ('amount_total', '>', 0)
    ])
    
    processed_count = 0
    for order in orders:
        try:
            # Add your business logic here
            order.action_confirm()
            
            # Create invoice if needed
            if order.auto_invoice:
                invoice = order._create_invoices()
                invoice.action_post()
            
            processed_count += 1
            
        except Exception as e:
            # Log error but continue with other orders
            _logger.error(f"Failed to process order {order.name}: {str(e)}")
    
    _logger.info(f"Automatically processed {processed_count} orders")
    return processed_count
```

## 4. Button Actions and Business Methods

### Model Methods for Buttons

```python
class CustomModel(models.Model):
    _name = 'custom.model'
    _description = 'Custom Model'
    
    def action_confirm(self):
        """Button action to confirm records"""
        for record in self:
            if record.state != 'draft':
                continue
                
            record.write({
                'state': 'confirmed',
                'confirmed_by': self.env.uid,
                'confirmation_date': fields.Datetime.now()
            })
            
            # Trigger other actions
            record._send_confirmation_email()
            record._create_fulfillment_order()
        
        return True
    
    def action_cancel(self):
        """Button action to cancel records"""
        for record in self:
            record.write({
                'state': 'cancel',
                'cancelled_by': self.env.uid,
                'cancellation_date': fields.Datetime.now()
            })
    
    def _send_confirmation_email(self):
        """Private method to send confirmation email"""
        template = self.env.ref('your_module.email_template_confirmation')
        template.send_mail(self.id, force_send=True)
    
    def _create_fulfillment_order(self):
        """Create related fulfillment records"""
        fulfillment_vals = {
            'source_id': self.id,
            'partner_id': self.partner_id.id,
            'date_planned': fields.Datetime.now(),
            'lines': [(0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
            }) for line in self.line_ids]
        }
        return self.env['fulfillment.order'].create(fulfillment_vals)
```

## 5. Wizard and Transient Models

### Interactive Wizard

```python
class BulkUpdateWizard(models.TransientModel):
    _name = 'bulk.update.wizard'
    _description = 'Bulk Update Wizard'
    
    model_name = fields.Char(string='Model', required=True)
    field_name = fields.Char(string='Field to Update', required=True)
    new_value = fields.Char(string='New Value')
    domain = fields.Char(string='Domain', default='[]')
    
    def action_bulk_update(self):
        """Perform bulk update on selected records"""
        self.ensure_one()
        
        # Get the target model
        model = self.env[self.model_name]
        
        # Parse domain
        try:
            domain = eval(self.domain) if self.domain else []
        except:
            domain = []
        
        # Find records to update
        records = model.search(domain)
        
        if not records:
            raise UserError("No records found matching the criteria")
        
        # Prepare update values
        update_vals = {self.field_name: self.new_value}
        
        # Perform update
        records.write(update_vals)
        
        # Return success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Updated {len(records)} records',
                'type': 'success',
                'sticky': False,
            }
        }
```

## 6. Advanced Python Scripts

### Data Migration Script

```python
def migrate_customer_data(self):
    """Script to migrate customer data from old structure"""
    _logger.info("Starting customer data migration...")
    
    # Find all partners that need migration
    partners = self.env['res.partner'].search([
        ('customer_rank', '>', 0),
        ('x_legacy_id', '!=', False)  # Custom field for legacy ID
    ])
    
    migration_count = 0
    for partner in partners:
        try:
            # Migrate contact information
            migration_vals = {}
            
            if partner.x_legacy_code:
                migration_vals['ref'] = partner.x_legacy_code
            
            if partner.x_old_category:
                # Map old categories to new tags
                new_category = self._map_old_category(partner.x_old_category)
                if new_category:
                    migration_vals['category_id'] = [(4, new_category.id)]
            
            if migration_vals:
                partner.write(migration_vals)
                migration_count += 1
                
        except Exception as e:
            _logger.error(f"Failed to migrate partner {partner.id}: {str(e)}")
            continue
    
    _logger.info(f"Completed migration for {migration_count} partners")
    return migration_count

def _map_old_category(self, old_category):
    """Map old category to new category ID"""
    category_mapping = {
        'VIP': 'VIP Customer',
        'REGULAR': 'Regular Customer',
        'WHOLESALE': 'Wholesale Customer'
    }
    
    new_category_name = category_mapping.get(old_category)
    if new_category_name:
        return self.env['res.partner.category'].search([
            ('name', '=', new_category_name)
        ], limit=1)
    return False
```

### Report Generation Script

```python
def generate_sales_report(self, start_date, end_date):
    """Generate custom sales report"""
    # Query sales data
    query = """
        SELECT 
            so.name as order_number,
            rp.name as customer_name,
            so.date_order,
            so.amount_total,
            so.state,
            ru.name as salesperson
        FROM sale_order so
        JOIN res_partner rp ON so.partner_id = rp.id
        JOIN res_users ru ON so.user_id = ru.id
        WHERE so.date_order BETWEEN %s AND %s
        ORDER BY so.date_order DESC
    """
    
    self.env.cr.execute(query, (start_date, end_date))
    results = self.env.cr.dictfetchall()
    
    # Process results
    report_data = {
        'period': f"{start_date} to {end_date}",
        'total_orders': len(results),
        'total_revenue': sum(r['amount_total'] for r in results),
        'orders_by_state': {},
        'details': results
    }
    
    # Group by state
    for order in results:
        state = order['state']
        if state not in report_data['orders_by_state']:
            report_data['orders_by_state'][state] = 0
        report_data['orders_by_state'][state] += 1
    
    return report_data
```

## 7. Security and Access Control

### Record Rules and Access Rights

```python
class CustomModel(models.Model):
    _name = 'custom.model'
    _description = 'Custom Model'
    
    @api.model
    def _check_access_rights(self, operation, raise_exception=True):
        """Custom access rights check"""
        if operation == 'create' and not self.env.user.has_group('your_module.group_manager'):
            if raise_exception:
                raise AccessError("You are not allowed to create records")
            return False
        return super()._check_access_rights(operation, raise_exception)
    
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """Implement custom search domain"""
        # Add default domain to only show user's records
        if not self.env.user.has_group('your_module.group_see_all'):
            args = expression.AND([args, [('user_id', '=', self.env.uid)]])
        
        return super()._search(args, offset, limit, order, count, access_rights_uid)
```

## 8. Best Practices and Tips

### Error Handling

```python
def safe_record_operation(self, records, operation):
    """Safely perform operations on records with proper error handling"""
    successful = []
    failed = []
    
    for record in records:
        try:
            # Perform the operation
            if operation == 'confirm':
                record.action_confirm()
            elif operation == 'cancel':
                record.action_cancel()
            elif operation == 'archive':
                record.active = False
            
            successful.append(record.name)
            
        except Exception as e:
            failed.append({
                'record': record.name,
                'error': str(e)
            })
            _logger.error(f"Operation failed for {record.name}: {str(e)}")
    
    return {
        'successful': successful,
        'failed': failed
    }
```

### Performance Optimization

```python
def optimized_bulk_operations(self):
    """Example of optimized bulk operations"""
    # BAD: Loop with individual writes
    # for record in records:
    #     record.write({'state': 'done'})
    
    # GOOD: Bulk write
    records = self.search([('state', '=', 'draft')])
    if records:
        records.write({'state': 'done'})
    
    # Use read() for large datasets
    large_dataset = self.search([('state', '=', 'done')])
    data = large_dataset.read(['name', 'date', 'value'])
    
    # Use SQL for complex operations
    query = """
        UPDATE custom_model 
        SET state = 'processed' 
        WHERE state = 'draft' 
        AND date < %s
    """
    self.env.cr.execute(query, (fields.Date.today(),))
