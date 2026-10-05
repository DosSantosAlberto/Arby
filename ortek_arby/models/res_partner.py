# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Pontuação e Fidelização
    customer_score = fields.Float(
        string='Customer Score',
        compute='_compute_customer_score',
        store=True,
        help='Pontuação dinâmica calculada com base no valor e frequência de compras.'
    )
    loyalty_tier = fields.Selection([
        ('standard', 'Standard'),
        ('silver', 'Prata'),
        ('gold', 'Ouro'),
        ('vip', 'VIP / Exclusive'),
    ], string='Nível de Fidelidade', compute='_compute_loyalty_tier', store=True, default='standard')

    arby_notes = fields.Text(string='Preferências de Estilo & Notas ARBY')
    total_arby_orders = fields.Integer(string='Total de Encomendas ARBY', compute='_compute_arby_stats')

    @api.depends('sale_order_ids.state', 'sale_order_ids.amount_total')
    def _compute_customer_score(self):
        for partner in self:
            confirmed_orders = partner.sale_order_ids.filtered(lambda s: s.state in ['sale', 'done'])
            total_spent = sum(confirmed_orders.mapped('amount_total'))
            order_count = len(confirmed_orders)

            # Algoritmo de Score: Valor investido + bónus por frequência
            score = (total_spent / 1000.0) + (order_count * 5.0)
            partner.customer_score = round(score, 2)

    @api.depends('customer_score')
    def _compute_loyalty_tier(self):
        for partner in self:
            score = partner.customer_score
            if score >= 100:
                partner.loyalty_tier = 'vip'
            elif score >= 50:
                partner.loyalty_tier = 'gold'
            elif score >= 20:
                partner.loyalty_tier = 'silver'
            else:
                partner.loyalty_tier = 'standard'

    @api.depends('sale_order_ids')
    def _compute_arby_stats(self):
        for partner in self:
            partner.total_arby_orders = len(partner.sale_order_ids)