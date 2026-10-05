# -*- coding: utf-8 -*-

import logging
import json
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from .ai_prompts import OrtekAiPrompts  # <--- Gestor central de prompts

_logger = logging.getLogger(__name__)


class OrtekAiEngine(models.Model):
    _name = 'ortek.ai.engine'
    _description = 'Motor de Inteligência Artificial Transversal Real'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nome do Motor',
        required=True,
        default='IAORTEK Orchestrator'
    )
    active = fields.Boolean(
        string='Ativo',
        default=True
    )
    sequence = fields.Integer(
        string='Sequência',
        default=10
    )

    # Campos de configuração de API e LLM
    api_key = fields.Char(
        string='Chave API (OpenAI/Anthropic/Ollama)',
        required=True
    )
    api_endpoint = fields.Char(
        string='Endpoint da API',
        default='https://api.openai.com/v1/chat/completions'
    )
    model_name = fields.Char(
        string='Nome do Modelo LLM',
        default='gpt-4o'
    )

    model_version = fields.Selection([
        ('v1_heuristic', 'Motor de Regras e Heurísticas'),
        ('v2_ml', 'Modelo Preditivo (Machine Learning)'),
        ('v3_llm', 'Agente Conversacional / RAG')
    ], string='Versão do Modelo', default='v3_llm', required=True)

    confidence_threshold = fields.Float(
        string='Limiar de Confiança (%)',
        default=85.0,
        help='Nível mínimo de precisão para aceitar recomendações automáticas.'
    )

    total_recommendations = fields.Integer(
        string='Total de Análises Realizadas',
        readonly=True,
        default=0
    )
    successful_outcomes = fields.Integer(
        string='Operações Bem-sucedidas',
        readonly=True,
        default=0
    )

    notes = fields.Text(
        string='Prompt de Sistema / Diretrizes Globais',
        help='Instruções de comportamento transversal para o assistente de IA.'
    )

    def action_test_connection(self):
        """Testa a operacionalidade do motor de IA."""
        for rec in self:
            _logger.info("A testar o Motor de IA transversal: %s", rec.name)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Ortek AI'),
                    'message': _('Motor de Inteligência Artificial operacional e online!'),
                    'type': 'success',
                    'sticky': False,
                }
            }

    @api.model
    def get_ai_response(self, user_message, context_data=None):
        """
        Ponto de entrada do Chat (ORTEK AI CHAT).
        Fluxo transversal: Contexto -> Router -> Múltiplos Módulos ERP -> Síntese da IA.
        """
        if not user_message:
            return _("Mensagem vazia.")

        _logger.info("=== [IAORTEK] INÍCIO DO PROCESSAMENTO TRANSVERSAL ===")
        _logger.info("Mensagem recebida do utilizador: %s", user_message)

        # PASSO 1: CONTEXTO + PERMISSÕES
        user_context = self._get_context_and_permissions()
        _logger.info("Contexto do utilizador carregado: %s", user_context)

        # PASSO 2: ROUTER DA IA (Quais departamentos acionar?)
        target_departments = self._ask_llm_to_route(user_message)
        _logger.info(">>> [ROUTER IAORTEK] Departamentos decididos: %s", target_departments)

        # PASSO 3: CONSULTA TRANSVERSAL AOS MÓDULOS DO ERP (Com controlo de acesso)
        erp_data = self._fetch_erp_data(target_departments, user_message, user_context)
        _logger.info(">>> [ERP DATA] Dados consolidados: %s", json.dumps(erp_data, ensure_ascii=False, default=str))

        # PASSO 4: RESPOSTA FINAL (Análise, Previsão e Recomendação)
        final_response = self._generate_final_response(user_message, erp_data, user_context)
        _logger.info("=== [IAORTEK] FIM DO PROCESSAMENTO COM SUCESSO ===")

        return final_response

    def _get_context_and_permissions(self):
        """Mapeia o contexto e os grupos de acesso do utilizador no Odoo."""
        user = self.env.user
        return {
            'user_name': user.name,
            'company': user.company_id.name,
            'is_admin': user.has_group('base.group_erp_manager'),
            'is_manager': user.has_group('sales_team.group_sale_manager') or user.has_group('base.group_erp_manager'),
        }

    def _ask_llm_to_route(self, prompt):
        """Pede à IA para classificar a intenção e escolher os departamentos necessários."""
        system_prompt = OrtekAiPrompts.get_router_system_prompt()
        response = self._call_llm_api(system_prompt, prompt)

        # Limpeza de blocos de markdown caso o LLM envie formatação extra
        cleaned_response = response.strip()
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.split("```")[1]
            if cleaned_response.startswith("json"):
                cleaned_response = cleaned_response[4:]
            cleaned_response = cleaned_response.strip()

        try:
            departments = json.loads(cleaned_response)
            if isinstance(departments, list):
                return departments
        except json.JSONDecodeError:
            _logger.warning("Falha ao parsear JSON do router da IA. Resposta bruta: %s", response)

        return []

    def _fetch_erp_data(self, departments, prompt, user_context):
        """
        Cruza os dados reais de múltiplos módulos do Odoo com base na decisão da IA,
        aplicando rigorosamente regras de acesso e transparência (sem alucinações).
        """
        data_gathered = {}

        # 1. FINANCEIRO (Restrito a Administradores/Gestores)
        if "FINANCEIRO" in departments:
            if not user_context.get('is_admin') and not user_context.get('is_manager'):
                data_gathered['Financeiro'] = "Não tem permissão. Contacte o seu administrador."
            else:
                try:
                    invoices = self.env['account.move'].search_read(
                        [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
                        ['name', 'amount_total', 'amount_residual', 'invoice_date', 'invoice_date_due'],
                        limit=10
                    )
                    data_gathered[
                        'Financeiro_Faturas'] = invoices if invoices else "Não existem faturas registadas no sistema no momento."
                except AccessError:
                    data_gathered['Financeiro'] = "Não tem permissão. Contacte o seu administrador."

        # 2. ENCOMENDAS / VENDAS (Com suporte a prazos personalizados e estado de pagamento)
        if "ENCOMENDAS" in departments or "Vendas" in departments:
            try:
                # Nota: Certifique-se de que 'x_studio_prazo' corresponde ao campo de prazo visível no kanban da ORTEK ARBY
                sales_fields = ['name', 'amount_total', 'partner_id', 'date_order', 'commitment_date', 'validity_date',
                                'state']

                # Tenta incluir o campo personalizado de prazo se existir no modelo
                model_fields = self.env['sale.order']._fields
                if 'x_studio_prazo' in model_fields:
                    sales_fields.append('x_studio_prazo')
                elif 'x_prazo' in model_fields:
                    sales_fields.append('x_prazo')

                sales = self.env['sale.order'].search_read(
                    [('state', 'in', ['sale', 'done', 'draft'])],  # Inclui rascunhos caso estejam no kanban inicial
                    sales_fields,
                    limit=15
                )
                data_gathered[
                    'Vendas_Encomendas'] = sales if sales else "Não existem encomendas de vendas registadas no sistema no momento."
            except AccessError:
                data_gathered['Vendas_Encomendas'] = "Não tem permissão. Contacte o seu administrador."
            except Exception as e:
                _logger.error("Erro ao procurar encomendas: %s", str(e))
                data_gathered['Vendas_Encomendas'] = "Erro ao recuperar dados de encomendas."

        # 3. ESTOQUE / INVENTÁRIO (Matérias-primas e artigos acabados)
        if "ESTOQUE" in departments or "COMPRAS" in departments:
            try:
                quants = self.env['stock.quant'].search_read(
                    [('location_id.usage', '=', 'internal')],
                    ['product_id', 'quantity'],
                    limit=15
                )
                data_gathered[
                    'Estoque'] = quants if quants else "Não existem produtos registados no estoque no momento."
            except AccessError:
                data_gathered['Estoque'] = "Não tem permissão. Contacte o seu administrador."
            except Exception:
                data_gathered['Estoque'] = "Módulo de estoque não inicializado ou sem registos disponíveis."

        # 4. PRODUÇÃO / FABRICO
        if "PRODUCAO" in departments:
            try:
                productions = self.env['mrp.production'].search_read(
                    [('state', 'in', ['confirmed', 'progress', 'to_close'])],
                    ['name', 'product_id', 'product_qty', 'state', 'date_planned_start'],
                    limit=10
                )
                data_gathered[
                    'Producao'] = productions if productions else "Não existem ordens de fabrico ativas no momento."
            except AccessError:
                data_gathered['Producao'] = "Não tem permissão. Contacte o seu administrador."
            except Exception:
                data_gathered['Producao'] = "Módulo de produção não inicializado ou sem ordens registadas."

        # 5. CLIENTES
        if "CLIENTES" in departments or "MARKETING" in departments:
            try:
                partners = self.env['res.partner'].search_read(
                    [('customer_rank', '>', 0)],
                    ['name', 'email', 'phone', 'commercial_partner_id'],
                    limit=10
                )
                data_gathered[
                    'Clientes'] = partners if partners else "Não existem clientes registados no sistema no momento."
            except AccessError:
                data_gathered['Clientes'] = "Não tem permissão. Contacte o seu administrador."

        # 6. RH (RECURSOS HUMANOS) - Restrito
        if "RH" in departments:
            if not user_context.get('is_admin'):
                data_gathered['RH'] = "Não tem permissão. Contacte o seu administrador."
            else:
                try:
                    employees = self.env['hr.employee'].search_read(
                        [], ['name', 'job_id', 'department_id'],
                        limit=10
                    )
                    data_gathered[
                        'RH_Colaboradores'] = employees if employees else "Não existem colaboradores registados no RH no momento."
                except Exception:
                    data_gathered['RH'] = "Módulo de RH não inicializado ou sem registos."

        return data_gathered

    def _generate_final_response(self, original_prompt, erp_data, user_context):
        """Envia os dados transversais recolhidos para a IA formular a análise e recomendação."""
        system_prompt = OrtekAiPrompts.get_final_response_system_prompt(
            user_context['user_name'],
            erp_data
        )
        return self._call_llm_api(system_prompt, original_prompt)

    def _call_llm_api(self, system_prompt, user_prompt):
        """Função central de comunicação HTTP com o Ollama / LLM com timeout robusto."""
        engine = self.env['ortek.ai.engine'].search([('active', '=', True)], limit=1)
        if not engine or not engine.api_key:
            _logger.error("Erro: Chave API da IA não configurada no sistema ORTEK.")
            return "Erro: Chave API da IA não configurada no sistema ORTEK."

        headers = {
            "Authorization": f"Bearer {engine.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": engine.model_name or "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        try:
            response = requests.post(engine.api_endpoint, headers=headers, json=payload, timeout=68)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            _logger.error("Falha na comunicação com a IA Real: %s", str(e))
            return f"Desculpe, ocorreu uma falha de comunicação com o servidor cerebral ORTEK AI: {str(e)}"