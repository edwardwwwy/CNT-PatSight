#!/usr/bin/env python3
"""Build the remaining evidence-grounded, physically extractable A-class papers."""

from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import (
    BATCH_ID,
    ROOT,
    TABLES,
    EvidenceStore,
    catalyst_row,
    cost_row,
    evidence_row,
    issue_row,
    load_metadata,
    master_row,
    process_row,
    run_row,
    yield_row,
)
from scripts.extraction.build_a_class_batch_002 import publish_package

BATCH_NUMBER = 39
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)


def rec(code: str, label: str, **values: Any) -> dict[str, Any]:
    return {"code": code, "label": label, **values}


SOURCES: dict[str, dict[str, Any]] = {
    "LIT_7F0D271A0CEB3037": {
        "scope": "Ni-film and catalyst-free Si temperature-series comparison.",
            "file": "data/raw/literature/html/LIT_7F0D271A0CEB3037.html",
        "common": {
            "catalyst": "10 nm Ni film",
            "active_metals": "Ni",
            "support": "Si substrate",
            "prep": "Ni film deposited on Si; compared with bare Si.",
            "stage": "thermal_CVD_temperature_series",
            "reactor": "horizontal thermal CVD reactor",
            "carbon": "ferrocene-derived carbon/catalyst vapor",
            "temp_range": "790-880",
            "product_type": "MWCNT",
        },
        "records": [
            rec(
                "NI_SERIES",
                "10 nm Ni/Si, 790-880 C series",
                result="CNT height increased with temperature and reached 34.28 micrometre at 860 C; at 880 C the mean outer and inner diameters were 50.7 and 16.3 nm.",
                outer="50.7",
                inner="16.3",
                length="height 34.28 micrometre at 860 C",
            ),
            rec(
                "BARE_SI_SERIES",
                "bare Si, 790-880 C series",
                catalyst="ferrocene-derived Fe without Ni film",
                active_metals="Fe",
                result="Catalyst-free Si comparison; at 880 C the mean outer and inner diameters were 20.8 and 10.2 nm.",
                outer="20.8",
                inner="10.2",
            ),
        ],
        "issue": "Intermediate temperature-dependent heights and diameters are figure-readable only; the series and printed endpoints are retained without inventing point values.",
    },
    "LIT_697F549224B22272": {
        "scope": "Fe, Fe-Cu, Fe-Co and Fe-Ni methane-CVD catalyst comparison.",
            "file": "data/raw/literature/html/LIT_697F549224B22272.html",
        "common": {
            "support": "Si strip",
            "prep": "10 mmol metal-chloride solutions in 20 mL DI water, sonicated 10 min and deposited on Si; bimetallic solutions were equimolar.",
            "stage": "methane_CVD",
            "reactor": "20 mm ID, 1800 mm quartz tube",
            "carbon": "CH4",
            "carbon_flow": "10 sccm",
            "reducing": "H2",
            "reducing_flow": "20 sccm",
            "temp": "950",
            "time": "30",
            "product_type": "CNT",
        },
        "records": [
            rec(
                "FE",
                "Fe catalyst",
                catalyst="Fe",
                active_metals="Fe",
                result="Longest observed CNT 1.32 cm; average length 0.42 cm; standard deviation 0.23 cm.",
                yield_original="1.32 cm longest CNT",
                length="longest 1.32 cm; average 0.42 cm",
            ),
            rec(
                "FECU",
                "Fe-Cu catalyst",
                catalyst="Fe-Cu",
                active_metals="Fe; Cu",
                result="Longest observed CNT 0.85 cm; average length 0.36 cm; standard deviation 0.16 cm.",
                yield_original="0.85 cm longest CNT",
                length="longest 0.85 cm; average 0.36 cm",
            ),
            rec(
                "FECO",
                "Fe-Co catalyst",
                catalyst="Fe-Co",
                active_metals="Fe; Co",
                result="Longest observed CNT 0.65 cm; average length 0.20 cm; standard deviation 0.13 cm.",
                yield_original="0.65 cm longest CNT",
                length="longest 0.65 cm; average 0.20 cm",
            ),
            rec(
                "FENI",
                "Fe-Ni catalyst",
                catalyst="Fe-Ni",
                active_metals="Fe; Ni",
                result="Longest observed CNT 0.55 cm; average length 0.14 cm; standard deviation 0.12 cm.",
                yield_original="0.55 cm longest CNT",
                length="longest 0.55 cm; average 0.14 cm",
            ),
        ],
        "issue": "The methods state 15 min while the results recalculate growth velocity using 30 min; table units and narrative length units also conflict. Narrative centimetre lengths and the results-section duration are retained with this issue flagged.",
    },
    "LIT_B001742209BFB7A3": {
        "scope": "Alcohol catalytic CVD temperature series on cobalt-acetate-coated Si.",
        "file": "data/raw/literature/pdf/LIT_B001742209BFB7A3_700c5f7722a7.pdf",
        "common": {
            "catalyst": "cobalt acetate-derived Co",
            "active_metals": "Co",
            "support": "Si",
            "prep": "42 mg cobalt acetate in 10 mL ethanol; stirred 10 min, sonicated 2 h; Si dipped 5 min, withdrawn at 4 cm/min and heated at 400 C.",
            "stage": "alcohol_catalytic_CVD",
            "reactor": "50 cm ceramic tube furnace",
            "carbon": "ethanol vapor",
            "inert": "Ar",
            "inert_flow": "250 sccm",
            "time": "50",
            "pressure": "5-10 Torr ethanol-vapor growth pressure",
        },
        "records": [
            rec(
                "T700",
                "ACCVD at 700 C",
                temp="700",
                result="MWCNTs with outer diameters approximately 12-37 nm appeared with carbon nanopowder.",
                outer_range="12-37",
                product_type="MWCNT",
            ),
            rec(
                "T800",
                "ACCVD at 800 C",
                temp="800",
                result="Mainly SWCNT bundles with mean diameter 1.6 nm; optical gap 1.16 eV and thermal conductivity 170.4 W/mK.",
                outer="1.6",
                product_type="SWCNT",
                application="optical gap 1.16 eV; thermal conductivity 170.4 W/mK",
            ),
            rec(
                "T900",
                "ACCVD at 900 C",
                temp="900",
                result="Majority MWCNTs with a small amount of SWCNT bundles; thermal conductivity 118.6 W/mK.",
                product_type="mixed MWCNT/SWCNT",
                application="thermal conductivity 118.6 W/mK",
            ),
        ],
        "issue": "The 400 and 500 C conditions mainly produced carbon nanopowder and are not promoted as successful CNT production runs.",
    },
    "LIT_3B5A2676F1FE1646": {
        "scope": "Table-1 natural-gas:H2 ratio and temperature matrix on 2 wt% Ni/gamma-Al2O3.",
        "file": "data/raw/literature/pdf/LIT_3B5A2676F1FE1646_93a73cbd3a65.pdf",
        "common": {
            "catalyst": "2 wt% Ni/gamma-Al2O3",
            "active_metals": "Ni",
            "support": "gamma-Al2O3",
            "metal_ratio": "2 wt% Ni/gamma-Al2O3",
            "prep": "Sol-gel gamma-Al2O3 calcined 850 C; Ni nitrate impregnated and dried 2 h at 200 C; reduced at 480-500 C for 1 h in 20 vol% H2/Ar at 500 mL/min.",
            "stage": "natural_gas_decomposition",
            "reactor": "CVD quartz tube",
            "carbon": "natural gas",
            "reducing": "H2",
            "product_type": "CNT/nanocarbon",
        },
        "records": [
            rec(
                "NG2H1_T650",
                "NG:H2 2:1, 650 C",
                temp="650",
                gas="NG:H2 = 2:1",
                result="Nanocarbon yield 2.2 g/g metal.",
                yield_original="2.2 g nanocarbon/g metal",
            ),
            rec(
                "NG2H1_T750",
                "NG:H2 2:1, 750 C",
                temp="750",
                gas="NG:H2 = 2:1",
                result="Nanocarbon yield 5.2 g/g metal.",
                yield_original="5.2 g nanocarbon/g metal",
            ),
            rec(
                "NG3H1_T750",
                "NG:H2 3:1, 750 C",
                temp="750",
                gas="NG:H2 = 3:1",
                result="Nanocarbon yield 5.5 g/g metal.",
                yield_original="5.5 g nanocarbon/g metal",
            ),
            rec(
                "NG1H1_T850",
                "NG:H2 1:1, 850 C",
                temp="850",
                gas="NG:H2 = 1:1",
                result="Nanocarbon yield 6.2 g/g metal.",
                yield_original="6.2 g nanocarbon/g metal",
            ),
            rec(
                "NG2H1_T850",
                "NG:H2 2:1, 850 C",
                temp="850",
                gas="NG:H2 = 2:1",
                result="Nanocarbon yield 7.9 g/g metal.",
                yield_original="7.9 g nanocarbon/g metal",
            ),
            rec(
                "NG3H1_T850",
                "NG:H2 3:1, 850 C",
                temp="850",
                gas="NG:H2 = 3:1",
                result="Maximum table yield 10.7 g/g metal.",
                yield_original="10.7 g nanocarbon/g metal",
            ),
            rec(
                "NG2H1_T900",
                "NG:H2 2:1, 900 C",
                temp="900",
                gas="NG:H2 = 2:1",
                result="Nanocarbon yield 8.4 g/g metal.",
                yield_original="8.4 g nanocarbon/g metal",
            ),
            rec(
                "NG3H1_T900",
                "NG:H2 3:1, 900 C",
                temp="900",
                gas="NG:H2 = 3:1",
                result="Nanocarbon yield 9.1 g/g metal.",
                yield_original="9.1 g nanocarbon/g metal",
            ),
        ],
        "issue": "The table reports nanocarbon rather than a purified CNT-only mass; 900 C is also described as undesirable because rapid coking/deactivation and alumina phase change occur.",
    },
    "LIT_7CABEA170695D083": {
        "scope": "Three-temperature Cu-filled VACNT PECVD matrix on thin Cu foil.",
        "file": "data/raw/literature/pdf/LIT_7CABEA170695D083_6e369704e8db.pdf",
        "common": {
            "catalyst": "in-situ Cu islands from 0.1 mm Cu foil",
            "active_metals": "Cu",
            "support": "0.1 mm Cu foil",
            "prep": "Cu foil sonicated in acetone and isopropanol for 10 min each; NH3 plasma formed catalytic sites.",
            "stage": "DC_PECVD",
            "reactor": "DC plasma-enhanced CVD chamber, 70 W",
            "carbon": "C2H2",
            "carbon_flow": "30 sccm",
            "cofeed": "NH3",
            "cofeed_flow": "110 sccm",
            "time": "30",
            "pressure": "7 Torr",
            "product_type": "Cu-filled VACNT",
        },
        "records": [
            rec(
                "S650",
                "S650",
                temp="650",
                result="Sparse, non-uniform Cu-filled VACNTs; height 0.4-10 micrometre and diameter 300-670 nm; continuous Cu filling.",
                outer_range="300-670",
                length="height 0.4-10 micrometre",
            ),
            rec(
                "S700",
                "S700",
                temp="700",
                result="Uniform free-standing Cu-filled VACNTs; average diameter 940 nm and height 14 micrometre; continuous Cu filling.",
                outer="940",
                length="height 14 micrometre",
                application="turn-on field 2.33 V/micrometre; threshold field 3.29 V/micrometre",
            ),
            rec(
                "S760",
                "S760",
                temp="760",
                result="Bundled Cu-filled VACNTs; average diameter 1200 nm and height 8.5 micrometre; Cu filling became discontinuous segments and dots.",
                outer="1200",
                length="height 8.5 micrometre",
            ),
        ],
        "issue": "One XRD paragraph labels the low-temperature sample 600 C, while methods, sample names, microscopy and conclusions consistently identify it as 650 C.",
    },
    "LIT_E949264AD5000FE1": {
        "scope": "Fast-CVD acetylene and ethylene carbon-input/residence-time comparison.",
            "file": "data/raw/literature/html/LIT_E949264AD5000FE1.html",
        "common": {
            "catalyst": "aerosol/floating catalyst used in Fast-CVD",
            "active_metals": "Fe",
            "support": "unsupported aerosol catalyst",
            "prep": "Fast-CVD catalyst feed as reported by the source.",
            "stage": "Fast_CVD",
            "reactor": "Fast-CVD flow reactor",
            "time": "10",
            "product_type": "CNT forest",
        },
        "records": [
            rec(
                "ACETYLENE_SERIES",
                "acetylene Fast-CVD series",
                carbon="C2H2",
                carbon_flow="2-30 sccm",
                temp_range="1083 K",
                gas="total inlet 500-5000 sccm",
                result="Yield and morphology mapped against carbon flux and dwell time; optimum dwell time was about 5 s.",
            ),
            rec(
                "ETHYLENE_SERIES",
                "ethylene Fast-CVD comparison",
                carbon="C2H4",
                temp_range="1073 K",
                gas="total inlet 500-5000 sccm",
                result="Ethylene comparison required roughly 15 times greater carbon input than acetylene; acetylene achieved higher carbon utilization efficiency.",
            ),
        ],
        "issue": "The multidimensional flow/flux matrix is plot-based; printed ranges, the approximately 5 s optimum and the 15-fold comparison are retained as grouped series rather than fabricated point rows.",
    },
    "LIT_FBC1DDD86139179A": {
        "scope": "Gold-supported catalyst screens across support, loading and hydrocarbon.",
        "file": "data/raw/literature/pdf/LIT_FBC1DDD86139179A_bc7b53adb2fa.pdf",
        "common": {
            "active_metals": "Au",
            "prep": "Gold salt or colloidal Au deposited on oxide support at 0.1 or 0.5 wt% loading.",
            "stage": "thermal_CVD",
            "reactor": "laboratory CVD reactor",
            "product_type": "filamentous carbon/CNT",
        },
        "records": [
            rec(
                "AU_AL2O3_CH4",
                "0.5 wt% Au/Al2O3 with methane",
                catalyst="0.5 wt% Au/Al2O3",
                support="Al2O3",
                metal_ratio="0.5 wt% Au",
                carbon="CH4",
                carbon_flow="20 vol% in Ar; 350 sccm total",
                temp="900",
                result="Approximately 10% methane conversion at 900 C and filamentous carbon formation.",
                yield_original="approximately 10% methane conversion",
            ),
            rec(
                "AU_SIO2_CH4",
                "Au/SiO2 with methane",
                catalyst="Au/SiO2",
                support="SiO2",
                carbon="CH4",
                carbon_flow="20 vol% in Ar; 350 sccm total",
                temp_range="700-900",
                result="Support comparison showed weak methane-decomposition activity and filamentous carbon only for active Au-supported formulations.",
            ),
            rec(
                "AU_AL2O3_C2H4",
                "Au/Al2O3 with ethylene",
                catalyst="Au/Al2O3",
                support="Al2O3",
                carbon="C2H4",
                carbon_flow="1 vol% C2H4 with 5 vol% H2",
                temp_range="700-900",
                result="Rapid-heating ethylene CVD produced double-walled CNT-rich material under the reported Au-supported condition.",
                product_type="DWCNT-rich CNT",
            ),
            rec(
                "AU_AL2O3_C2H2",
                "Au/Al2O3 with acetylene",
                catalyst="Au/Al2O3",
                support="Al2O3",
                carbon="C2H2",
                carbon_flow="1 vol% C2H2 with 5 vol% H2",
                temp_range="700-900",
                result="Acetylene CVD produced MWCNTs with reported diameters of 10-50 nm.",
                product_type="MWCNT",
                outer_range="10-50",
            ),
        ],
        "issue": "Several support/loading comparisons are presented graphically or qualitatively; only printed conversion, gas composition and diameter statements are numeric here.",
    },
    "LIT_FB76AA75976322C2": {
        "scope": "In-situ Raman comparison of ethanol CNT growth at 725 and 875 C.",
        "file": "data/raw/literature/pdf/LIT_FB76AA75976322C2_02b54e4c1e57.pdf",
        "common": {
            "catalyst": "approximately 1 nm Co film",
            "active_metals": "Co",
            "support": "SiO2",
            "prep": "Approximately 1 nm Co film on SiO2; heated under 98% Ar/2% H2 before ethanol exposure.",
            "stage": "in_situ_Raman_CVD",
            "reactor": "in-situ Raman CVD cell",
            "carbon": "ethanol vapor",
            "carbon_flow": "2 sccm carrier diverted through room-temperature ethanol bubbler",
            "gas": "initial approximately 80 sccm 98% Ar/2% H2; growth flow 2 sccm",
            "time": "20",
            "product_type": "CNT",
        },
        "records": [
            rec(
                "T725",
                "ethanol growth at 725 C",
                temp="725",
                result="Low-yield condition used to resolve nucleation and early growth dynamics by in-situ Raman spectroscopy.",
            ),
            rec(
                "T875",
                "ethanol growth at 875 C",
                temp="875",
                result="Substantially higher CNT yield than at 725 C; in-situ Raman tracked catalyst activation, nucleation and growth.",
            ),
        ],
        "issue": "The paper emphasizes time-resolved Raman dynamics; absolute mass yield is not reported for either temperature.",
    },
    "LIT_71A66ACE3835B00D": {
        "scope": "Five Fe-Co-Mo/MgO total-metal loadings for LPG CVD.",
        "file": "data/raw/literature/pdf/LIT_71A66ACE3835B00D_993a74362b45.pdf",
        "common": {
            "catalyst": "Fe-Co-Mo/MgO",
            "active_metals": "Fe; Co; Mo",
            "support": "MgO",
            "prep": "Wet impregnation at Fe:Co:Mo = 2:2:1; vacuum dried at 110 C, milled and calcined at 500 C for 4 h.",
            "stage": "LPG_CVD",
            "reactor": "electrically heated vertical tubular reactor",
            "carbon": "LPG",
            "carbon_flow": "25 cm3/min",
            "reducing": "H2",
            "reducing_flow": "19 cm3/min",
            "inert": "Ar",
            "inert_flow": "150 cm3/min",
            "temp_range": "750-850",
            "time": "30",
            "product_type": "MWCNT",
        },
        "records": [
            rec(
                "ML2P5",
                "2.5 wt% total metal",
                metal_ratio="Fe:Co:Mo:MgO = 1:1:0.5:97.5 wt%",
                result="Lower-than-optimum CNT yield; product BET surface area 88 m2/g.",
            ),
            rec(
                "ML5",
                "5 wt% total metal",
                metal_ratio="Fe:Co:Mo:MgO = 2:2:1:95 wt%",
                result="Intermediate metal-loading condition; yield was below the 10 wt% optimum.",
            ),
            rec(
                "ML10",
                "10 wt% total metal",
                metal_ratio="Fe:Co:Mo:MgO = 4:4:2:90 wt%",
                result="Maximum yield 4.55 g CNT/g catalyst, equivalent to 68.98 g CNT/g active components; catalyst pore volume 0.632 cm3/g.",
                yield_original="4.55 g CNT/g catalyst",
                outer_range="4-12",
                inner="2-5",
                application="product BET 229 m2/g; product pore volume 1.024 cm3/g",
            ),
            rec(
                "ML15",
                "15 wt% total metal",
                metal_ratio="Fe:Co:Mo:MgO = 6:6:3:85 wt%",
                result="Yield decreased above the 10 wt% optimum as support pore openings became partially blocked.",
            ),
            rec(
                "ML20",
                "20 wt% total metal",
                metal_ratio="Fe:Co:Mo:MgO = 8:8:4:80 wt%",
                result="Highest loading condition; yield remained below the 10 wt% optimum because accessible pore volume decreased.",
            ),
        ],
        "issue": "The source reports synthesis temperature as a 750-850 C range rather than assigning a single setpoint to each loading; non-optimum yields are graph-only.",
    },
    "LIT_82A4395696545B8B": {
        "scope": "Five green plant extracts at 575 C plus walnut at 800 C.",
        "file": "data/raw/literature/pdf/LIT_82A4395696545B8B_f528eaed35a7.pdf",
        "common": {
            "active_metals": "none reported",
            "support": "oxygen-plasma-cleaned p-Si",
            "prep": "Leaves Soxhlet-extracted with methanol; 0.5 g extract dissolved in 50 mL methanol, sonicated 30 min and drop-cast on 10 x 10 mm Si.",
            "stage": "green_catalyst_CVD",
            "reactor": "thermal CVD furnace",
            "carbon": "C2H2",
            "carbon_flow": "15 sccm",
            "inert": "Ar",
            "inert_flow": "50 sccm",
            "time": "10",
            "product_type": "MWCNT",
        },
        "records": [
            rec(
                "GRASS575",
                "garden grass extract at 575 C",
                catalyst="Cynodon dactylon extract",
                temp="575",
                result="MWCNT growth observed at 575 C; exact yield and dimensions not printed.",
            ),
            rec(
                "ROSE575",
                "rose extract at 575 C",
                catalyst="Rosa extract",
                temp="575",
                result="MWCNT growth observed at 575 C; exact yield and dimensions not printed.",
            ),
            rec(
                "NEEM575",
                "neem extract at 575 C",
                catalyst="Azadirachta indica extract",
                temp="575",
                result="MWCNT growth observed at 575 C; exact yield and dimensions not printed.",
            ),
            rec(
                "KANER575",
                "Kaner extract at 575 C",
                catalyst="Thevetia peruviana extract",
                temp="575",
                result="MWCNT growth observed at 575 C; exact yield and dimensions not printed.",
            ),
            rec(
                "WALNUT575",
                "walnut extract at 575 C",
                catalyst="Juglans regia extract",
                temp="575",
                result="High-density MWNTs, diameter 8-15 nm, length 3600 micrometre, collected mass about 0.0113 g and Raman ID/IG 0.59.",
                yield_original="about 0.0113 g collected CNT",
                outer_range="8-15",
                length="3600 micrometre",
                raman="0.59",
            ),
            rec(
                "WALNUT800",
                "walnut extract at 800 C",
                catalyst="Juglans regia extract",
                temp="800",
                result="Carbon nanobelts and SWCNT signatures appeared; nanobelts had walls around 25 nm thick and Raman ID/IG about 0.90.",
                product_type="CNB/SWCNT/MWCNT mixture",
                raman="0.90",
            ),
        ],
        "issue": "The paper gives an exact collected mass only for walnut at 575 C; other plant-extract yields and dimensions are not numerically tabulated.",
    },
    "LIT_97B977951A7C653F": {
        "scope": "Conventional versus sudden-initiation Co3O4/MgO acetylene CVD.",
        "file": "data/raw/literature/pdf/LIT_97B977951A7C653F_6acf5407590f.pdf",
        "common": {
            "catalyst": "Co3O4/MgO",
            "active_metals": "Co",
            "support": "MgO",
            "prep": "10, 20, 30 and 40 wt% Co3O4/MgO by impregnation; stirred 1 h, dried 120 C and calcined 550 C for 2 h.",
            "stage": "acetylene_CVD",
            "reactor": "quartz-tube atmospheric-pressure CVD",
            "carbon": "C2H2",
            "carbon_flow": "15 sccm",
            "inert": "Ar/carrier gas",
            "inert_flow": "150 sccm during growth",
            "time": "15",
            "product_type": "CNT",
        },
        "records": [
            rec(
                "CONVENTIONAL_SERIES",
                "conventional preheated series",
                metal_ratio="10, 20, 30 and 40 wt% Co3O4/MgO",
                temp_range="500-975",
                result="Conventional preheating produced lower carbon yield, especially above 800 C and above 30 wt% loading.",
            ),
            rec(
                "SUDDEN_SERIES",
                "sudden-initiation series",
                metal_ratio="10, 20, 30 and 40 wt% Co3O4/MgO",
                temp_range="500-975",
                result="Sudden insertion into the hot zone produced considerably higher carbon yield by limiting catalyst aggregation.",
            ),
            rec(
                "SUDDEN20_T600",
                "20 wt% Co3O4/MgO, sudden initiation, 600 C",
                metal_ratio="20 wt% Co3O4/MgO",
                temp="600",
                result="High-quality hollow CNTs with smooth walls and low impurity; diameter range 10-22 nm and mean about 15 nm.",
                outer="15",
                outer_range="10-22",
            ),
        ],
        "issue": "The full loading-by-temperature carbon-yield matrix is graphical; it is represented by two grouped series plus the printed 20 wt%/600 C morphology point.",
    },
    "LIT_94D32BA662BC711A": {
        "scope": "Fe versus Ni catalyst comparison under identical propane APCVD.",
        "file": "data/raw/literature/pdf/LIT_94D32BA662BC711A_27b562cb73bb.pdf",
        "common": {
            "support": "Si(111)",
            "prep": "Approximately 20 nm evaporated metal film; H2 annealed at 900 C for 10 min.",
            "stage": "propane_APCVD",
            "reactor": "hot-wall horizontal quartz-tube APCVD",
            "carbon": "propane",
            "carbon_flow": "200 sccm",
            "temp": "850",
            "time": "60",
            "product_type": "MWCNT",
        },
        "records": [
            rec(
                "FE",
                "Fe catalyst",
                catalyst="20 nm Fe film",
                active_metals="Fe",
                result="Straight Fe-filled MWCNTs by tip growth; C:Fe atomic ratio about 175 and Raman ID/IG 0.15.",
                raman="0.15",
                application="C:Fe atomic ratio about 175",
            ),
            rec(
                "NI",
                "Ni catalyst",
                catalyst="20 nm Ni film",
                active_metals="Ni",
                result="Bamboo-like MWCNTs without metal filling; C:Ni atomic ratio about 422 and Raman ID/IG 0.23.",
                raman="0.23",
                application="C:Ni atomic ratio about 422",
            ),
        ],
        "issue": "The paper reports RBM-derived innermost diameters for individual peaks, not a run-level TEM diameter distribution; those peak assignments remain in the result summary rather than a fabricated range.",
    },
    "LIT_35CC6817563FC3B9": {
        "scope": "Direct versus 35 nm Pt-assisted growth on Ni-alloy substrate.",
            "file": "data/raw/literature/html/LIT_35CC6817563FC3B9.html",
        "common": {
            "active_metals": "Ni; Fe; Co",
            "support": "0.2 mm Ni-Cr-Fe-Co alloy",
            "metal_ratio": "Ni:Cr:Fe:Co = 57.5:15.5:6:1.5",
            "stage": "acetylene_CVD",
            "reactor": "low-pressure thermal CVD",
            "carbon": "C2H2",
            "temp": "750",
            "time": "10",
            "pressure": "1000 Pa",
            "product_type": "MWCNT",
        },
        "records": [
            rec(
                "DIRECT",
                "direct growth on anodized alloy",
                catalyst="Ni-Cr-Fe-Co alloy surface particles",
                prep="Alloy anodized in oxalic acid and ultrasonically cleaned; heated under Ar.",
                result="Random MWCNTs about 1 micrometre long and 50-70 nm in diameter; Raman ID/IG 0.73; contact resistance 7.86 ohm.",
                outer_range="50-70",
                length="about 1 micrometre",
                raman="0.73",
                application="contact resistance 7.86 ohm; turn-on 2.7 V/micrometre; threshold 4.65 V/micrometre",
            ),
            rec(
                "PT_ASSISTED",
                "35 nm Pt-assisted growth",
                catalyst="35 nm Pt-coated Ni-Cr-Fe-Co alloy",
                prep="35 nm Pt film magnetron-sputtered at 40 W before identical CVD.",
                result="Random MWCNTs about 10 micrometre long and 70-90 nm in diameter; Raman ID/IG 0.56; contact resistance 4.68 ohm.",
                outer_range="70-90",
                length="about 10 micrometre",
                raman="0.56",
                application="contact resistance 4.68 ohm; turn-on 2.0 V/micrometre; threshold 3.5 V/micrometre",
            ),
        ],
        "issue": "Pt alone did not grow CNTs under these conditions; the Pt film is treated as an assistant layer while Ni/Fe/Co from the alloy remain the active growth metals.",
    },
}


def choose_span(store: EvidenceStore, source_id: str) -> str:
    row = store.connection.execute(
        """
        SELECT span_id
        FROM candidate_experiment_span
        WHERE source_id = ?
        ORDER BY
          CASE span_type
            WHEN 'process' THEN 0
            WHEN 'yield' THEN 1
            WHEN 'catalyst' THEN 2
            ELSE 3
          END,
          length(text) DESC
        LIMIT 1
        """,
        (source_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"No candidate span for {source_id}")
    return str(row["span_id"])


def merged(
    common: dict[str, Any], item: dict[str, Any], key: str, default: str = ""
) -> str:
    return str(item.get(key, common.get(key, default)))


def evidence_text(*rows: dict[str, str], result: str) -> str:
    values = [result]
    for row in rows:
        values.extend(f"{key}={value}" for key, value in row.items() if value)
    return "; ".join(values)


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    source_id: str,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    span_id: str,
    text: str,
    file_ref: str,
) -> None:
    item = evidence_row(
        store,
        source_id,
        f"EVD_{run_id}_{suffix}",
        run_id,
        table,
        record_id,
        "record_level",
        span_id,
        f"Manual transcription supporting {table}.",
        "high",
    )
    item.update(
        {
            "evidence_type": "manual_fulltext_transcription",
            "source_locator": "local full text/PDF; source-specific values transcribed",
            "source_object_ref": file_ref,
            "evidence_text": text,
            "evidence_summary": f"Source-grounded {table} fields for {run_id}.",
            "notes": "No graph-only numeric point was inferred.",
        }
    )
    tables["evidence_index"].append(item)


def build_source(
    metadata: dict[str, Any],
    spec: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    common = spec["common"]
    span_id = choose_span(store, source_id)
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(master_row(metadata, spec["scope"]))
    tables["source_master"][0]["local_file_path"] = spec["file"]
    tables["source_master"][0]["pdf_status"] = "validated_local_fulltext"

    for item in spec["records"]:
        run_id = f"{source_id}_{item['code']}"
        result = str(item["result"])
        run = run_row(source_id, item["code"], item["label"], result)
        cat = catalyst_row(
            run_id,
            catalyst_label=merged(common, item, "catalyst", "not_reported"),
            active_metals=merged(common, item, "active_metals", "not_reported"),
            support_material=merged(common, item, "support", "not_reported"),
            promoter=merged(common, item, "promoter", "not_applicable"),
            metal_ratio_original=merged(common, item, "metal_ratio", "not_reported"),
            metal_ratio_standardized=merged(
                common, item, "metal_ratio", "not_reported"
            ),
            precursor_summary=merged(common, item, "precursor", "not_reported"),
            preparation_method=merged(
                common, item, "preparation_method", "reported_source_route"
            ),
            preparation_detail=merged(common, item, "prep", "not_reported"),
            drying_condition=merged(common, item, "drying", "not_reported"),
            calcination_condition=merged(common, item, "calcination", "not_reported"),
            reduction_condition=merged(common, item, "reduction", "not_reported"),
            phase_or_state_summary=merged(common, item, "phase", "not_reported"),
        )
        proc = process_row(
            run_id,
            1,
            merged(common, item, "stage", "CNT_growth"),
            reactor_type=merged(common, item, "reactor", "not_reported"),
            reactor_setup_summary=merged(common, item, "setup", "not_reported"),
            temperature_setpoint_C=merged(common, item, "temp"),
            temperature_range_reported_C=merged(common, item, "temp_range"),
            holding_time_min=merged(common, item, "time"),
            pressure_original=merged(common, item, "pressure", "atmospheric"),
            pressure_kPa=""
            if merged(common, item, "pressure", "atmospheric") != "atmospheric"
            else "101.325",
            carbon_source=merged(common, item, "carbon", "not_reported"),
            carbon_source_flow_original=merged(common, item, "carbon_flow"),
            reducing_gas=merged(common, item, "reducing", "not_reported"),
            reducing_gas_flow_original=merged(common, item, "reducing_flow"),
            inert_gas=merged(common, item, "inert", "not_reported"),
            inert_gas_flow_original=merged(common, item, "inert_flow"),
            cofeed_or_reactive_gas=merged(common, item, "cofeed", "not_reported"),
            cofeed_flow_original=merged(common, item, "cofeed_flow"),
            total_flow_original=merged(common, item, "total_flow"),
            gas_composition_summary=merged(common, item, "gas", "not_reported"),
        )
        product = yield_row(
            run_id,
            primary_yield_metric=(
                "reported_result"
                if item.get("yield_original")
                else "qualitative_product_outcome"
            ),
            yield_original=str(item.get("yield_original", "not numerically reported")),
            yield_definition_original="Source-reported run outcome; no cross-definition conversion.",
            yield_value_standardized="",
            yield_unit_standardized="reported_original_or_qualitative",
            secondary_result_summary=result,
            CNT_type_reported=merged(common, item, "product_type", "CNT"),
            CNT_type_confirmed=merged(common, item, "product_type", "CNT"),
            product_mixture_summary=result,
            CNT_type_evidence="Source microscopy/spectroscopy as described in the full text.",
            outer_diameter_mean_nm=merged(common, item, "outer"),
            outer_diameter_range_nm=merged(common, item, "outer_range"),
            inner_diameter_mean_nm=merged(common, item, "inner"),
            wall_number_summary=merged(common, item, "product_type", "CNT"),
            length_summary=merged(common, item, "length"),
            morphology=result,
            Raman_ratio_type="ID/IG" if item.get("raman") else "not_reported",
            Raman_ratio_value=str(item.get("raman", "")),
            Raman_laser_wavelength_nm=merged(common, item, "raman_laser"),
            characterization_methods="SEM/TEM/Raman/XRD or source-specific methods reported in full text",
            application_property_summary=merged(common, item, "application"),
        )
        cost = cost_row(
            run_id,
            scale_evidence_summary=f"Laboratory experiment: {result}",
            reactor_capacity_or_throughput=merged(
                common, item, "throughput", "not_reported"
            ),
            cost_driver_summary="Catalyst preparation, reactor heating and hydrocarbon/inert-gas use; no source-specific cost model.",
            safety_risk="Hot CVD reactor and flammable hydrocarbon/reducing gas where applicable.",
            emission_or_waste="Offgas and spent catalyst/product separation were not quantitatively assessed.",
            reproduction_value="high",
            reproduction_priority="medium",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(cat)
        tables["reactor_process_gas"].append(proc)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)

        full_text = evidence_text(run, cat, proc, product, cost, result=result)
        add_evidence(
            tables,
            store,
            source_id,
            run_id,
            "RUN",
            "source_run",
            run_id,
            span_id,
            full_text,
            spec["file"],
        )
        add_evidence(
            tables,
            store,
            source_id,
            run_id,
            "CAT",
            "catalyst_system",
            cat["catalyst_id"],
            span_id,
            full_text,
            spec["file"],
        )
        add_evidence(
            tables,
            store,
            source_id,
            run_id,
            "PROC",
            "reactor_process_gas",
            proc["process_stage_id"],
            span_id,
            full_text,
            spec["file"],
        )
        add_evidence(
            tables,
            store,
            source_id,
            run_id,
            "PROD",
            "yield_quality",
            product["product_id"],
            span_id,
            full_text,
            spec["file"],
        )
        add_evidence(
            tables,
            store,
            source_id,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            span_id,
            full_text,
            spec["file"],
        )

    first_run = f"{source_id}_{spec['records'][0]['code']}"
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_SCOPE_001",
            source_id,
            first_run,
            "source_limitation",
            "source_run",
            first_run,
            "run_summary",
            spec["issue"],
            f"EVD_{first_run}_RUN",
            "high",
        )
    )
    return tables


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
