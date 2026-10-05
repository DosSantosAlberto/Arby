# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class ArbyWebsiteSale(WebsiteSale):

    @http.route(['/shop/payment/upload_proof'], type='http', auth='public', methods=['POST'], website=True)
    def upload_payment_proof(self, order_id=None, **post):
        """Processa o upload do comprovativo de pagamento feito pela cliente na loja online."""
        if not order_id:
            return request.redirect('/shop')

        order = request.env['sale.order'].sudo().browse(int(order_id))
        if order.exists() and 'proof_file' in request.params:
            file = request.params['proof_file']
            if file:
                file_content = file.read()
                order.sudo().write({
                    'payment_proof': file_content,
                    'payment_proof_filename': file.filename,
                })
                order.message_post(body=_("Comprovativo enviado pela cliente através do checkout da loja online."))

        return request.redirect('/shop/confirmation')