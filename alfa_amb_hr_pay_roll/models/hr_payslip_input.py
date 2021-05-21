#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)

class HrPayslipInput(models.Model):

	_inherit = 'hr.payslip.input'

	note = fields.Text(string = 'Nota')
	show_on_report = fields.Boolean(string = 'Mostrar en reporte')
	is_monetary = fields.Boolean(string = u'Formato moneda en PDF',
		help = u"Si este campo está activo, en el reporte PDF de nómina se utilizará " 
			u"formato numérico en lugar de moneda")

	state_payslip = fields.Selection(string = u'Estado Nómina', related = 'payslip_id.state')