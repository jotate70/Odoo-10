# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class HrSalaryRule(models.Model):

	_inherit = "hr.salary.rule"


	specific_struct_salary_ids = fields.One2many('alfa.amb_specific_cau_sal_str', 
		'rule_id', 
		string = u'Causación especifica según estructura salarial')

	sum_on_payroll = fields.Boolean(string = u'Suma en nómina')

	where_takes_analytical_account = fields.Selection([('contract', 'Contrato'), 
			('general_causation', u'Causación general'),
			('specific_causation', u'Causación especifica')],
			string = u'¿Donde toma la cuenta analítica?',
			default = 'contract')

	is_monetary = fields.Boolean(string = u'Formato moneda en pdf', 
		default = False,
		help = u"Si este campo está activo, en el reporte PDF de nómina se utilizará " 
			u"formato numérico en lugar de moneda")


	@api.multi
	@api.constrains('specific_struct_salary_ids')
	def _identify_same_state(self):
		
		specific_struct_salary_obj = self.env['alfa.amb_specific_cau_sal_str']

		structs = list()

		for record in self:
			
			specific_struct_salary_ids = specific_struct_salary_obj.search([('rule_id', '=', record.id)])

			if specific_struct_salary_ids:
				
				for struct in specific_struct_salary_ids:

					structs.append(struct.struct_id)

				contains_duplicates = any(structs.count(element) > 1 for element in structs)

				if contains_duplicates:

					raise ValidationError(u"Solo puede tener una estructura salarial al tiempo")


