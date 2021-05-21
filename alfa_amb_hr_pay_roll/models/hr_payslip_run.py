#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel, os

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):

	_inherit = 'hr.payslip.run'


	@api.multi
	def _get_has_slip_ids(self):
		
		for payslip_run in self:

			if payslip_run.slip_ids:
				payslip_run.has_slip_ids = True
			else:
				payslip_run.has_slip_ids = False

	has_slip_ids = fields.Boolean(string = u'¿Tiene Nóminas?', 
		compute = '_get_has_slip_ids', default = False)


	@api.multi
	def recalculate_payslips(self):
		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):
			for payslip in self.mapped('slip_ids'):
				payslip.compute_sheet()
		else:
			raise UserError(_('No esta autorizado para realizar esta acción'))

	@api.multi
	def confirm_payslips(self):
		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):
			for payslip in self.mapped('slip_ids'):
				payslip.action_payslip_done()
		else:
			raise UserError(_('No esta autorizado para realizar esta acción'))


	@api.multi
	def cancel_payslips(self):
		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):

			for payslip in self.mapped('slip_ids'):
				payslip.action_payslip_cancel()
		else:
			raise UserError(_('No esta autorizado para realizar esta acción'))

	@api.multi
	def update_news(self):
		for payslip in self.mapped('slip_ids').filtered(lambda slip: slip.state == 'draft'):
			payslip.update_news()



	@api.multi
	def print_multi_hr_payslip_run(self, hr_payslips):

		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):

			path = os.path.dirname(os.path.realpath(__file__))
			file_name, file_name_zip = self.env['hr.payslip'].get_file_names(path)
			self.env['hr.payslip'].print_multi_hr_payslip(hr_payslips)
			
			return {
				'type' : 'ir.actions.act_url',
				'url':   '/download/saveas?model=%(model)s&record_id=%(record_id)s&method=%(method)s&filename=%(filename)s'%
				{
					'filename': file_name+'.rar',
					'model': 'hr.payslip',
					'record_id': 0,
					'method': 'get_read_file',
				},
				'target': 'new',
			}
		else:
			raise UserError(_('No esta autorizado para realizar esta acción'))
		