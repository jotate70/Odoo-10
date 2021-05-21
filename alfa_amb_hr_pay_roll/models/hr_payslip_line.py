#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)
class HrPayslipLine(models.Model):
	_inherit = 'hr.payslip.line'


	date_from = fields.Date(string=u'Fecha inicio nómina', related = 'slip_id.date_from')
	date_to = fields.Date(string=u'Fecha fin nómina', related = 'slip_id.date_to')

	sum_on_payroll = fields.Boolean(string=u'Suma en nómina', 
		related = 'salary_rule_id.sum_on_payroll')

	number_payslip = fields.Char(string=u'Referencia nómina', 
		related = 'slip_id.number')

	payslip_run_id = fields.Many2one('hr.payslip.run', related = 'slip_id.payslip_run_id', store = True)

	state = fields.Selection(related = 'slip_id.state', string = 'Estado nómina')

	def _get_partner_id(self, credit_account):
		
		res = super(HrPayslipLine, self)._get_partner_id(credit_account)

		if self.salary_rule_id.register_id.partner_from_employee_contract:

			baselocaldict = {
				'env': self.env,
				'uid': self._uid,
				'user': self.env.user,
				'self': self, 
			}

			field_name = self.salary_rule_id.register_id.field_id.name

			partner_id = safe_eval(str('self.employee_id.'+field_name+'.id'), baselocaldict)

			return partner_id

		if not res:

			register_partner_id = self.salary_rule_id.register_id.partner_id
			
			partner_id = register_partner_id.id or self.slip_id.employee_id.address_home_id.id
			
			if partner_id or register_partner_id:
				
				return partner_id or register_partner_id

		return res
		
