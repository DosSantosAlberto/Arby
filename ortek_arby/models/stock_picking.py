from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    carrier_id = fields.Many2one('delivery.carrier', string="Delivery Carrier")
    carrier_tracking_ref = fields.Char(string="Carrier Tracking Reference", copy=False)
    carrier_tracking_url = fields.Char(string="Tracking URL", compute='_compute_carrier_tracking_url')

    @api.depends('carrier_id', 'carrier_tracking_ref')
    def _compute_carrier_tracking_url(self):
        for picking in self:
            # Lógica segura para gerar o URL de rastreio se necessário
            picking.carrier_tracking_url = False

    def get_multiple_carrier_tracking(self):
        """Método de suporte exigido por alguns templates de portal para tracking múltiplo."""
        self.ensure_one()
        return []