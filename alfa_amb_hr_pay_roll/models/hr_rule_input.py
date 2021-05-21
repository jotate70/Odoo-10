# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class HrRuleInput(models.Model):

	_inherit = "hr.rule.input"

	is_monetary = fields.Boolean(string = u'Formato moneda en PDF', 
		default = False,
		help = u"Si este campo está activo, en el reporte PDF de nómina se utilizará " 
			u"formato numérico en lugar de moneda")

	apply_retefunte = fields.Boolean(string = u'Aplica retención a la fuente',
		default = False)