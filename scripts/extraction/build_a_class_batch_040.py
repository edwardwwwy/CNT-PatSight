#!/usr/bin/env python3
"""Build A-class packages for the six full texts recovered in the final retry."""

from __future__ import annotations

import json
import re
from typing import Any

from scripts.extraction.batch_common import (
    BATCH_ID,
    ROOT,
    EvidenceStore,
    load_metadata,
)
from scripts.extraction.build_a_class_batch_002 import publish_package
from scripts.extraction.build_a_class_batch_039 import build_source, rec

BATCH_NUMBER = 40
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)


def bo_records() -> list[dict[str, Any]]:
    path = ROOT / "data/interim/parsed_text/by_source/LIT_DB283D1C5235DA93.parsed.json"
    tables = json.loads(path.read_text(encoding="utf-8"))["tables"]
    records: list[dict[str, Any]] = []
    labels = ("SOBOL", "EI", "OKG")
    for label, table in zip(labels, tables[1:4], strict=True):
        lines = table["text"].splitlines()[1:]
        for line in lines:
            columns = line.split("\t")
            if len(columns) != 7:
                continue
            number, metal, co, mo, drying, calcination, raw_yield = columns
            cleaned = raw_yield.replace("鈭?", "-").replace("−", "-").replace("卤", "±")
            match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
            if match is None:
                raise ValueError(f"Cannot parse carbon yield: {raw_yield}")
            mean_yield = match.group(0)
            records.append(
                rec(
                    f"{label}_{int(number):02d}",
                    f"{label} point {number}",
                    catalyst=f"{metal} wt% Co-Mo/Al2O3",
                    active_metals="Co; Mo" if int(mo) else "Co",
                    metal_ratio=(f"total metal {metal} wt%; Co {co} wt%; Mo {mo} wt%"),
                    prep=(
                        "Wet impregnation; "
                        f"drying {drying} C; calcination {calcination} C for 2 h in air."
                    ),
                    drying=f"{drying} C",
                    calcination=f"{calcination} C for 2 h in air",
                    result=(
                        f"{label} experimental point {number}: total metal "
                        f"{metal} wt%, Co {co} wt%, Mo {mo} wt%, drying "
                        f"{drying} C, calcination {calcination} C; carbon "
                        f"yield {cleaned}%."
                    ),
                    yield_original=f"{mean_yield}% carbon yield",
                )
            )
    return records


def diatomite_records() -> list[dict[str, Any]]:
    records = []
    for metal in ("Ni", "Co"):
        for concentration in ("0.5", "1.0", "1.5"):
            for temperature in (650, 700, 750, 800):
                if metal == "Ni":
                    if temperature <= 700:
                        outcome = "amorphous carbon or low-quality CNT"
                    elif concentration in {"1.0", "1.5"}:
                        outcome = "medium-quality MWCNT"
                    else:
                        outcome = "CNT quality below the 1.0-1.5 M Ni optimum"
                else:
                    outcome = "MWCNT formation"
                    if concentration == "1.5" and temperature in {750, 800}:
                        outcome = "optimal high-quality MWCNT; diameter 30-170 nm"
                records.append(
                    rec(
                        f"{metal.upper()}_{concentration.replace('.', 'P')}M_T{temperature}",
                        f"{metal} {concentration} M, {temperature} C",
                        catalyst=f"{metal} nitrate-derived catalyst on diatomite",
                        active_metals=metal,
                        metal_ratio=f"{concentration} M {metal} salt solution",
                        temp=str(temperature),
                        result=outcome,
                        product_type=(
                            "MWCNT"
                            if "MWCNT" in outcome
                            else "carbon/CNT screening product"
                        ),
                        outer_range=(
                            "30-170"
                            if concentration == "1.5"
                            and temperature in {750, 800}
                            and metal == "Co"
                            else ""
                        ),
                    )
                )
    return records


SOURCES: dict[str, dict[str, Any]] = {
    "LIT_DB283D1C5235DA93": {
        "scope": "All 61 physical experiments in the Sobol, EI and OKG catalyst-optimization tables.",
            "file": "data/raw/literature/html/LIT_DB283D1C5235DA93.html",
        "common": {
            "support": "porous Al2O3, 200 m2/g",
            "precursor": "cobalt nitrate hexahydrate; ammonium heptamolybdate tetrahydrate",
            "preparation_method": "wet_impregnation",
            "stage": "ethylene_CVD",
            "reactor": "5.5 cm ID, 1.3 m horizontal quartz-tube furnace",
            "carbon": "C2H4",
            "carbon_flow": "30 sccm",
            "reducing": "H2",
            "reducing_flow": "30 sccm",
            "inert": "N2",
            "inert_flow": "150 sccm",
            "temp": "690",
            "time": "10",
            "product_type": "CNT",
        },
        "records": bo_records(),
        "issue": "Each table value is the reported mean of four repeat experiments. Typical TEM/Raman/TGA properties are not assigned to every optimization point because the source does not identify a run-specific characterization mapping.",
    },
    "LIT_9B1D9A7023DB7A6C": {
        "scope": "Complete 2-metal x 3-concentration x 4-temperature diatomite screen.",
            "file": "data/raw/literature/html/LIT_9B1D9A7023DB7A6C.html",
        "common": {
            "support": "natural diatomite",
            "prep": "0.5 g diatomite impregnated with alcohol solution of metal nitrate; dried 13-15 min at 80-100 C and heated under Ar.",
            "stage": "propane_butane_CVD",
            "reactor": "atmospheric-pressure quartz-tube CVD",
            "carbon": "propane-butane mixture",
            "carbon_flow": "90 cm3/min",
            "time": "30",
            "product_type": "MWCNT",
            "raman_laser": "473",
        },
        "records": diatomite_records(),
        "issue": "Raman-quality classifications are reported mainly as trends and figures; the complete factorial conditions are preserved while only the printed optimum diameter range is numeric.",
    },
    "LIT_09E1F558A5050320": {
        "scope": "Baseline, fixed-ferrocene and optimized-ferrocene VA-CNT growth conditions.",
        "file": "data/raw/literature/pdf/LIT_09E1F558A5050320_b7b6566ff764.pdf",
        "common": {
            "catalyst": "Al/Fe/Mo multilayer on Si(100)",
            "active_metals": "Fe; Mo",
            "support": "10 nm Al / 1 nm Fe / 0.2 nm Mo on Si(100)",
            "prep": "Electron-beam evaporated multilayer catalyst film.",
            "stage": "acetylene_CVD",
            "reactor": "1.5 inch quartz-tube single-stage furnace",
            "carbon": "C2H2",
            "reducing": "H2",
            "reducing_flow": "100 sccm",
            "inert": "Ar",
            "inert_flow": "500 sccm",
            "temp_range": "550-900",
            "time": "60",
            "product_type": "vertically aligned MWCNT with minor top-surface SWCNT",
        },
        "records": [
            rec(
                "BASELINE",
                "predeposited film without ferrocene",
                carbon_flow="2.9 sccm",
                result="Baseline temperature series without ferrocene; growth saturated after a few hundred micrometres and showed strong film-to-film variation.",
            ),
            rec(
                "FERRO4_FIXED",
                "4 mg/h ferrocene, fixed gas comparison",
                carbon_flow="2.9 sccm",
                promoter="ferrocene 4 mg/h",
                result="Adding 4 mg/h ferrocene increased film thickness and shifted the temperature optimum upward.",
            ),
            rec(
                "FERRO4_OPT",
                "optimized 4 mg/h ferrocene to 12.4 sccm acetylene",
                carbon_flow="12.4 sccm",
                promoter="ferrocene 4 mg/h",
                result="Maximum VA-CNT film thickness 3.25 mm; MWCNTs had four to ten shells and diameter distribution peaking near 10 nm.",
                yield_original="3.25 mm CNT film thickness",
                outer="10",
                length="film thickness 3.25 mm",
            ),
        ],
        "issue": "Most temperature-by-thickness values are graph-readable only; the printed feed conditions, grouped curves and 3.25 mm optimum are retained.",
    },
    "LIT_619441B609804F78": {
        "scope": "Bithiophene-free, low-pressure optimum, composite-forming and pyrolysis regimes.",
            "file": "data/raw/literature/html/LIT_619441B609804F78.html",
        "common": {
            "catalyst": "ferrocene-derived Fe aerosol",
            "active_metals": "Fe",
            "support": "unsupported aerosol catalyst",
            "metal_ratio": "ferrocene partial pressure 0.17 Pa",
            "prep": "Ferrocene and bithiophene vapor carried from thermostated cartridges by N2.",
            "stage": "aerosol_CVD",
            "reactor": "floating-catalyst aerosol CVD reactor",
            "carbon": "C2H4",
            "carbon_flow": "0.22 vol%",
            "cofeed": "CO2",
            "cofeed_flow": "0.20 vol%",
            "inert": "N2",
            "temp": "1000",
            "product_type": "SWCNT",
        },
        "records": [
            rec(
                "BT0",
                "no bithiophene baseline",
                promoter="none",
                result="Baseline SWCNT film; geometric mean nanotube length about 7 micrometre.",
                length="geometric mean 7 micrometre",
            ),
            rec(
                "BT0025",
                "0.025 Pa bithiophene optimum",
                promoter="bithiophene 0.025 Pa; Fe:S molar ratio 3.4",
                result="Low-pressure optimum enhanced SWCNT yield and improved equivalent sheet resistance by about two-fold.",
            ),
            rec(
                "BT008",
                "0.08 Pa bithiophene composite",
                promoter="bithiophene 0.08 Pa",
                result="SWCNTs accompanied by few-layer graphene flakes from non-catalytic bithiophene decomposition.",
                product_type="SWCNT/few-layer graphene composite",
            ),
            rec(
                "BT_GT1",
                "bithiophene pyrolysis above 1 Pa",
                promoter="bithiophene above 1 Pa",
                result="Bithiophene pyrolysis produced additional aerosol carbon deposits; at 1000 C this regime no longer represented selective SWCNT promotion.",
                product_type="pyrolytic carbon/SWCNT mixture",
            ),
        ],
        "issue": "The full promoter-response curves are graphical. Printed partial pressures and qualitative regimes are extracted; apparent yield at higher promoter loading includes few-layer graphene.",
    },
    "LIT_54330E2C79FE4C21": {
        "scope": "Pretreatment-temperature and 850 C pretreatment-time comparisons on stainless-steel foil.",
            "file": "data/raw/literature/html/LIT_54330E2C79FE4C21.html",
        "common": {
            "catalyst": "40 micrometre commercial stainless-steel foil",
            "active_metals": "Fe; Cr",
            "support": "1 x 1 inch stainless-steel foil",
            "prep": "Foil thermally pretreated under 1000 sccm Ar; growth conducted at the same temperature.",
            "stage": "methane_CVD",
            "reactor": "automated horizontal quartz-tube thermal CVD",
            "carbon": "CH4",
            "carbon_flow": "100 sccm",
            "inert": "Ar",
            "inert_flow": "1000 sccm purge/pretreatment",
            "time": "30",
            "product_type": "CNT",
        },
        "records": [
            rec(
                "T750_P10",
                "750 C, 10 min pretreatment",
                temp="750",
                prep="Ar pretreatment at 750 C for 10 min.",
                result="No CNT formation was detected.",
            ),
            rec(
                "T850_P10",
                "850 C, 10 min pretreatment",
                temp="850",
                prep="Ar pretreatment at 850 C for 10 min.",
                result="Mixed SWCNT, DWCNT and MWCNT growth; diameter 20-80 nm, Raman ID/IG 0.54 and nearly 100% nanocarbon by TGA.",
                outer_range="20-80",
                raman="0.54",
                product_type="SWCNT/DWCNT/MWCNT mixture",
            ),
            rec(
                "T950_P10",
                "950 C, 10 min pretreatment",
                temp="950",
                prep="Ar pretreatment at 950 C for 10 min.",
                result="MWCNT growth on Fe/Cr-rich sites; high-temperature pretreatment also produced local foil melting.",
                product_type="MWCNT",
            ),
            rec(
                "T850_P2",
                "850 C, 2 min pretreatment",
                temp="850",
                prep="Ar pretreatment at 850 C for 2 min.",
                result="Higher-density CNTs, diameter 10-20 nm and length about 300 nm; Raman ID/IG 0.53.",
                outer_range="10-20",
                length="about 300 nm",
                raman="0.53",
            ),
        ],
        "issue": "The 850 C/10 min product diameter is reported from SEM while TEM also shows multiple wall-number classes; no mass yield is reported.",
    },
    "LIT_77C8EA9D8BC34BDB": {
        "scope": "Low-temperature SWCNT catalyst-film and pretreatment comparisons.",
        "file": "data/raw/literature/pdf/LIT_77C8EA9D8BC34BDB_9880b53c0fdf.pdf",
        "common": {
            "active_metals": "Fe",
            "support": "Si/SiO2 or Si3N4",
            "prep": "Sub-nanometre evaporated catalyst film, typically annealed 15 min in NH3 or H2 before growth.",
            "stage": "low_pressure_cold_wall_CVD",
            "reactor": "resistively heated cold-wall vacuum CVD chamber",
            "carbon": "undiluted C2H2",
            "carbon_flow": "10^-3 to 10^-2 mbar",
            "time": "5",
            "pressure": "10^-3 to 10^-2 mbar acetylene",
            "product_type": "SWCNT",
            "raman_laser": "514.5; 633; 785",
        },
        "records": [
            rec(
                "FE03_T500",
                "0.3 nm Fe at 500 C",
                catalyst="0.3 nm Fe film",
                temp="500",
                result="Long bundled SWCNTs on Si/SiO2 after NH3/H2 catalyst restructuring.",
            ),
            rec(
                "FE03_T420",
                "0.3 nm Fe at 420 C",
                catalyst="0.3 nm Fe film",
                temp="420",
                result="Low-temperature SWCNT growth with narrower diameter distribution than at higher temperature.",
            ),
            rec(
                "ALFEAL_T350",
                "Al/0.3 nm Fe/0.2 nm Al at 350 C",
                catalyst="Al/Fe(0.3 nm)/Al(0.2 nm)",
                temp="350",
                result="Lowest confirmed SWCNT growth temperature; HRTEM and Raman showed SWCNTs, with more defects/disordered carbon than at 500 C.",
            ),
            rec(
                "FE01_SIN_T500",
                "0.1 nm Fe on Si3N4 at 500 C",
                catalyst="0.1 nm Fe film",
                support="50 nm Si3N4 membrane",
                temp="500",
                result="Low-density sub-3-nm Fe particles nucleated SWCNTs with diameter 1.2-2.3 nm.",
                outer_range="1.2-2.3",
            ),
            rec(
                "VACUUM_PREANNEAL",
                "vacuum-preannealed control",
                catalyst="thin Fe film",
                temp_range="350-500",
                prep="Vacuum preannealing below 10^-5 mbar before identical acetylene exposure.",
                result="No CNT growth; NH3 or H2 pretreatment was required for effective low-temperature catalyst restructuring.",
            ),
        ],
        "issue": "Figure-specific catalyst thickness/temperature combinations are retained as representative physical conditions; Raman intensities cannot be converted into absolute chirality abundances.",
    },
}


def main() -> None:
    metadata = load_metadata()
    store = EvidenceStore()
    metrics: list[dict[str, Any]] = []
    try:
        for source_id, spec in SOURCES.items():
            metrics.append(
                publish_package(
                    source_id,
                    build_source(metadata[source_id], spec, store),
                )
            )
    finally:
        store.close()
    result = {
        "batch_id": BATCH_NAME,
        "sources": metrics,
        "total_runs": sum(item["row_counts"]["source_run"] for item in metrics),
        "status": "completed_needs_review",
    }
    (REPORT_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
