from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ------------------------------------------------------------------
    # Clasificación ABC:
    #   A → productos de alta rotación / alto valor
    #   B → rotación/valor intermedio
    #   C → baja rotación / bajo valor
    # En v1.0 el campo es OPCIONAL: el comercial puede dejarlo en blanco.
    # ------------------------------------------------------------------
    clasificacion_abc = fields.Selection(
        selection=[
            ('a', 'A – Alta rotación'),
            ('b', 'B – Rotación media'),
            ('c', 'C – Baja rotación'),
        ],
        string='Clasificación ABC',
        help='Clasificación del producto según su rotación y valor comercial.',
    )

    # ------------------------------------------------------------------
    # Margen mínimo aceptado (%) para este producto.
    # En v1.0 también es opcional y puede quedar a 0 o NULL.
    # ------------------------------------------------------------------
    margen_minimo = fields.Float(
        string='Margen mínimo (%)',
        digits=(5, 2),
        help='Porcentaje de margen mínimo aceptable para este producto.',
    )
