# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Etapa e Controlo do Ciclo E-Commerce
    arby_stage_id = fields.Many2one(
        'sale.order.stage',
        string='Etapa ARBY',
        copy=False,
        tracking=True,
        index=True
    )

    payment_proof = fields.Binary(string='Comprovativo de Pagamento', attachment=True)
    payment_proof_filename = fields.Char(string='Nome do Ficheiro de Comprovativo')
    payment_verified = fields.Boolean(
        string='Pagamento Verificado',
        default=False,
        copy=False,
        tracking=True
    )

    deadline_date = fields.Date(
        string='Data Limite de Processamento',
        compute='_compute_deadline_date',
        store=True,
        help='Prazo máximo de 15 dias após confirmação.'
    )

    @api.depends('date_order')
    def _compute_deadline_date(self):
        for order in self:
            if order.date_order:
                order.deadline_date = order.date_order.date() + timedelta(days=15)
            else:
                order.deadline_date = False

    def action_verify_payment(self):
        """Valida o pagamento e avança a encomenda na pipeline ARBY"""
        for order in self:
            if not order.payment_proof and not order.invoice_ids.filtered(
                    lambda i: i.payment_state in ['paid', 'in_payment']):
                raise UserError(_("Não é possível verificar sem um comprovativo carregado ou fatura paga."))
            order.payment_verified = True

            # Mover para a etapa de processamento se existir
            processing_stage = self.env['sale.order.stage'].search([('name', 'ilike', 'Processamento')], limit=1)
            if processing_stage:
                order.arby_stage_id = processing_stage.id
            order.message_post(body=_("Pagamento validado com sucesso pela equipa ARBY."))

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            # Atribuir primeira etapa caso não definida
            if not order.arby_stage_id:
                first_stage = self.env['sale.order.stage'].search([], order='sequence asc', limit=1)
                if first_stage:
                    order.arby_stage_id = first_stage.id
        return res


class SaleOrderStage(models.Model):
    _name = 'sale.order.stage'
    _description = 'Etapas do Pedido ARBY'
    _order = 'sequence, id'

    name = fields.Char(string='Nome da Etapa', required=True, translate=True)
    sequence = fields.Integer(string='Sequência', default=10)
    fold = fields.Boolean(string='Dobrado no Kanban', default=False)
    description = fields.Text(string='Descrição')