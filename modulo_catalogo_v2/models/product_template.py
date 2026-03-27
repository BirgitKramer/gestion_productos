from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ------------------------------------------------------------------
    # CAMBIO 1: clasificacion_abc ahora es OBLIGATORIA (required=True).
    # Los productos creados con v1.0 tienen NULL en este campo.
    # Al añadir el CHECK constraint PostgreSQL rechazará el ALTER TABLE
    # porque ya existen filas con NULL → error si se actualiza por interfaz.
    # ------------------------------------------------------------------
    clasificacion_abc = fields.Selection(
        selection=[
            ('a', 'A – Alta rotación'),
            ('b', 'B – Rotación media'),
            ('c', 'C – Baja rotación'),
        ],
        string='Clasificación ABC',
        required=True,
        default='c',
        help='Clasificación del producto según su rotación y valor comercial.',
    )

    # ------------------------------------------------------------------
    # CAMBIO 2: margen_minimo ahora debe ser MAYOR QUE CERO.
    # Los productos de v1.0 tienen margen_minimo = 0.0 (valor por defecto
    # de Float en PostgreSQL cuando no se especifica nada).
    # El _sql_constraints añade un CHECK(margen_minimo > 0) que PostgreSQL
    # rechazará porque existen filas con 0.0 → segundo motivo de error.
    # ------------------------------------------------------------------
    margen_minimo = fields.Float(
        string='Margen mínimo (%)',
        digits=(5, 2),
        required=True,
        default=5.0,
        help='Porcentaje de margen mínimo aceptable. Debe ser mayor que 0.',
    )

    # ------------------------------------------------------------------
    # RESTRICCIONES SQL (nivel PostgreSQL)
    # ------------------------------------------------------------------
    # Estas dos restricciones se traducen en ALTER TABLE ... ADD CONSTRAINT.
    # Si la tabla ya tiene filas que violan las condiciones (NULL o 0.0),
    # PostgreSQL lanza CheckViolation y Odoo muestra un error genérico
    # en la interfaz web, dejando el módulo en estado inconsistente.
    #
    # Con la CLI el traceback completo aparece en terminal y además
    # se ejecuta el script pre-migration.py ANTES de llegar aquí,
    # evitando el error.
    # ------------------------------------------------------------------
    _sql_constraints = [
        (
            'clasificacion_abc_required',
            "CHECK(clasificacion_abc IS NOT NULL AND clasificacion_abc != '')",
            'La clasificación ABC es obligatoria. '
            'Ejecuta la migración con CLI para asignar valores por defecto.',
        ),
        (
            'margen_minimo_positivo',
            'CHECK(margen_minimo > 0)',
            'El margen mínimo debe ser mayor que 0. '
            'Ejecuta la migración con CLI para corregir los valores a 0.',
        ),
    ]

    # ------------------------------------------------------------------
    # CAMBIO 3: validación en capa Python (se suma al error de BD)
    # ------------------------------------------------------------------
    @api.constrains('margen_minimo')
    def _check_margen_minimo(self):
        for record in self:
            if record.margen_minimo <= 0:
                raise ValidationError(
                    f'El producto "{record.name}" tiene un margen mínimo de '
                    f'{record.margen_minimo}%. Debe ser mayor que 0.'
                )
