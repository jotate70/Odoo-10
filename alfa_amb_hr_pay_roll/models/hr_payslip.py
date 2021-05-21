#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time
from datetime import datetime, timedelta, date
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_is_zero


import os, zipfile
import base64, unicodedata,tempfile

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):


	_inherit = 'hr.payslip'

	@api.multi
	@api.onchange('struct_id')
	def onchange_struct(self):

		if not self.struct_id:
			return

		employee = self.employee_id
		date_from = self.date_from
		date_to = self.date_to

		if not self.env.context.get('contract') or not self.contract_id:
			contract_ids = self.get_contract(employee, date_from, date_to)
			if not contract_ids:
				return

		#computation of the salary input
		worked_days_line_ids = self.get_worked_day_lines(contract_ids, date_from, date_to)
		worked_days_lines = self.worked_days_line_ids.browse([])
		for r in worked_days_line_ids:
			worked_days_lines += worked_days_lines.new(r)
		
		self.worked_days_line_ids = []
		self.input_line_ids = []
		self.line_ids = []
		self.details_by_salary_rule_category = []
		
		self.worked_days_line_ids = worked_days_lines
		input_line_ids = self.get_inputs(contract_ids, date_from, date_to)

		input_lines = self.input_line_ids.browse([])
		for r in input_line_ids:
			input_lines += input_lines.new(r)
		
		self.input_line_ids = input_lines
		
		return

	@api.model
	def get_payslip_lines(self, contract_ids, payslip_id):
		def _sum_salary_rule_category(localdict, category, amount):
			if category.parent_id:
				localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
			localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
			return localdict

		class BrowsableObject(object):
			def __init__(self, employee_id, dict, env):
				self.employee_id = employee_id
				self.dict = dict
				self.env = env

			def __getattr__(self, attr):
				return attr in self.dict and self.dict.__getitem__(attr) or 0.0

		class InputLine(BrowsableObject):
			"""a class that will be used into the python code, mainly for usability purposes"""
			def sum(self, code, from_date, to_date=None):
				if to_date is None:
					to_date = fields.Date.today()
				self.env.cr.execute("""
					SELECT sum(amount) as sum
					FROM hr_payslip as hp, hr_payslip_input as pi
					WHERE hp.employee_id = %s AND hp.state = 'done'
					AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
					(self.employee_id, from_date, to_date, code))
				return self.env.cr.fetchone()[0] or 0.0

		class WorkedDays(BrowsableObject):
			"""a class that will be used into the python code, mainly for usability purposes"""
			def _sum(self, code, from_date, to_date=None):
				if to_date is None:
					to_date = fields.Date.today()
				self.env.cr.execute("""
					SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
					FROM hr_payslip as hp, hr_payslip_worked_days as pi
					WHERE hp.employee_id = %s AND hp.state = 'done'
					AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
					(self.employee_id, from_date, to_date, code))
				return self.env.cr.fetchone()

			def sum(self, code, from_date, to_date=None):
				res = self._sum(code, from_date, to_date)
				return res and res[0] or 0.0

			def sum_hours(self, code, from_date, to_date=None):
				res = self._sum(code, from_date, to_date)
				return res and res[1] or 0.0

		class Payslips(BrowsableObject):
			"""a class that will be used into the python code, mainly for usability purposes"""

			def sum(self, code, from_date, to_date=None):
				if to_date is None:
					to_date = fields.Date.today()
				self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
							FROM hr_payslip as hp, hr_payslip_line as pl
							WHERE hp.employee_id = %s AND hp.state = 'done'
							AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
							(self.employee_id, from_date, to_date, code))
				res = self.env.cr.fetchone()
				return res and res[0] or 0.0

		#we keep a dict with the result because a value can be overwritten by another rule with the same code
		result_dict = {}
		rules_dict = {}
		worked_days_dict = {}
		inputs_dict = {}
		blacklist = []
		payslip = self.env['hr.payslip'].browse(payslip_id)
		for worked_days_line in payslip.worked_days_line_ids:
			worked_days_dict[worked_days_line.code] = worked_days_line
		for input_line in payslip.input_line_ids:
			inputs_dict[input_line.code] = input_line

		categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
		inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
		worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
		payslips = Payslips(payslip.employee_id.id, payslip, self.env)
		rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

		baselocaldict = {'categories': categories, 'rules': rules, 'payslip': payslips, 'worked_days': worked_days, 'inputs': inputs}
		#get the ids of the structures on the contracts and their parent id as well
		contracts = self.env['hr.contract'].browse(contract_ids)
		structure_ids = contracts.get_all_structures()
		#get the rules of the structure and thier children
		rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
		if self.struct_id:
			rule_ids = self.env['hr.payroll.structure'].browse(self.struct_id.id).get_all_rules()
		#run the rules by sequence
		sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
		sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

		for contract in contracts:
			employee = contract.employee_id
			localdict = dict(baselocaldict, employee=employee, contract=contract)
			for rule in sorted_rules:
				key = rule.code + '-' + str(contract.id)
				localdict['result'] = None
				localdict['result_qty'] = 1.0
				localdict['result_rate'] = 100
				#check if the rule can be applied
				if rule.satisfy_condition(localdict) and rule.id not in blacklist:
					#compute the amount of the rule
					amount, qty, rate = rule.compute_rule(localdict)
					#check if there is already a rule computed with that code
					previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
					#set/overwrite the amount computed for this rule in the localdict
					tot_rule = amount * qty * rate / 100.0
					localdict[rule.code] = tot_rule
					rules_dict[rule.code] = rule
					#sum the amount for its salary category
					localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
					#create/overwrite the rule in the temporary results
					result_dict[key] = {
						'salary_rule_id': rule.id,
						'contract_id': contract.id,
						'name': rule.name,
						'code': rule.code,
						'category_id': rule.category_id.id,
						'sequence': rule.sequence,
						'appears_on_payslip': rule.appears_on_payslip,
						'condition_select': rule.condition_select,
						'condition_python': rule.condition_python,
						'condition_range': rule.condition_range,
						'condition_range_min': rule.condition_range_min,
						'condition_range_max': rule.condition_range_max,
						'amount_select': rule.amount_select,
						'amount_fix': rule.amount_fix,
						'amount_python_compute': rule.amount_python_compute,
						'amount_percentage': rule.amount_percentage,
						'amount_percentage_base': rule.amount_percentage_base,
						'register_id': rule.register_id.id,
						'amount': amount,
						'employee_id': contract.employee_id.id,
						'quantity': qty,
						'rate': rate,
					}
				else:
					#blacklist this rule and its children
					blacklist += [id for id, seq in rule._recursive_search_of_rules()]

		return [value for code, value in result_dict.items()]


	@api.multi
	@api.depends('line_ids', 'company_id.rule_net_to_pay_id')
	def _get_net_to_pay(self):
		
		for rec in self:

			line_id = rec.mapped('line_ids').filtered(lambda line: line.salary_rule_id.id == self.env.user.company_id.rule_net_to_pay_id.id)
	
			if line_id:
				rec.net_to_pay = line_id.amount
			else:
				rec.net_to_pay = 0.0


	@api.multi
	@api.depends('line_ids', 'company_id.rule_base_salary_id')
	def _get_base_salary(self):
		
		for rec in self:

			line_id = rec.mapped('line_ids').filtered(lambda line: line.salary_rule_id.id == self.env.user.company_id.rule_base_salary_id.id)
	
			if line_id:
				rec.base_salary = line_id.amount
			else:
				rec.base_salary = 0.0

	@api.multi
	@api.depends('line_ids', 'company_id.rule_payroll_days_id')
	def _get_payroll_days(self):
		
		for rec in self:

			line_id = rec.mapped('line_ids').filtered(lambda line: line.salary_rule_id.id == self.env.user.company_id.rule_payroll_days_id.id)
	
			if line_id:
				rec.payroll_days = line_id.amount
			else:
				rec.payroll_days = 0.0



	@api.multi
	@api.depends('line_ids', 'company_id.rule_payroll_total_cost_id')
	def _get_total_cost(self):
		
		for rec in self:

			line_id = rec.mapped('line_ids').filtered(lambda line: line.salary_rule_id.id == self.env.user.company_id.rule_payroll_total_cost_id.id)
	
			if line_id:
				rec.total_cost = line_id.amount
			else:
				rec.total_cost = 0.0


	net_to_pay = fields.Float(string = 'Neto a pagar', 
					default = 0.0, 
					compute = '_get_net_to_pay', 
					store = True)


	base_salary = fields.Float(string = 'Salario base', 
					default = 0.0, 
					compute = '_get_base_salary', 
					store = True)


	payroll_days = fields.Float(string = 'Días nómina', 
					default = 0.0, 
					compute = '_get_payroll_days', 
					store = True)


	total_cost = fields.Float(string = 'Costo Total', 
					default = 0.0, 
					compute = '_get_total_cost', 
					store = True)

	note = fields.Text(readonly=False)


	input_line_ids = fields.One2many(readonly=False)

	"""
		Herencia al boton action_payslip_cancel para cambiar el estado de la novedad a cancel
	"""
	@api.multi
	def action_payslip_cancel(self):

		for payslip in self:
			
			payslip.write({'state': 'cancel'})
			super(HrPayslip, self).action_payslip_cancel()
			payslip._get_noveltys(payslip, 'cancel')

	"""
		Herencia al boton action_payslip_draft para cambiar el estado de la novedad a approved
	"""
	@api.multi
	def action_payslip_draft(self):
		for payslip in self:
			super(HrPayslip, self).action_payslip_draft()
			payslip._get_noveltys(self, 'approved')


	@api.multi
	def action_payslip_done(self):
		precision = self.env['decimal.precision'].precision_get('Payroll')

		for slip in self:
			
			slip.compute_sheet() 
			
			line_ids = []
			debit_sum = 0.0
			credit_sum = 0.0
			date = slip.date or slip.date_to

			name = _('Payslip of %s') % (slip.employee_id.name)
			move_dict = {
				'narration': name,
				'ref': slip.number,
				'journal_id': slip.journal_id.id,
				'date': date,
			}
			for line in slip.details_by_salary_rule_category:

				amount = slip.credit_note and -line.total or line.total

				if float_is_zero(amount, precision_digits=precision):
					continue
				
				debit_account_id = None
				credit_account_id = None

				specify_structure_salary_id = line.salary_rule_id.mapped('specific_struct_salary_ids').filtered(lambda sss: sss.struct_id.id == slip.struct_id.id)

				if specify_structure_salary_id:
					debit_account_id = specify_structure_salary_id.account_debit.id
					credit_account_id = specify_structure_salary_id.account_credit.id
				else:
					debit_account_id = line.salary_rule_id.account_debit.id
					credit_account_id = line.salary_rule_id.account_credit.id
				
				analytic_account_id =  self.get_analytic_account_id(line, specify_structure_salary_id)


				if debit_account_id:
					debit_line = (0, 0, {
						'name': line.name,
						'partner_id': line._get_partner_id(credit_account=False),
						'account_id': debit_account_id,
						'journal_id': slip.journal_id.id,
						'date': date,
						'debit': amount > 0.0 and amount or 0.0,
						'credit': amount < 0.0 and -amount or 0.0,
						'analytic_account_id': analytic_account_id,
						'tax_line_id': line.salary_rule_id.account_tax_id.id,
					})
					line_ids.append(debit_line)
					debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

				if credit_account_id:
					credit_line = (0, 0, {
						'name': line.name,
						'partner_id': line._get_partner_id(credit_account=True),
						'account_id': credit_account_id,
						'journal_id': slip.journal_id.id,
						'date': date,
						'debit': amount < 0.0 and -amount or 0.0,
						'credit': amount > 0.0 and amount or 0.0,
						'analytic_account_id': analytic_account_id,
						'tax_line_id': line.salary_rule_id.account_tax_id.id,
					})
					line_ids.append(credit_line)
					credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

			if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
				acc_id = slip.journal_id.default_credit_account_id.id
				if not acc_id:
					raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
				adjust_credit = (0, 0, {
					'name': _('Adjustment Entry'),
					'account_id': acc_id,
					'journal_id': slip.journal_id.id,
					'date': date,
					'debit': 0.0,
					'credit': debit_sum - credit_sum,
					'partner_id': line._get_partner_id(credit_account=True)
				})
				line_ids.append(adjust_credit)

			elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
				acc_id = slip.journal_id.default_debit_account_id.id
				if not acc_id:
					raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
				adjust_debit = (0, 0, {
					'name': _('Adjustment Entry'),
					'account_id': acc_id,
					'journal_id': slip.journal_id.id,
					'date': date,
					'debit': credit_sum - debit_sum,
					'credit': 0.0,
					'partner_id': line._get_partner_id(credit_account=False)
				})
				line_ids.append(adjust_debit)

			move_dict['line_ids'] = line_ids
			move = self.env['account.move'].create(move_dict)
			slip.write({'move_id': move.id, 'date': date})
			move.post()
			self._get_noveltys(slip, 'done')
			
		return self.write({'state': 'done'})



	def get_analytic_account_id(self, line, specify_structure_salary_id):

		analytic_account_id = None

		if line.salary_rule_id.where_takes_analytical_account == 'contract':

			analytic_account_id = line.slip_id.contract_id.analytic_account_id
			if analytic_account_id:
				analytic_account_id = analytic_account_id.id

		elif line.salary_rule_id.where_takes_analytical_account == 'general_causation':
			analytic_account_id =  line.salary_rule_id.analytic_account_id

			if analytic_account_id:
				analytic_account_id =  analytic_account_id.id

		elif line.salary_rule_id.where_takes_analytical_account == 'specific_causation':
			analytic_account_id = specify_structure_salary_id.analytic_account_id

			if analytic_account_id:
				analytic_account_id = analytic_account_id.id

		return analytic_account_id


	"""	
		Herencia al metodo create para hacer llamado al metodo _set_novelty
	"""

	@api.model
	def create(self, vals):
		payslip = super(HrPayslip, self).create(vals)
		self._set_novelty(payslip)
		return payslip


	def _set_novelty(self, payslip_id):
		
		"""
			Este metodo permite obtener las novedades al momento de hacer la creacion
			de la nomina, se obtiene las novedades para poder setearle el valor del payslip_id
			se hace una busqueda por el empleado, la fecha y el estado de la novedad para dar el id
			del payslip_id a la novedad

		"""
		hr_novelty_obj = self.env['hr.novelty']
		domain = [('state', '=', 'approved'), 
					('employee_id', '=', payslip_id.employee_id.id), 
					('date_from', '<=', payslip_id.date_to), 
					('date_to', '>=', payslip_id.date_from)]

		hr_novelty_ids = hr_novelty_obj.search(domain)

		for novelty in hr_novelty_ids:

			novelty.payslip_id = payslip_id.id



	def _get_noveltys(self, payslip_id, state):

		"""
			Esta funcion permite recorrer las novedades que ya tengan asociada una nomina
			y le cambia el estado al que se seleccione
		"""
		hr_novelty_obj = self.env['hr.novelty']

		hr_novelty_ids = hr_novelty_obj.search([('payslip_id', '=', payslip_id.id)])
		
		for novelty in hr_novelty_ids:

			if novelty.apply_retefunte and state == 'done':
				continue
			
			self.set_state_novelty(novelty, state)


	def _set_amount_input_line(self, hr_novelty_ids, input_code):

		""" 
			Este metodo retorna el valor de las novedades pra ser asignado en las lineas 
			de otros ingresos que se encuentran en la nomina.

			recibe el record de las novedades y el codigo del input
		"""
		novelty_amount = 0.0
		notes = list()
		show_on_report = False
		if hr_novelty_ids:

			for novelty in hr_novelty_ids.filtered(lambda novelty: novelty.input_id.code == input_code):
				
				novelty_amount += novelty.total

				if novelty.novelty:
					notes.append(novelty.novelty)

				show_on_report = True

		return novelty_amount, ", ".join(notes), show_on_report
	
	

	"""
		Se hace herencia a este metodo para poder agregarle el valor que se encuentran en las 
		novedades, a cada uno de los inputs, se agregan las lineas de la 115 a la 137 en donde 
		se buscan las novedades por el empleado, el periodo (date_to - date_from) y el estado de 
		la noveda, despues en la linea 149 se hace el llamado 
		'amount': self._set_amount_input_line(hr_novelty_ids, input.code) para asignar el valor
	"""

	@api.model
	def get_inputs(self, contract_ids, date_from, date_to):

		res = []
		hr_novelty_obj = self.env['hr.novelty']
		contracts = self.env['hr.contract'].browse(contract_ids)
		structure_ids = contracts.get_all_structures()
		rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
		if self.struct_id:
			rule_ids = self.env['hr.payroll.structure'].browse(self.struct_id.id).get_all_rules()
		sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
		inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

		domain = [('state', '=', 'approved')]
		domain_retefuente = list()

		if not self.employee_id:
			if self.env.context.get('employee_id', False):
				domain.append(('employee_id', '=', self.env.context.get('employee_id')))
		else:
			domain.append(('employee_id', '=', self.employee_id.id))


		if not self.date_to:
			if self.env.context.get('date_to', False):
				domain.append(('date_from', '<=', self.env.context.get('date_to')))
		else:
			domain.append(('date_from', '<=', self.date_to))


		if not self.date_from:
			if self.env.context.get('date_from', False):
				domain.append(('date_to', '>=', self.env.context.get('date_from')))
		else:
			domain.append(('date_to', '>=', self.date_from))

		domain_retefuente = domain[:]
		domain_retefuente.append(('apply_retefunte', '=', True))
		domain.append(('apply_retefunte', '=', False))

		hr_novelty_ids = hr_novelty_obj.search(domain)
		hr_novelty_retefuente_ids = hr_novelty_obj.search(domain_retefuente)

		for contract in contracts:

			for input in inputs:
				
				novelty_amount, note, show_on_report = self._set_amount_input_line(hr_novelty_ids, input.code)
				
				if not show_on_report:

					novelty_amount, note, show_on_report = self._set_amount_input_line(hr_novelty_retefuente_ids, input.code)

				input_data = {
					'name': input.name,
					'code': input.code,
					'contract_id': contract.id,
					'amount': novelty_amount,
					'note': note,
					'is_monetary': input.is_monetary,
					'show_on_report': show_on_report,
				}

				res += [input_data]

		return res


	def set_state_novelty(self, novelty, state):

		""" 
			Esta función permite a las novedades cambiarles el estado
			a medida que cambia el estado de la nomina

			recibe el record de la novedad y el estado a la 
			que se va a setear la novedad
		"""
		
		novelty.state = state


	@api.multi
	def make_done_hr_payslip(self, hr_payslips):


		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):
			if hr_payslips:

				for payslip in hr_payslips:

					payslip.action_payslip_done()		
		else:
			raise UserError(_('No esta autorizado para realizar esta acción'))


	@api.multi
	def make_cancel_hr_payslip(self, hr_payslips):

		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):

			if hr_payslips:

				for payslip in hr_payslips:

					payslip.action_payslip_cancel()	

		else:
			raise UserError(_('No esta autorizado para realizar esta acción'))

	@api.multi
	def make_draft_hr_payslip(self, hr_payslips):

		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):
			if hr_payslips:

				for payslip in hr_payslips:

					payslip.action_payslip_draft()	
		else:
			raise UserError(_('No esta autorizado para realizar esta acción'))


	@api.multi
	def make_recalculate_hr_payslip(self, hr_payslips):

		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):
			if hr_payslips:

				for payslip in hr_payslips:

					payslip.compute_sheet()
		else:
			raise UserError(_('No esta autorizado para realizar esta acción'))

	@api.multi
	def _get_print_report_name(self):
		""" 
			Esta funcion retorna el nombre del archivo de nomina que se esta creando
		"""
		self.ensure_one()
		date_format = str(datetime.strftime(date.today(), '%Y-%m-%d'))
		return (u"{}_{}".format(date_format, self.employee_id.name))



	def get_file_names(self, path):
		"""	
			con este modulo obtenemos el nombre del archivo y la ruta de donde 
			se ubica temporalmente el archivo .rar que se va a descargar, para trabajarlo
			en los demas modulo

			recibe el path y retorna tanto el nombre del archivo como la ruta de donde esta
		"""

		date_format = str(datetime.strftime(date.today(), '%Y%m%d'))
		#Nombre del archivo comprimido que se descarga 
		file_name = "{}_{}".format(date_format,"payslip")
		#ruta de donde se encuentra el archivo
		file_name_zip = "{}{}.rar".format('/tmp/',file_name)

		return file_name, file_name_zip

	def create_attachment_temp(self, report_obj, payslip):
		"""	
			Esta funcion lee el pdf que se crea cpara cada nomina y retorna el encode
			del resultado de leerlo

			esto se hace así porque esta funcion get_pdf nos retorna la lectura de ese archivo pdf

			retorna el encodestring de la lectura de cada pdf generado
		"""
		result = report_obj.get_pdf(payslip.ids, "hr_payroll.report_payslip")
		b64_pdf = base64.encodestring(result)
		return b64_pdf


	def write_file_rar(self, b64_pdf, fname, zip_archive):
		"""
			Funcion que nos permite escribir los archivos generados en el
			.rar
		"""
		def isBase64_decodestring(s):
			try:
				return base64.decodestring(s)
			except Exception as e:
				raise ValidationError('Error: ' + str(e))

		object_name = "/tmp/{}.pdf".format(self.get_normalize_name(fname))
		with open(object_name, "w") as object_handle:
			object_handle.write(isBase64_decodestring(b64_pdf)) 
			object_handle.close()
		
		zip_archive.write(object_name)
		os.remove(object_name)



	def get_read_file(self):
		"""
			Funcion que nos permite obtener la data del archivo .rar, para que
			pueda ser descargado
		"""
		path = os.path.dirname(os.path.realpath(__file__))

		file_name, file_name_zip = self.get_file_names(path)

		with open(file_name_zip, 'rb') as zip_to_read:

			zip_read = zip_to_read.read()
			b64_zip = base64.encodestring(zip_read)
			zip_to_read.close()
			os.remove(file_name_zip)

		return base64.b64decode(b64_zip)



	@api.multi
	def print_multi_hr_payslip(self, hr_payslips):
		"""
			Esta funcion permite imprimir las nominas de los usuarios de manera
			multiple y descarga un archivo .rar con los pdf de cada nomina
		"""
		if self.env.user.has_group('hr_payroll.group_hr_payroll_manager'):
			path = os.path.dirname(os.path.realpath(__file__))
			file_name, file_name_zip = self.get_file_names(path)

			zipfilepath = os.path.join(path, file_name_zip) 
			zip_archive = zipfile.ZipFile(zipfilepath, "w")

			report_obj = self.env['report']

			if hr_payslips:
				for payslip in hr_payslips:
					fname = payslip._get_print_report_name()
					b64_pdf  = self.create_attachment_temp(report_obj, payslip)
					self.write_file_rar(b64_pdf, fname, zip_archive)
			zip_archive.close()
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


	@api.multi
	def update_news(self):

		for payslips in self:

			payslips.onchange_employee()

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
