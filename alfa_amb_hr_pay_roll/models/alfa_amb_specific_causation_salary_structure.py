# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from collections import defaultdict
import math

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class AlfaAmbSpecificCausationSS(models.Model):

	_name = 'alfa.amb_specific_cau_sal_str'


	rule_id = fields.Many2one('hr.salary.rule', 
		string = 'Regla Salarial')


	struct_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial')

	analytic_account_id = fields.Many2one('account.analytic.account', 
		string = u'Cuenta Analítica')

	account_tax_id = fields.Many2one('account.tax', string = 'Impuesto')

	account_debit = fields.Many2one('account.account', 
		string = u'Cuenta Débito', 
		domain=[('deprecated', '=', False)])

	account_credit = fields.Many2one('account.account', 
		string = 'Cuenta Crédito', 
		domain=[('deprecated', '=', False)])
