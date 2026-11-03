# Argentina Open Data

**Datos públicos argentinos, con contexto territorial, trazabilidad y límites estadísticos explícitos.**

Argentina Open Data es una plataforma pública para descubrir, consultar, comparar y reutilizar datos de Argentina. Argentina Open MCP es su interfaz para agentes y desarrolladores. Ambos productos comparten un kernel de datos y un contrato de respuesta; ninguno depende de que el otro exista.

> Estado: kernel de datos y primer adaptador territorial implementados; no hay todavía API REST/MCP ni aplicación web desplegadas. La rama de trabajo contiene contratos canónicos, comparabilidad con warnings, registro de fuentes y perfil Georef. Las fuentes, sus licencias y su granularidad se incorporan únicamente después de una verificación por dataset.

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
  sources/georef.py       # Cliente de lectura Georef v2

tests/                    # Contratos y reglas del kernel
docs/architecture/        # Límites y decisiones de arquitectura
docs/governance/          # Procedencia, cobertura y política de licencias
docs/sources/             # Registro y perfiles de fuentes con evidencia
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

### Primera ingesta territorial

La aplicación **no descarga datos al arrancar**. Para capturar un snapshot acotado de provincias desde Georef:

```bash
argentina-open snapshot-georef provincias --limit 1000 --max-pages 1
```

El resultado se guarda en `data/snapshots/` como objeto inmutable identificado por SHA-256. Para ampliar cobertura, indicar explícitamente otro recurso y un máximo de páginas; cada solicitud respeta la cadencia conservadora del cliente Georef. No publicar datasets adicionales hasta revisar sus términos particulares.

### Docker Compose

```bash
docker compose up --build -d
docker compose --profile ingest run --rm ingest-georef provincias --limit 1000 --max-pages 1
```

Compose comparte el volumen de snapshots entre REST y MCP. La ingesta es un perfil manual, nunca una tarea de inicio automática.

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
```

## Productos previstos

1. **Argentina Open Data:** buscador y catálogo, fichas metodológicas, mapas, series, comparadores, descargas y estado verificable de fuentes.
2. **Argentina Open MCP:** herramientas MCP acotadas y REST `/api/v1` para descubrir indicadores, consultar observaciones, comparar territorios y recuperar procedencia.

La lista de herramientas y los proveedores de ejecución se definirán después de probar contratos y fuentes reales. No se fija todavía un framework MCP ni un proveedor de hosting.

## Estado del trabajo

Consultar [la arquitectura](docs/architecture/overview.md), [la política de datos y licencias](docs/governance/data-and-licenses.md), [el registro de fuentes](docs/sources/registry.md), [el perfil de Georef](docs/sources/georef.md), [el perfil BCRA](docs/sources/bcra.md) y [el plan de implementación](docs/plans/2026-11-02-foundation.md).

## Licencia del software

El código de este repositorio se ofrece bajo Apache-2.0. Esta licencia **no** se extiende a los datasets, mapas, marcas ni contenidos de terceros; cada recurso conserva sus propias condiciones.
