# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_arby_transaction = fields.Boolean(
        string='Transação ARBY',
        default=False,
        help='Indica se a fatura foi gerada a partir da plataforma ARBY Store.'
    )

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            # Sincronizar validação com as encomendas de venda associadas
            sales = move.invoice_line_ids.mapped('sale_line_ids.order_id')
            for sale in sales:
                if move.payment_state in ['paid', 'in_payment']:
                    sale.payment_verified = True
        return res