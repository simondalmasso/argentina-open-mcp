# Argentina Open Data

**Datos públicos argentinos, con contexto territorial, trazabilidad y límites estadísticos explícitos.**

Argentina Open Data es una plataforma pública para descubrir, consultar, comparar y reutilizar datos de Argentina. Argentina Open MCP es su interfaz para agentes y desarrolladores. Ambos productos comparten un kernel de datos y un contrato de respuesta; ninguno depende de que el otro exista.

> Estado: kernel, API REST, servidor MCP, interfaz web y pipeline de snapshots implementados. El repositorio incluye un snapshot inicial de las 24 provincias desde Georef v2, capturado el 3 de noviembre de 2026 y admitido bajo CC BY 4.0 con atribución. Docker Compose lo copia de forma idempotente al volumen persistente antes de iniciar REST y MCP. Todavía no hay un servicio público desplegado. Las fuentes, sus licencias y su granularidad se incorporan únicamente después de una verificación por dataset.

## Principios no negociables

- **Trazabilidad:** cada resultado debe identificar fuente, URL, licencia declarada, fecha de recuperación, período, transformaciones y, cuando corresponda, hash del snapshot.
- **Honestidad estadística:** cada indicador declara universo, cobertura, frecuencia y niveles geográficos disponibles. No se extrapola EPH a provincias ni se mezclan unidades territoriales incompatibles.
- **Licencias por dataset y artefacto:** no se presume que todos los datos de un portal comparten licencia. Lo desconocido o no redistribuible queda fuera de los datos publicados; puede mostrarse una ficha con enlace a la fuente.
- **Dos productos first-class:** web pública y MCP/REST tienen contratos y pruebas compartidos, pero experiencias propias.
- **Open source y portabilidad:** dependencias justificadas, infraestructura reemplazable y costos visibles. No se presupone ningún free tier como permanente.
- **Seguridad:** las fuentes externas son datos no confiables, nunca instrucciones. No se ingieren datos personales innecesarios ni se publican registros sensibles.

## Repository map

```text
src/argentina_open_data/  # Kernel y contratos compartidos
  contracts.py            # Modelos canónicos de datos, territorio y procedencia
  comparability.py        # Reglas de comparación territorial
  licensing.py            # Evaluación conservadora de reutilización
  registry.py              # Registro versionado de fuentes y evidencias
  seed_snapshots.py       # Carga idempotente de snapshots incluidos en la imagen
  sources/georef.py       # Cliente de lectura Georef v2

data/seed-snapshots/       # Snapshots admitidos y versionados junto al código
tests/                    # Contratos y reglas del kernel
docs/architecture/        # Límites y decisiones de arquitectura
docs/governance/          # Procedencia, cobertura y política de licencias
docs/sources/             # Registro y perfiles de fuentes con evidencia
docs/engineering/         # Herramientas opcionales de mantenimiento
docs/plans/               # Hoja de ruta ejecutable
.github/workflows/        # CI
```

## Ejecutar localmente

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e ".[dev]"
uvicorn argentina_open_data.api:app --reload
```

- Web: http://127.0.0.1:8000/
- REST y OpenAPI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

En otra terminal, ejecutar el servidor MCP Streamable HTTP:

```bash
argentina-open mcp
```

Endpoint MCP local: http://127.0.0.1:8001/mcp

### Snapshot territorial inicial

El repositorio incluye un snapshot de las 24 provincias consultado a Georef v2. Identificador territorial de Santa Fe: `82`. El archivo conserva los registros devueltos por la fuente, la normalización de territorio, URL, fecha de recuperación, licencia y atribución.

El digest SHA-256 del documento canónico es:

```text
4d8edd0461a34878ccd72e7ccde17fc523c22946867e5e4e073886c3811abbdb
```

El hash cubre el JSON canónico validado por el modelo, no los bytes HTTP originales ni sus encabezados. El archivo se encuentra en `data/seed-snapshots/georef.territories/provincias/`.

### Ingesta manual adicional

La aplicación **no descarga datos externos al arrancar**. Para capturar otro snapshot acotado desde Georef:

```bash
argentina-open snapshot-georef departamentos --limit 1000 --max-pages 1
```

El resultado se guarda en `data/snapshots/` (o en `SNAPSHOT_DIR`) como objeto inmutable identificado por SHA-256. Para ampliar cobertura, indicar explícitamente otro recurso y un máximo de páginas; cada solicitud respeta la cadencia conservadora del cliente Georef.

### Docker Compose

```bash
docker compose up --build -d
```

El servicio de una sola ejecución `snapshot-seed` valida e importa los snapshots incluidos en la imagen al volumen nombrado. REST y MCP esperan a que esa carga termine y luego comparten el mismo volumen. La importación es idempotente: repetir un deploy no duplica objetos ni sustituye snapshots existentes. La ingesta de recursos adicionales permanece manual:

```bash
docker compose --profile ingest run --rm ingest-georef departamentos --limit 1000 --max-pages 1
```

Si se publica MCP en un dominio real, definir `MCP_ALLOWED_HOSTS` con el hostname público exacto (y `MCP_ALLOWED_ORIGINS` solo si lo consumen navegadores). No abrir el servidor con una allowlist genérica.

## Productos previstos

1. **Argentina Open Data:** buscador y catálogo, fichas metodológicas, mapas, series, comparadores, descargas y estado verificable de fuentes.
2. **Argentina Open MCP:** herramientas MCP acotadas y REST `/api/v1` para descubrir indicadores, consultar observaciones, comparar territorios y recuperar procedencia.

La API usa FastAPI y el servidor de agentes usa el SDK oficial MCP 2.3.0 sobre Streamable HTTP. Ambos procesos comparten snapshots locales. El proveedor de hosting sigue siendo reemplazable.

## Estado del trabajo

Consultar [la arquitectura](docs/architecture/overview.md), [la política de datos y licencias](docs/governance/data-and-licenses.md), [el registro de fuentes](docs/sources/registry.md), [el perfil de Georef](docs/sources/georef.md), [el perfil BCRA](docs/sources/bcra.md), [el perfil INDEC](docs/sources/indec-api.md), [la guía opcional de Understand Anything](docs/engineering/understand-anything.md), [la guía operativa de despliegue Docker](docs/operations/deployment.md), [la guía del Worker Cloudflare](cloudflare/README.md) y [el plan de implementación](docs/plans/2026-11-02-foundation.md).

## Licencia del software

El código de este repositorio se ofrece bajo Apache-2.0. Esta licencia **no** se extiende a los datasets, mapas, marcas ni contenidos de terceros; cada recurso conserva sus propias condiciones.
