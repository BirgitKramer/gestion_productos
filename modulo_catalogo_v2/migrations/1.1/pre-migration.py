# migrations/1.1/pre-migration.py
#
# Se ejecuta AUTOMÁTICAMENTE con:
#
#   sudo -u odoo /opt/odoo/odoo-bin -c /etc/odoo.conf -d odoo19 -u modulo_catalogo
#
# Con la interfaz web este archivo es IGNORADO completamente.
# Eso es exactamente el problema: sin este script los CHECK constraints
# de v1.1 fallan porque la tabla tiene datos de v1.0 con NULL y 0.0.
#
# Propósito:
#   1. Rellenar clasificacion_abc = NULL  →  'c'  (baja rotación por defecto)
#   2. Rellenar margen_minimo    = 0.0   →  5.0  (5% como mínimo razonable)

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Normaliza los datos de v1.0 antes de que el ORM aplique
    los nuevos CHECK constraints de v1.1.
    """
    if not version:
        # Primera instalación limpia: no hay datos previos que migrar.
        _logger.info('[modulo_catalogo] Primera instalación, sin datos que migrar.')
        return

    _logger.info(
        '[modulo_catalogo] Iniciando migración 1.0 → 1.1 en product_template...'
    )

    # -- 1. Clasificación ABC: rellenar NULL con 'c' ----------------------
    cr.execute("""
        UPDATE product_template
        SET    clasificacion_abc = 'c'
        WHERE  clasificacion_abc IS NULL
           OR  clasificacion_abc = ''
    """)
    filas_abc = cr.rowcount
    _logger.info(
        '[modulo_catalogo] clasificacion_abc: %d producto(s) actualizados a "c".',
        filas_abc,
    )

    # -- 2. Margen mínimo: corregir 0.0 a 5.0 ----------------------------
    cr.execute("""
        UPDATE product_template
        SET    margen_minimo = 5.0
        WHERE  margen_minimo <= 0
           OR  margen_minimo IS NULL
    """)
    filas_margen = cr.rowcount
    _logger.info(
        '[modulo_catalogo] margen_minimo: %d producto(s) corregidos a 5.0%%.',
        filas_margen,
    )

    _logger.info(
        '[modulo_catalogo] Migración completada. '
        'El ORM puede añadir los CHECK constraints sin errores.'
    )
