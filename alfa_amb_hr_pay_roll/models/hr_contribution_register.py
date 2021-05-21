#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp


class HrContributionRegister(models.Model):

	_inherit = 'hr.contribution.register'


	partner_from_employee_contract = fields.Boolean(string = 'Seleccionar el partner desde el empleado', 
		default = False)

	field_id = fields.Many2one('ir.model.fields', 
		string = 'Campo', 
		domain = [('model_id.model', '=', 'hr.employee'), 
			('ttype', '=', 'many2one'), 
			('name', 'in', ('eps_id', 'afp_id', 'ccf_id', 'severance_id', 'arl_id'))])