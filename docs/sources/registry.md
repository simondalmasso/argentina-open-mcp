# Source registry

The runtime registry lives in `src/argentina_open_data/registry.py`. It is deliberately dataset-scoped. A publisher or portal name is not enough to grant one license to every resource it exposes.

| Registry ID | Publisher / resource | License policy | Admission | Evidence |
|---|---|---|---|---|
| `georef.territories` | Servicio Georef, territorial reference resources | CC BY 4.0 | Verified for the resources covered by Georef's terms | [Official terms](https://www.argentina.gob.ar/georef/condiciones-de-uso-y-licencia) |
| `bcra.website-content` | BCRA institutional website content | Custom terms | Metadata only; no bulk redistribution | [Official legal notice](https://www.bcra.gob.ar/aviso-legal/) |

## Admission states

- `VERIFIED`: license evidence, review date and a positive redistribution assessment are present.
- `METADATA_ONLY`: source metadata and official links may be listed, but the dataset is not approved for redistribution.
- `QUARANTINED`: license evidence or scope is missing, ambiguous or incompatible with the intended use.

Custom terms must include a valid evidence URL, allowed purposes and explicit redistribution, commercial-use, attribution, integrity and share-alike conditions. Without that information, `assess_reuse(CUSTOM_TERMS)` returns a quarantine decision.

Additional candidates such as INDEC products, OEDE datasets, provincial statistical portals, IGN and BAHRA are not pre-approved here. They enter the registry only after the exact resource and its current terms are reviewed. In particular, the CC BY-NC-SA claim previously associated with Tucumán has not been promoted to a source record because a primary source establishing its applicability to a specific dataset was not verified in this pass.
