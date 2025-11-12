# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class medical_dose_unit(models.Model):
    _name = 'medical.dose.unit'

    name = fields.Char(string="Unit",required=True)
    description = fields.Char(string="Description")
    
    description = fields.Char(string="Description",
    help="Brief explanation of the medication unit.",
    required=True,
    translate=True,
    index=True,
    size=128
)

