# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Company(models.Model):

	_inherit = "res.company"

	eps_partner_ids = fields.Many2many('res.partner', 
			relation = 'res_company_eps_res_partner_rel', 
			string = u'EPS',
			help = u"""Los terceros que pueden funcar como una EPS.""")

	afp_partner_ids = fields.Many2many('res.partner', 
			relation = 'res_company_afp_res_partner_rel', 
			string = u'AFP',
			help = u"""Los terceros que pueden funcar como una AFP.""")

	severance_partner_ids = fields.Many2many('res.partner', 
			relation = 'res_company_severance_res_partner_rel', 
			string = u'Cesantías',
			help = u"""Los terceros que pueden funcar como una compañía donde pagar las cesantías.""")

	arl_partner_ids = fields.Many2many('res.partner', 
			relation = 'res_company_arl_res_partner_rel', 
			string = u'ARL',
			help = u"""Los terceros que pueden funcar como una ARL.""")

	ccf_partner_ids = fields.Many2many('res.partner', 
			relation = 'res_company_ccf_res_partner_rel', 
			string = u'CCF',
			help = u"""Los terceros que pueden funcar como una Caja de compensación Familiar.""")

	rule_net_to_pay_id = fields.Many2one('hr.salary.rule', string = u'Neto a pagar')

	rule_base_salary_id = fields.Many2one('hr.salary.rule', string = u'Base salarial')

	rule_payroll_days_id = fields.Many2one('hr.salary.rule', string = u'Días Nómina')

	rule_payroll_total_cost_id = fields.Many2one('hr.salary.rule', string = u'Costo Total')
