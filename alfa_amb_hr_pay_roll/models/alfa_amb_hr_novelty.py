#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel, unicodedata

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)

STATES = [('draft', 'Borrador'),
		('verify', u'Esperando Aprobación'),
		('approved', u'Aprobado'),
		('done', 'Hecho'),
		('cancel', 'Cancelado')]

class AlfaAmbHrNovelty(models.Model):

	_name = 'hr.novelty'
	_description = 'Novedades'

	_inherit = ['mail.thread', 'ir.needaction_mixin']

	employee_id = fields.Many2one('hr.employee', 
		string='Empleado', 
		required=True, 
		readonly=True,
		states={'draft': [('readonly', False)]},
		track_visibility='onchange')

	state = fields.Selection(STATES, 
		string='Estado', 
		index=True, 
		readonly=True, 
		copy=False, 
		default='draft',
		help="""* Cuando la novedad es creada el estado es \'Borrador\'
				\n* Si la novedad esta esperando verificación, el estado es \'Esperando\'.
				\n* Si la novedad es confirmada el estado es \'Hecho\'.
				\n* Cuando el usuario cancela la novedad el estado es \'Cancelado\'.""",
		track_visibility='onchange')

	input_id = fields.Many2one('hr.rule.input', 
		string = 'Input', 
		track_visibility='onchange',
		readonly=True,
		states={'draft': [('readonly', False)]})

	total = fields.Float(string='Total', 
		digits=dp.get_precision('Payroll'),
		track_visibility='onchange',
		readonly=True,
		states={'draft': [('readonly', False)]})

	contract_id = fields.Many2one('hr.contract', 
		compute='_compute_contract_id', 
		string='Contrato', 
		store=True)

	struct_id = fields.Many2one('hr.payroll.structure', 
		related = 'contract_id.struct_id',
		store = True)


	payslip_id = fields.Many2one('hr.payslip', 
		string='Pay Slip', 
		ondelete='cascade', 
		index=True,
		copy=False)

	date_from = fields.Date(string='Date From', readonly=True, required=True,
		default=time.strftime('%Y-%m-01'), 
		states={'draft': [('readonly', False)]},
		track_visibility='onchange')

	date_to = fields.Date(string='Date To', readonly=True, required=True,
		default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
		states={'draft': [('readonly', False)]},
		track_visibility='onchange')

	novelty = fields.Text(string = 'Nota',
		readonly=True,
		states={'draft': [('readonly', False)]})

	calculate_values_automatically = fields.Boolean(
		string = u'Calcular Automático', 
		states={'draft': [('readonly', False)]})


	apply_retefunte = fields.Boolean(string = u'Aplica retención a la fuente',
		related = 'input_id.apply_retefunte', store = True)


	@api.depends('employee_id')
	def _compute_contract_id(self):

		for novelty in self:

			contract_id = novelty.employee_id.mapped('contract_ids').filtered(lambda contract: contract.state in ('open'))
			if contract_id:

				novelty.sudo().contract_id = contract_id.id


	@api.multi
	@api.onchange('employee_id')
	def onchange_pqrs_line_id(self):
		for novelty in self:

			domain = {'struct_id': []}

			if novelty.contract_id:
				domain['struct_id'] = [('id', 'in', novelty.sudo().struct_id.mapped('rule_ids').filtered(lambda rule: rule.active).mapped('input_ids').ids)]
			
			return {'domain': domain}



	@api.multi
	@api.constrains('date_from', 'date_to')
	def _identify_dates(self):

		for record in self:

			if record.date_to < record.date_from:

				raise ValidationError(u"La fecha hasta no puede ser menor que la fecha desde")



	@api.multi
	@api.depends('date_from', 'date_to', 'employee_id')
	def name_get(self):
		result = []
		for novelty in self:
			name = '[{}-{}] {}'.format(novelty.date_from, novelty.date_to, self.get_normalize_name(novelty.employee_id.name))
			result.append((novelty.id, name))
		return result


	@api.multi
	def send_approval(self):
		return self.write({'state': 'verify'})

	@api.multi
	def approve(self):
		return self.write({'state': 'approved'})

	@api.multi
	def cancel(self):
		return self.write({'state': 'cancel'})

	@api.multi
	def send_draft(self):
		return self.write({'state': 'draft'})


	""" 
		metodo que nos permite normalizar el nombre del usuario
		quitando acentos, y caracteres especiales

		@params
			supplier_name -> recibe el nombre del proveedor
		
		@return
			el nombre del usuario normalizado
	"""
	def get_normalize_name(self, supplier_name):
		return unicodedata.normalize('NFKD', supplier_name).encode('ascii','ignore')


	@api.multi
	def approved_novelty(self, noveltys):

		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):

			for novelty in noveltys:

				novelty.approve()
		else:
			
			raise UserError(_('No esta autorizado para realizar esta acción'))

