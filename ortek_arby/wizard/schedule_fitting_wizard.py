# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class ScheduleFittingWizard(models.TransientModel):
    _name = 'schedule.fitting.wizard'
    _description = 'Assistente de Agendamento de Prova ARBY'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Encomenda ARBY',
        required=True,
        readonly=True,
        default=lambda self: self._default_sale_order()
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='sale_order_id.partner_id',
        readonly=True
    )

    fitting_type = fields.Selection([
        ('first', '1.ª Prova (Ajuste Inicial)'),
        ('second', '2.ª Prova (Confirmação de Corte)'),
        ('final', '3.ª Prova / Ajustes Finais')
    ], string='Tipo de Prova', required=True, default='first')

    fitting_date = fields.Datetime(
        string='Data e Hora Pretendida',
        required=True,
        default=lambda self: fields.Datetime.now()
    )

    location_type = fields.Selection([
        ('store', 'Presencial na Loja / Ateliê'),
        ('home', 'Ao Domicílio / Endereço do Cliente')
    ], string='Local da Prova', required=True, default='store')

    notes = fields.Text(
        string='Observações Especiais para a Prova',
        help='Indique detalhes adicionais sobre o agendamento ou pedidos específicos da cliente.'
    )

    def _default_sale_order(self):
        """Busca a encomenda ativa pelo contexto se chamado a partir de uma vista de venda."""
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'sale.order':
            return active_id
        return False

    def action_confirm_fitting(self):
        """Regista a marcação da prova, cria a atividade interna e atualiza o histórico."""
        self.ensure_one()

        if self.fitting_date < fields.Datetime.now():
            raise UserError(_("Não é possível agendar uma prova para uma data ou hora no passado."))

        order = self.sale_order_id

        # Descrição detalhada para o registo e atividade
        fitting_label = dict(self._fields['fitting_type'].selection).get(self.fitting_type)
        location_label = dict(self._fields['location_type'].selection).get(self.location_type)

        message_body = _(
            "<b>Agendamento Criado com Sucesso!</b><br/>"
            "• <b>Tipo:</b> %s<br/>"
            "• <b>Data/Hora:</b> %s<br/>"
            "• <b>Local:</b> %s<br/>"
            "• <b>Notas:</b> %s"
        ) % (fitting_label, self.fitting_date, location_label, self.notes or 'Nenhuma observação.')

        # Regista a mensagem na linha do tempo da encomenda
        order.message_post(body=message_body)

        # Cria uma atividade interna para a receção / equipa de ateliê gerir o atendimento
        self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get('sale.order').id,
            'res_id': order.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': f"Agendamento: {fitting_label} - {order.name}",
            'note': message_body,
            'date_deadline': self.fitting_date.date(),
            'user_id': order.user_id.id or self.env.user.id,
        })

        return {'type': 'ir.actions.act_window_close'}