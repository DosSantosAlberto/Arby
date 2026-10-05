# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OrtekAutomation(models.Model):
    _name = 'ortek.automation'
    _description = 'Motor de Automação de Processos Transversal ORTEK'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nome da Regra de Automação',
        required=True,
        default='Nova Regra de Automação'
    )
    active = fields.Boolean(
        string='Ativo',
        default=True
    )
    sequence = fields.Integer(
        string='Sequência',
        default=10
    )

    # Gatilhos de Automação Universais
    trigger_event = fields.Selection([
        ('on_record_create', 'Ao Criar Novo Registo'),
        ('on_status_change', 'Ao Alterar Estado / Fase'),
        ('on_threshold_reach', 'Ao Atingir Limiar Crítico'),
        ('cron_daily', 'Execução Diária (Temporizador)')
    ], string='Gatilho (Trigger)', default='on_record_create', required=True)

    action_type = fields.Selection([
        ('send_notification', 'Enviar Notificação / Alerta'),
        ('assign_task', 'Atribuir Tarefa Interna'),
        ('trigger_ai', 'Solicitar Análise do Motor de IA'),
        ('update_stage', 'Avançar Estado Automaticamente')
    ], string='Ação a Executar', default='send_notification', required=True)

    # Parâmetros adicionais
    description = fields.Text(
        string='Descrição da Regra & Condições'
    )
    execution_count = fields.Integer(
        string='Vezes Executada',
        readonly=True,
        default=0
    )

    # --- MÉTODOS DE NEGÓCIO ---

    def action_execute_rule(self):
        """Executa manualmente a regra de automação selecionada."""
        for rec in self:
            _logger.info("A executar regra de automação transversal [%s] ID: %s", rec.name, rec.id)
            rec.execution_count += 1

            # Notificação na interface para feedback imediato
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Automação Executada'),
                    'message': _('A regra "%s" foi processada com sucesso!') % rec.name,
                    'type': 'success',
                    'sticky': False,
                }
            }

    @api.model
    def process_automated_triggers(self, event_type, record_id=None):
        """
        Método global acionado por fluxos do sistema para disparar as regras associadas.
        """
        rules = self.search([('active', '=', True), ('trigger_event', '=', event_type)])
        _logger.info("Encontradas %s regras de automação para o evento: %s", len(rules), event_type)

        for rule in rules:
            rule.execution_count += 1
            # Lógica de processamento das ações transversais
            if rule.action_type == 'send_notification':
                _logger.info("Disparada notificação automática para o registo ID: %s", record_id)
            elif rule.action_type == 'trigger_ai':
                _logger.info("Solicitada intervenção do ortek.ai.engine para o registo ID: %s", record_id)

        return True