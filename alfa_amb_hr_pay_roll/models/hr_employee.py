#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from babel.dates import format_datetime, format_date
_logger = logging.getLogger(__name__)

class Employee(models.Model):

	_inherit = 'hr.employee'

	@api.onchange('address_home_id')
	def _onchange_employee_id(self):

		if self.address_home_id:
			self.identification_id = self.address_home_id.vat
			self.work_email = self.address_home_id.email

	eps_id = fields.Many2one('res.partner', 
					string='EPS',
					domain=lambda self: [('id', 'in', self.env.user.company_id.eps_partner_ids.ids)])


	afp_id = fields.Many2one('res.partner', 
					string='AFP',
					domain=lambda self: [('id', 'in', self.env.user.company_id.afp_partner_ids.ids)])

	ccf_id = fields.Many2one('res.partner', 
					string= u'CCF',
					domain=lambda self: [('id', 'in', self.env.user.company_id.ccf_partner_ids.ids)])

	severance_id = fields.Many2one('res.partner', 
					string= u'CESANTÍAS',
					domain=lambda self: [('id', 'in', self.env.user.company_id.severance_partner_ids.ids)])

	arl_id = fields.Many2one('res.partner', 
					string='ARL',
					domain=lambda self: [('id', 'in', self.env.user.company_id.arl_partner_ids.ids)])

	risk_type_id = fields.Many2one('alfa.amb_risk_classes', string = 'Tipo de riesgo')

	percentage_risk = fields.Float(related = 'risk_type_id.percentage_risk', 
			string = u'Porcentaje Riesgo',
			digits=dp.get_precision('Risk Classes'),
			store = True)

	active_contracts = fields.Boolean(string = 'Contractos activos?', 
		compute='_compute_contracts_active', store = True)


	date_start_contract = fields.Date(
		string = 'Fecha inicio contrato',
		compute='_compute_date_contract',
		store = True
	)

	date_end_contract = fields.Date(
		string = 'Fecha fin contrato',
		compute='_compute_date_contract',
		store = True
	)

	date_last_payroll = fields.Date(
		string = u'Fecha ultima nómina',
		compute='_compute_date_last_payroll',
		store = True
	)

	work_contract = fields.Boolean(
		string = 'Contrato laboral', 
		compute='_compute_contracts_active', 
		store = True
	)

	@api.depends('contract_ids', 'contract_ids.state', 'contract_ids.work_contract', 'contract_ids.date_end', 'contract_ids.date_start')
	def _compute_contracts_active(self):
		""" 
			Campo que nos permite saber si el empleado cuenta con por lo menos
			un contracto activo
		"""
		date_now = datetime.strftime(date.today(), '%d-%m-%Y')
		new_date = datetime.strptime(date_now, '%d-%m-%Y')
		new_date = format_datetime(new_date, format="YYYY-MM-d", locale=self._context.get('lang') or 'es_CO')
		
		Contract = self.env['hr.contract']
		for employee in self:

			contracts = Contract.search([('employee_id', '=', employee.id),
				('employee_id.active', '=', True),
				('state', '!=', 'close'),
				('work_contract', '=', True)], order='date_start desc')
			
			for contract in contracts:
				
				if contract.date_end:
					
					if datetime.strptime(new_date,'%Y-%m-%d') >= datetime.strptime(contract.date_start, '%Y-%m-%d') and datetime.strptime(new_date,'%Y-%m-%d') <= datetime.strptime(contract.date_end,'%Y-%m-%d'):	
						employee.active_contracts = True
					else:
						employee.active_contracts = False

				else:

					if datetime.strptime(new_date,'%Y-%m-%d') >= datetime.strptime(contract.date_start, '%Y-%m-%d'):
						employee.active_contracts = True
					else:
						employee.active_contracts = False


				
				employee.work_contract = contract.work_contract


	@api.depends('contract_ids', 'contract_ids.date_end', 'contract_ids.date_start')
	def _compute_date_contract(self):
		""" 
			Con este metodo podemos obtener la fecha de inicio y fecha de fin en caso de 
			tenerla del contrato del empleado
		"""
		Contract = self.env['hr.contract']

		for employee in self:

			contract = Contract.search([('employee_id', '=', employee.id),
				('employee_id.active', '=', True)], order='date_start desc', limit = 1)
			
			if contract:

				employee.date_start_contract = contract.date_start

				if contract.date_end:

					employee.date_end_contract = contract.date_end


	@api.depends('slip_ids', 'slip_ids.state', 'slip_ids.date_from', 'slip_ids.date_to')
	def _compute_date_last_payroll(self):
		""" 
			Con este metodo podemos obtener la fecha de inicio y fecha de fin en caso de 
			tenerla del contrato del empleado
		"""
		payslip_obj = self.env['hr.payslip']

		for employee in self:

			payslip = payslip_obj.search([('employee_id', '=', employee.id),
				('employee_id.active', '=', True)],
				order='date_to desc', limit = 1)
			
			if payslip:

				employee.date_last_payroll = payslip.date_to
