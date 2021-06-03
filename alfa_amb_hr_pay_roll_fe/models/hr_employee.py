#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)

class Employee(models.Model):

	_inherit = 'hr.employee'


	def get_document_type(self, fe_tipo_documento):

		document_type = {'11': 'R.C.N',
			'12': 'T.I',
			'13': 'C.C',
			'21': 'T.E',
			'22': 'C.E',
			'31': 'NIT',
			'41': 'Pasaporte',
			'42': 'D.I.E',
			'50': u'NIT de otro país',
			'91': 'NUIP'}
		
		return document_type.get(fe_tipo_documento, False)



	@api.onchange('address_home_id')
	def _onchange_employee_id(self):

		if self.address_home_id:

			document_formed = []
			fe_tipo_documento = self.address_home_id.fe_tipo_documento
			document_type = self.get_document_type(fe_tipo_documento)
			document_number = self.address_home_id.fe_nit

			if document_number:

				if document_type:
					document_formed.append(str(document_type+"."))

				document_formed.append(document_number)

				if fe_tipo_documento == '31' and self.address_home_id.fe_digito_verificacion != 'No aplica':
					
					document_formed.append(str('-'+self.address_home_id.fe_digito_verificacion))

				self.identification_id = "".join(document_formed)
			
			else:
				self.identification_id = ''
		