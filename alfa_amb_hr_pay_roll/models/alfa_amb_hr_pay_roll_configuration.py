# -*- coding: utf-8 -*-

from odoo import fields, models


class AlfaAmbHrPayRollConfig(models.TransientModel):

	_name = 'alfa.amb_hr_pay_roll_config_settings'
	_inherit = 'res.config.settings'

	company_id = fields.Many2one(
		'res.company', string = 'Company',
		default=lambda self: self.env.user.company_id, required=True)

	eps_partner_ids = fields.Many2many('res.partner', 
			related = 'company_id.eps_partner_ids', 
			string = u'EPS')

	afp_partner_ids = fields.Many2many('res.partner', 
			related = 'company_id.afp_partner_ids', 
			string = u'AFP')

	severance_partner_ids = fields.Many2many('res.partner', 
			related = 'company_id.severance_partner_ids', 
			string = u'CESANTÍAS')

	ccf_partner_ids = fields.Many2many('res.partner', 
			related = 'company_id.ccf_partner_ids', 
			string = u'CCF')

	arl_partner_ids = fields.Many2many('res.partner', 
			related = 'company_id.arl_partner_ids', 
			string = u'ARL')