# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class ArbyCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(ArbyCustomerPortal, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'arby_orders_count' in counters:
            values['arby_orders_count'] = request.env['sale.order'].search_count([
                ('partner_id', '=', partner.id)
            ])
        return values

    @http.route(['/my/arby/fittings'], type='http', auth='user', website=True)
    def portal_my_fittings(self, **kw):
        """Lista as encomendas e estado de provas para a cliente no Portal."""
        partner = request.env.user.partner_id
        orders = request.env['sale.order'].search([
            ('partner_id', '=', partner.id)
        ], order='date_order desc')

        values = {
            'orders': orders,
            'page_name': 'arby_fittings',
        }
        return request.render("ortek_arby.portal_my_fittings_template", values)