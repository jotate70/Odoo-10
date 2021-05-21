# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from collections import defaultdict
import math

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class AlfaAmbRiskClasses(models.Model):

	_name = 'alfa.amb_risk_classes'
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	name = fields.Char(string = 'Nombre')
	percentage_risk = fields.Float(string = u'Porcentaje Riesgo',
		digits=dp.get_precision('Risk Classes'),
		track_visibility='onchange')


