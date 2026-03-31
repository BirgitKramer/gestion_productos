# Demo: Módulo Gestión Catálogo de Productos
## Objetivo
Demostrar que actualizar un módulo con cambios estructurales desde la
**interfaz web** provoca un error de PostgreSQL y deja la BD inconsistente,
mientras que la **CLI con `-u`** ejecuta los scripts de migración y resuelve
el problema correctamente.

---

## Funcionalidad del módulo
Extiende `product.template` (catálogo de productos) con dos campos:

| Campo             | Tipo      | Descripción                                      |
|-------------------|-----------|--------------------------------------------------|
| `clasificacion_abc` | Selection | Clasificación A/B/C por rotación del producto  |
| `margen_minimo`    | Float     | Margen mínimo aceptable en % para el producto   |

---

## Estructura de archivos

```
modulo_catalogo_v1/          ← versión 1.0: campos opcionales
├── __manifest__.py          (version: '1.0')
├── __init__.py
├── models/
│   ├── __init__.py
│   └── product_template.py  (campos sin required ni constraints)
└── views/
    └── product_views.xml

modulo_catalogo_v2/          ← versión 1.1: campos obligatorios + constraints
├── __manifest__.py          (version: '1.1')
├── __init__.py
├── models/
│   ├── __init__.py
│   └── product_template.py  (required=True + _sql_constraints + @constrains)
├── views/
│   └── product_views.xml
└── migrations/
    └── 1.1/
        └── pre-migration.py  ← CLAVE: solo lo ejecuta la CLI
```

---

## Pasos para reproducir el error

### FASE 1 — Instalar v1.0 y crear datos problemáticos

```bash
# Copiar v1 al servidor
scp -r modulo_catalogo_v1 user@IP:/tmp/modulo_catalogo
ssh -t user@IP "sudo mv /tmp/modulo_catalogo /opt/odoo/custom_addons/modulo_catalogo && sudo chown -R odoo:odoo /opt/odoo/custom_addons/modulo_catalogo"
```

Desde la interfaz:
1. Modo desarrollador → **Aplicaciones → Actualizar lista → Instalar** "Gestión Catálogo"
2. Ir a **Inventario → Productos** (o **Ventas → Productos**)
3. Editar 3–4 productos **sin rellenar** Clasificación ABC ni Margen mínimo
4. Guardar → los campos quedan a `NULL` y `0.0` en la BD

Verificar en psql:
```sql
SELECT name, clasificacion_abc, margen_minimo
FROM   product_template
WHERE  clasificacion_abc IS NULL OR margen_minimo <= 0
LIMIT  10;
```

---

### FASE 2 — Actualizar a v2 desde la INTERFAZ (el error)

```bash
# Subir v2 SIN el script de migración (simulamos actualización descuidada)

ssh -t user@192.168.1.76 "
  sudo rm -rf /opt/odoo/odoo/custom_addons/modulo_catalogo && \
  sudo mv /tmp/modulo_catalogo_nuevo /opt/odoo/odoo/custom_addons/modulo_catalogo && \
  sudo rm -rf /opt/odoo/odoo/custom_addons/modulo_catalogo/migrations && \
  sudo chown -R odoo:odoo /opt/odoo/odoo/custom_addons/modulo_catalogo
"
```

Desde la interfaz:
- Modo desarrollador → **Aplicaciones** → buscar "Gestión Catálogo" → **Actualizar**

**Resultado esperado → ERROR:**
```
psycopg2.errors.CheckViolation: check constraint "product_template_clasificacion_abc_required"
of relation "product_template" is violated by some row
```

La interfaz muestra un error rojo genérico. El módulo queda inconsistente:
- El código Python es v1.1
- La BD sigue sin los CHECK constraints
- Los productos siguen con NULL y 0.0

---

### FASE 3 — Actualizar con CLI (la solución correcta)

```bash
# Subir v2 completa, incluyendo migrations/
scp -r modulo_catalogo_v2 user@192.168.1.76:/tmp/modulo_catalogo_nuevo
ssh -t user@192.168.1.76 "
  sudo rm -rf /opt/odoo/odoo/custom_addons/modulo_catalogo && \
  sudo mv /tmp/modulo_catalogo_nuevo /opt/odoo/odoo/custom_addons/modulo_catalogo && \
  sudo chown -R odoo:odoo /opt/odoo/odoo/custom_addons/modulo_catalogo
"

# Actualizar con CLI
ssh -t user@192.168.1.76 "sudo -u odoo /usr/bin/odoo -c /etc/odoo/odoo.conf -d odoo19 -u modulo_catalogo"
```

**Lo que ocurre paso a paso:**
1. Odoo detecta cambio de versión `1.0 → 1.1`
2. Ejecuta `migrations/1.1/pre-migration.py`:
   - Rellena `clasificacion_abc = NULL` → `'c'`
   - Corrige `margen_minimo <= 0` → `5.0`
3. El ORM aplica los modelos y añade los CHECK constraints sin error
4. El traceback completo aparece en terminal si algo falla

Verificar que la migración se ejecutó:
```sql
SELECT name, clasificacion_abc, margen_minimo
FROM   product_template
WHERE  clasificacion_abc IS NULL OR margen_minimo <= 0;
-- Debe devolver 0 filas
```

---

## Resumen de por qué falla la interfaz

| Motivo                          | Interfaz web       | CLI con `-u`            |
|---------------------------------|--------------------|-------------------------|
| Ejecuta `pre-migration.py`      | ❌ Nunca           | ✅ Siempre              |
| Muestra traceback completo      | ❌ Error genérico  | ✅ Línea exacta         |
| CHECK constraint con NULL       | ❌ CheckViolation  | ✅ Datos migrados antes |
| CHECK constraint con 0.0        | ❌ CheckViolation  | ✅ Datos migrados antes |
| Estado BD si falla              | ⚠️ Inconsistente  | ✅ Rollback limpio      |
