# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http import request
import base64
from odoo.addons.web.controllers.main import content_disposition
_logger = logging.getLogger(__name__)


class website_account(http.Controller):


	@http.route('/download/saveas', type='http', auth="public")
	def saveas(self, model, record_id, method, encoded=False, filename=None, **kw):
		""" Download link for files generated on the fly.

		:param str model: name of the model to fetch the data from
		:param str record_id: id of the record from which to fetch the data
		:param str method: name of the method used to fetch data, decorated with @api.one
		:param bool encoded: whether the data is encoded in base64
		:param str filename: the file's name, if any
		:returns: :class:`werkzeug.wrappers.Response`
		"""
		Model = request.env[model].browse(int(record_id))
		datas = getattr(Model, method)()
		
		if not datas:
			return request.not_found()
		filecontent = datas
		if not filecontent:
			return request.not_found()
		if encoded:
			filecontent = base64.b64decode(filecontent)
		if not filename:
			filename = '%s_%s' % (model.replace('.', '_'), record_id)
		return request.make_response(filecontent,
									 [('Content-Type', 'application/octet-stream'),
									  ('Content-Disposition', content_disposition(filename))])
