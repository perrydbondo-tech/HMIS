# Recreate the combined Odoo module skeleton "lta_operator_management" with models and zip it.
import os, zipfile, textwrap, shutil

base_dir = "/mnt/data/lta_operator_management"
zip_path = "/mnt/data/lta_operator_management_module.zip"

# Clean up if exists
if os.path.exists(base_dir):
    shutil.rmtree(base_dir)
if os.path.exists(zip_path):
    os.remove(zip_path)

dirs = [
    base_dir,
    os.path.join(base_dir, "models"),
    os.path.join(base_dir, "views"),
    os.path.join(base_dir, "security"),
    os.path.join(base_dir, "data"),
    os.path.join(base_dir, "reports"),
    os.path.join(base_dir, "wizards"),
    os.path.join(base_dir, "static"),
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

files = {
    "__manifest__.py": textwrap.dedent("""\
        {
            'name': 'LTA Operator Management',
            'version': '1.0.0',
            'category': 'Localization/Regulatory',
            'summary': 'Operator Registry, Licenses, Sites and UAF management for LTA',
            'description': 'This module provides skeleton models, views and reports for managing operators, licenses, sites, and UAF contributors.',
            'author': 'Implementation Team',
            'website': 'https://example.org',
            'depends': ['base','contacts','documents','account','hr'],
            'data': [
                'security/security.xml',
                'security/ir.model.access.csv',
                'data/lta_operator_type.xml',
                'views/lta_operator_views.xml',
                'views/lta_license_views.xml',
                'views/lta_site_views.xml',
                'views/lta_uaf_views.xml',
                'reports/lta_reports.xml',
                'data/cron_jobs.xml',
            ],
            'installable': True,
            'application': False,
        }
    """),
    "__init__.py": textwrap.dedent("""\
        from . import models
        from . import wizards
    """),
    "README.md": textwrap.dedent("""\
        LTA Operator Management - Odoo module skeleton
        ==============================================
        Contains skeleton models for:
         - lta.operator.profile (extends res.partner)
         - lta.license
         - lta.site
         - lta.uaf.payment / declaration

        Installation:
         1. Copy this folder to your Odoo addons path.
         2. Restart Odoo service.
         3. Update Apps and install 'LTA Operator Management'.
         4. Configure user groups and follow the implementation checklist.
    """),
    "models/__init__.py": textwrap.dedent("""\
        from . import lta_operator_profile
        from . import lta_license
        from . import lta_site
        from . import lta_uaf
    """),
    "models/lta_operator_profile.py": textwrap.dedent("""\
        from odoo import models, fields, api

        class LtaOperatorProfile(models.Model):
            _name = 'lta.operator.profile'
            _description = 'LTA Operator Profile'
            _inherit = ['mail.thread', 'mail.activity.mixin']

            partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade')
            operator_code = fields.Char(string='Operator Code', required=True)
            operator_type = fields.Selection([('mno','MNO'),('isp','ISP'),('vsat','VSAT'),('tv','TV'),('fm','FM')], string='Operator Type', required=True)
            legal_name = fields.Char(string='Legal Name')
            trading_name = fields.Char(string='Trading Name')
            tin = fields.Char(string='Tax ID (TIN)')
            registration_no = fields.Char(string='Registration No.')
            is_uaf_contributor = fields.Boolean(string='UAF Contributor', default=False)
            uaf_rate = fields.Float(string='UAF Rate', digits=(6,4))
            status = fields.Selection([('active','Active'),('suspended','Suspended'),('revoked','Revoked'),('pending','Pending')], default='pending')
            license_count = fields.Integer(string='License Count', compute='_compute_license_count')
            created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.uid)

            @api.depends('partner_id')
            def _compute_license_count(self):
                for rec in self:
                    count = self.env['lta.license'].search_count([('operator_profile_id','=',rec.id)])
                    rec.license_count = count

            def name_get(self):
                result = []
                for rec in self:
                    name = rec.partner_id.name or rec.operator_code
                    result.append((rec.id, "%s [%s]" % (name, rec.operator_code)))
                return result
    """),
    "models/lta_license.py": textwrap.dedent("""\
        from odoo import models, fields, api

        class LtaLicense(models.Model):
            _name = 'lta.license'
            _description = 'LTA License'
            _inherit = ['mail.thread']

            operator_profile_id = fields.Many2one('lta.operator.profile', string='Operator', required=True, ondelete='cascade')
            license_number = fields.Char(string='License Number', required=True)
            license_type = fields.Selection([('operator','Operator'),('spectrum','Spectrum'),('site','Site')], string='License Type', required=True)
            issue_date = fields.Date(string='Issue Date')
            expiry_date = fields.Date(string='Expiry Date')
            fee_amount = fields.Monetary(string='Fee', currency_field='currency_id')
            currency_id = fields.Many2one('res.currency', string='Currency')
            status = fields.Selection([('active','Active'),('expired','Expired'),('suspended','Suspended'),('revoked','Revoked')], default='active')
            conditions = fields.Text(string='Conditions')
            document_ids = fields.Many2many('documents.document', string='Attached Documents')
            created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.uid)
    """),
    "models/lta_site.py": textwrap.dedent("""\
        from odoo import models, fields, api

        class LtaSite(models.Model):
            _name = 'lta.site'
            _description = 'LTA Site / Tower'
            _inherit = ['mail.thread']

            site_code = fields.Char(string='Site Code', required=True)
            name = fields.Char(string='Name')
            operator_profile_id = fields.Many2one('lta.operator.profile', string='Operator')
            site_type = fields.Selection([('tower','Tower'),('exchange','Exchange'),('datacenter','Datacenter'),('hub','Hub')], string='Site Type')
            address = fields.Text(string='Address')
            latitude = fields.Float(string='Latitude', digits=(9,6))
            longitude = fields.Float(string='Longitude', digits=(9,6))
            installation_date = fields.Date(string='Installation Date')
            co_location = fields.Boolean(string='Co-location Available', default=False)
            active = fields.Boolean(string='Active', default=True)
            infrastructure = fields.One2many('lta.site.infrastructure','site_id', string='Infrastructure')
    """),
    "models/lta_uaf.py": textwrap.dedent("""\
        from odoo import models, fields, api

        class LtaUafDeclaration(models.Model):
            _name = 'lta.uaf.declaration'
            _description = 'LTA UAF Declaration'

            operator_profile_id = fields.Many2one('lta.operator.profile', string='Operator', required=True)
            period_start = fields.Date(string='Period Start', required=True)
            period_end = fields.Date(string='Period End', required=True)
            declared_amount = fields.Monetary(string='Declared Amount', currency_field='currency_id')
            currency_id = fields.Many2one('res.currency', string='Currency')
            state = fields.Selection([('draft','Draft'),('verified','Verified'),('invoiced','Invoiced'),('paid','Paid')], default='draft')
            invoice_id = fields.Many2one('account.move', string='Linked Invoice')
            payment_id = fields.Many2one('account.payment', string='Linked Payment')
            notes = fields.Text(string='Notes')

        class LtaUafPayment(models.Model):
            _name = 'lta.uaf.payment'
            _description = 'LTA UAF Payment'

            declaration_id = fields.Many2one('lta.uaf.declaration', string='Declaration', required=True, ondelete='cascade')
            amount = fields.Monetary(string='Amount', currency_field='currency_id')
            currency_id = fields.Many2one('res.currency', string='Currency')
            payment_date = fields.Date(string='Payment Date')
            received_by = fields.Many2one('res.users', string='Received By')
    """),
    "views/lta_operator_views.xml": textwrap.dedent("""\
        <odoo>
          <record id="view_lta_operator_form" model="ir.ui.view">
            <field name="name">lta.operator.form</field>
            <field name="model">lta.operator.profile</field>
            <field name="arch" type="xml">
              <form string="Operator Profile">
                <sheet>
                  <group>
                    <field name="partner_id" />
                    <field name="operator_code"/>
                    <field name="operator_type"/>
                    <field name="status"/>
                    <field name="is_uaf_contributor"/>
                    <field name="uaf_rate"/>
                  </group>
                  <notebook>
                    <page string="Details">
                      <group>
                        <field name="legal_name"/>
                        <field name="trading_name"/>
                        <field name="tin"/>
                        <field name="registration_no"/>
                      </group>
                    </page>
                    <page string="Licenses">
                      <field name="license_count" readonly="1"/>
                      <field name="partner_id" widget="many2one"/>
                    </page>
                  </notebook>
                </sheet>
              </form>
            </field>
          </record>

          <record id="view_lta_operator_tree" model="ir.ui.view">
            <field name="name">lta.operator.tree</field>
            <field name="model">lta.operator.profile</field>
            <field name="arch" type="xml">
              <tree string="Operators">
                <field name="partner_id"/>
                <field name="operator_code"/>
                <field name="operator_type"/>
                <field name="status"/>
                <field name="is_uaf_contributor"/>
              </tree>
            </field>
          </record>

          <menuitem id="menu_lta_root" name="LTA" sequence="10"/>
          <menuitem id="menu_lta_operator" name="Operators" parent="menu_lta_root"/>
          <record id="action_lta_operator" model="ir.actions.act_window">
            <field name="name">Operators</field>
            <field name="res_model">lta.operator.profile</field>
            <field name="view_mode">tree,form</field>
          </record>
          <menuitem id="menu_lta_operator_action" name="Manage Operators" parent="menu_lta_operator" action="action_lta_operator"/>
        </odoo>
    """),
    "views/lta_license_views.xml": textwrap.dedent("""\
        <odoo>
          <record id="view_lta_license_form" model="ir.ui.view">
            <field name="name">lta.license.form</field>
            <field name="model">lta.license</field>
            <field name="arch" type="xml">
              <form string="License">
                <sheet>
                  <group>
                    <field name="operator_profile_id"/>
                    <field name="license_number"/>
                    <field name="license_type"/>
                    <field name="issue_date"/>
                    <field name="expiry_date"/>
                    <field name="fee_amount"/>
                    <field name="status"/>
                  </group>
                  <group>
                    <field name="conditions"/>
                    <field name="document_ids" widget="many2many_tags"/>
                  </group>
                </sheet>
              </form>
            </field>
          </record>

          <record id="view_lta_license_tree" model="ir.ui.view">
            <field name="name">lta.license.tree</field>
            <field name="model">lta.license</field>
            <field name="arch" type="xml">
              <tree string="Licenses">
                <field name="license_number"/>
                <field name="operator_profile_id"/>
                <field name="license_type"/>
                <field name="expiry_date"/>
                <field name="status"/>
              </tree>
            </field>
          </record>

          <menuitem id="menu_lta_license" name="Licenses" parent="menu_lta_root"/>
          <record id="action_lta_license" model="ir.actions.act_window">
            <field name="name">Licenses</field>
            <field name="res_model">lta.license</field>
            <field name="view_mode">tree,form</field>
          </record>
          <menuitem id="menu_lta_license_action" name="Manage Licenses" parent="menu_lta_license" action="action_lta_license"/>
        </odoo>
    """),
    "views/lta_site_views.xml": textwrap.dedent("""\
        <odoo>
          <record id="view_lta_site_form" model="ir.ui.view">
            <field name="name">lta.site.form</field>
            <field name="model">lta.site</field>
            <field name="arch" type="xml">
              <form string="Site / Tower">
                <sheet>
                  <group>
                    <field name="site_code"/>
                    <field name="name"/>
                    <field name="operator_profile_id"/>
                    <field name="site_type"/>
                    <field name="address"/>
                  </group>
                  <group>
                    <field name="latitude"/>
                    <field name="longitude"/>
                    <field name="installation_date"/>
                    <field name="co_location"/>
                    <field name="active"/>
                  </group>
                </sheet>
              </form>
            </field>
          </record>

          <record id="view_lta_site_tree" model="ir.ui.view">
            <field name="name">lta.site.tree</field>
            <field name="model">lta.site</field>
            <field name="arch" type="xml">
              <tree string="Sites">
                <field name="site_code"/>
                <field name="name"/>
                <field name="operator_profile_id"/>
                <field name="site_type"/>
                <field name="active"/>
              </tree>
            </field>
          </record>

          <menuitem id="menu_lta_site" name="Sites" parent="menu_lta_root"/>
          <record id="action_lta_site" model="ir.actions.act_window">
            <field name="name">Sites</field>
            <field name="res_model">lta.site</field>
            <field name="view_mode">tree,form</field>
          </record>
          <menuitem id="menu_lta_site_action" name="Manage Sites" parent="menu_lta_site" action="action_lta_site"/>
        </odoo>
    """),
    "views/lta_uaf_views.xml": textwrap.dedent("""\
        <odoo>
          <record id="view_lta_uaf_declaration_form" model="ir.ui.view">
            <field name="name">lta.uaf.declaration.form</field>
            <field name="model">lta.uaf.declaration</field>
            <field name="arch" type="xml">
              <form string="UAF Declaration">
                <sheet>
                  <group>
                    <field name="operator_profile_id"/>
                    <field name="period_start"/>
                    <field name="period_end"/>
                    <field name="declared_amount"/>
                    <field name="state"/>
                    <field name="invoice_id"/>
                  </group>
                  <group>
                    <field name="notes"/>
                  </group>
                </sheet>
              </form>
            </field>
          </record>

          <record id="view_lta_uaf_tree" model="ir.ui.view">
            <field name="name">lta.uaf.tree</field>
            <field name="model">lta.uaf.declaration</field>
            <field name="arch" type="xml">
              <tree string="UAF Declarations">
                <field name="operator_profile_id"/>
                <field name="period_start"/>
                <field name="period_end"/>
                <field name="declared_amount"/>
                <field name="state"/>
              </tree>
            </field>
          </record>

          <menuitem id="menu_lta_uaf" name="UAF" parent="menu_lta_root"/>
          <record id="action_lta_uaf" model="ir.actions.act_window">
            <field name="name">UAF Declarations</field>
            <field name="res_model">lta.uaf.declaration</field>
            <field name="view_mode">tree,form</field>
          </record>
          <menuitem id="menu_lta_uaf_action" name="Manage UAF" parent="menu_lta_uaf" action="action_lta_uaf"/>
        </odoo>
    """),
    "reports/lta_reports.xml": textwrap.dedent("""\
        <odoo>
          <report id='report_expiring_licenses' model='lta.license' string='Expiring Licenses' report_type='qweb-pdf' name='lta_operator_management.report_expiring_licenses' file='lta_operator_management.report_expiring_licenses'/>
          <template id='report_expiring_licenses_template'>
            <t t-call='web.html_container'>
              <div class='page'>
                <h2>Expiring Licenses Report</h2>
                <table class='table table-sm'>
                  <thead><tr><th>License</th><th>Operator</th><th>Expiry</th><th>Status</th></tr></thead>
                  <tbody>
                    <t t-foreach='docs' t-as='o'>
                      <tr>
                        <td><t t-esc='o.license_number'/></td>
                        <td><t t-esc='o.operator_profile_id.partner_id.name or \"-\"'/></td>
                        <td><t t-esc='o.expiry_date or \"-\"'/></td>
                        <td><t t-esc='o.status'/></td>
                      </tr>
                    </t>
                  </tbody>
                </table>
              </div>
            </t>
          </template>
        </odoo>
    """),
    "security/security.xml": textwrap.dedent("""\
        <odoo>
          <record id='group_lta_regulatory' model='res.groups'>
            <field name='name'>LTA Regulatory Officer</field>
            <field name='category_id' ref='base.module_category_hidden'/>
          </record>
          <record id='group_lta_uaf' model='res.groups'>
            <field name='name'>LTA UAF Officer</field>
            <field name='category_id' ref='base.module_category_hidden'/>
          </record>
        </odoo>
    """),
    "security/ir.model.access.csv": "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\naccess_lta_operator_profile,lta.operator.profile,model_lta_operator_profile,,1,1,1,1\naccess_lta_license,lta.license,model_lta_license,,1,1,1,1\naccess_lta_site,lta.site,model_lta_site,,1,1,1,1\naccess_lta_uaf_declaration,lta.uaf.declaration,model_lta_uaf_declaration,,1,1,1,1\naccess_lta_uaf_payment,lta.uaf.payment,model_lta_uaf_payment,,1,1,1,1\n",
    "data/lta_operator_type.xml": textwrap.dedent("""\
        <odoo>
          <record id='lta_operator_type_mno' model='lta.operator.type'>
            <field name='name'>MNO</field>
            <field name='code'>mno</field>
          </record>
        </odoo>
    """),
    "data/cron_jobs.xml": textwrap.dedent("""\
        <odoo>
          <record id='ir_cron_lta_license_reminder' model='ir.cron'>
            <field name='name'>LTA License Expiry Reminder</field>
            <field name='model_id' ref='base.model_ir_cron'/>
            <field name='state'>code</field>
            <field name='code'>model.env['lta.license'].search([('expiry_date','&lt;', fields.Date.context_today(self)+relativedelta(days=90)),('status','=','active')]).message_post(body='License expiring soon')</field>
            <field name='interval_number'>1</field>
            <field name='interval_type'>days</field>
            <field name='numbercall'>-1</field>
            <field name='active'>True</field>
          </record>
        </odoo>
    """),
    "wizards/__init__.py": textwrap.dedent("""\
        from . import generate_uaf_invoice
    """),
    "wizards/generate_uaf_invoice.py": textwrap.dedent("""\
        from odoo import models, fields, api

        class GenerateUafInvoiceWizard(models.TransientModel):
            _name = 'lta.generate.uaf.invoice'
            _description = 'Generate UAF Invoices'

            date_from = fields.Date(string='From', required=True)
            date_to = fields.Date(string='To', required=True)
            operator_ids = fields.Many2many('lta.operator.profile', string='Operators')

            def action_generate(self):
                # skeleton: create draft invoices for UAF declarations found
                declarations = self.env['lta.uaf.declaration'].search([('period_start','>=',self.date_from),('period_end','<=',self.date_to),('state','=','verified')])
                for d in declarations:
                    # create account.move here (omitted - skeleton)
                    d.state = 'invoiced'
                return True
    """),
}

# write files
for rel, content in files.items():
    path = os.path.join(base_dir, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# create zip
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, _, filenames in os.walk(base_dir):
        for fn in filenames:
            fp = os.path.join(root, fn)
            arcname = os.path.relpath(fp, base_dir)
            zf.write(fp, arcname)

# prepare output
created = []
for root, _, filenames in os.walk(base_dir):
    for fn in filenames:
        created.append(os.path.join(root, fn))

{"status":"ok","zip_path": zip_path, "files_count": len(created), "sample": created[:12]}
