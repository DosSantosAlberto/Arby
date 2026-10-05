# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Vinculação com a Encomenda e Cliente ARBY
    arby_sale_order_id = fields.Many2one(
        'sale.order',
        string='Encomenda ARBY',
        compute='_compute_arby_sale_order',
        store=True,
        help='Encomenda de venda ARBY associada a esta ordem de produção.'
    )

    arby_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente ARBY',
        related='arby_sale_order_id.partner_id',
        store=True,
        readonly=True
    )

    arby_payment_verified = fields.Boolean(
        string='Pagamento Verificado',
        related='arby_sale_order_id.payment_verified',
        readonly=True,
        help='Indica se a encomenda tem o pagamento validado pela equipa financeira.'
    )

    arby_production_notes = fields.Text(
        string='Notas Especiais de Confecção / Estilo',
        help='Instruções de personalização trazidas da encomenda de venda.'
    )

    @api.depends('origin')
    def _compute_arby_sale_order(self):
        """Associa a Ordem de Produção à Encomenda de Venda pelo campo origin."""
        for production in self:
            if production.origin:
                sale_order = self.env['sale.order'].search([('name', '=', production.origin)], limit=1)
                production.arby_sale_order_id = sale_order.id if sale_order else False
            else:
                production.arby_sale_order_id = False

    def action_confirm(self):
        """Valida se o pagamento da encomenda foi verificado antes de confirmar a Ordem de Produção."""
        for production in self:
            if production.arby_sale_order_id and not production.arby_sale_order_id.payment_verified:
                raise UserError(_(
                    "Bloqueio ARBY: Não é possível iniciar a produção para a encomenda %s sem a validação do pagamento ou comprovativo."
                ) % production.arby_sale_order_id.name)
        return super(MrpProduction, self).action_confirm()