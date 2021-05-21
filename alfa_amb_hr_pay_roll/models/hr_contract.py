# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)
class HrContract(models.Model):

	_inherit = "hr.contract"

	non_benefit_wage = fields.Float(string =  u'Salario no prestacional', default = 0)

	bearing = fields.Float(string = 'Rodamiento', help = u'Este rodamiento no es prestacional')

	apply_transportation_assistance = fields.Boolean(string = 'Aplica auxilio de transporte', 
			default = False,
			help = u'Esta campo se usa para trabajadores que por nivel de salario clasifican para el auxilio de transporte pero por cercanía al trabajo no clasifican. De manera que para incluir el auxilio de transporte en la nómina se requiere que el salario sea menor a dos salarios mínimos y que este campo esté activado')


	retired = fields.Boolean(string = 'Pensionado', default = False)

	currency_id = fields.Many2one('res.currency', 'Currency',
								  default=lambda self: self.env.user.company_id.currency_id.id)

	rtefte_incentivo_vivienda = fields.Float(string = u'Incentivo empleador para vivienda', 
				default = 0, 
				help=u"Este es un incentivo que paga el empleador con destinación exclusiva para inversión " 
				u"en vivienda. Será contemplado como un ingreso laboral no prestacional. Solo influye en el "
				u"cálculo de la retención en la fuente, de manera que debe estar ingresado en el campo de pago "
				u"no salarial para que afecte la nómina como un ingreso.")

	rtefte_aportes_vol_pens_empleador = fields.Float(string = u'Incentivo empleador para vivienda', 
				default = 0, 
				help=u"Este es el aporte que el empleador hace a nombre del trabajador como aporte " 
				u"voluntario a pensiones obligatorias, diferente de los aportes a fondos de pensiones "
				u"voluntarias que pueda hacer el trabajador por su cuenta")

	work_contract = fields.Boolean(string = 'Contrato laboral')

	@api.multi
	@api.constrains('employee_id')
	def _identify_same_state(self):

		for record in self:

			obj = self.search([('state','not in',('close', 'pending')), ('employee_id', '=', record.employee_id.id)])

			if len(obj) > 1:

				raise ValidationError(u"No puede tener dos contratos al tiempo activos")
