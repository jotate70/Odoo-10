# -*- coding: utf-8 -*-

from odoo import fields, models


class AlfaAmbHrPayRollConfig(models.TransientModel):

	_inherit = 'hr.payroll.config.settings'


	company_id = fields.Many2one(
		'res.company', string = 'Company',
		default=lambda self: self.env.user.company_id, required=True)

	rule_net_to_pay_id = fields.Many2one('hr.salary.rule', 
		related = 'company_id.rule_net_to_pay_id',
		string = u'Neto a pagar')

	rule_base_salary_id = fields.Many2one('hr.salary.rule', 
		related = 'company_id.rule_base_salary_id',
		string = u'Salario base')

	rule_payroll_days_id = fields.Many2one('hr.salary.rule', 
		related = 'company_id.rule_payroll_days_id',
		string = u'Días nómina')

	rule_payroll_total_cost_id = fields.Many2one('hr.salary.rule', 
		related = 'company_id.rule_payroll_total_cost_id',
		string = u'Costo Total')



		