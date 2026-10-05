# -*- coding: utf-8 -*-
{
    'name': 'ORTEK ARBY - E-Commerce & Retail Management',
    'version': '18.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Plataforma enterprise de e-commerce, ciclo de provas/provas presenciais e gestão de loja.',
    'description': """
        Módulo ORTEK ARBY para Odoo 18.
        - Loja online enterprise integrada.
        - Gestão avançada de clientes (Customer Score e Fidelização).
        - Ciclo automatizado de provas e acompanhamento de encomendas.
        - Validação de pagamentos, sinalizações e entregas.
        - Motor de automação e integração de IA.
    """,
    'author': 'Jeronimo Jamba dos Santos / ORTEK',
    'website': 'https://www.ortek.ao',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'sale',
        'account',
        'stock',
        'payment',
        'mrp',
        'website',
        'website_sale',
        'portal',
        'mail',
        'project',
        'sale_project',  # Recomendado para garantir o mapeamento do project_id no fluxo de Vendas
        'delivery',

    ],

    'data': [
        # 1. Regras de Segurança (Grupos primeiro, Acessos a modelos depois)
        'security/security_groups.xml',
        'security/ir.model.access.csv',

        # 2. Dados do Sistema, Templates de Email e Cron
        'data/arby_stages_data.xml',
        'data/mail_template_data.xml',
        'data/cron_jobs.xml',
        'data/ai_engine_data.xml',  # <-- Adicione aqui

        # 3. Vistas de Formatos / Formulários / Listas (Declaram as Ações)
        'views/automation_views.xml',
        'views/ortek_ai_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_production_views.xml',

        # 4. Estrutura de Menus (Consome as Ações criadas acima)
        'views/menus.xml',

        # 5. Templates Web / Portal
        'views/ecommerce_templates.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ortek_arby/static/src/css/arby_style.css',
        ],
        'web.assets_backend': [
            'ortek_arby/static/src/js/ortek_ai_chat.js',
            'ortek_arby/static/src/xml/ortek_ai_chat.xml',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
