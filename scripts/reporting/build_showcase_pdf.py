from __future__ import annotations

import csv
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "interim"
OUTPUT = ROOT / "output" / "pdf" / "CNT-PatSight_当前数据展示.pdf"
PAGE = landscape(A4)

FONT = "MicrosoftYaHei"
FONT_BOLD = "MicrosoftYaHeiBold"
NAVY = HexColor("#0B2942")
NAVY_2 = HexColor("#174967")
TEAL = HexColor("#00A6A6")
ORANGE = HexColor("#F2A65A")
INK = HexColor("#17324D")
MUTED = HexColor("#64798B")
LINE = HexColor("#C9D9E2")
PALE = HexColor("#F3F7F9")
SKY = HexColor("#DDF4F4")
WHITE = colors.white


SOURCE_META = {
    "P001": {"title": "溶胶-凝胶法Fe-Mo/MgO催化合成薄壁多壁碳纳米管", "year": "2012", "doi": "10.5714/CL.2012.13.2.099"},
    "P002": {"title": "FeMo/MgO催化甲烷CVD制备MWCNT：氢气作用与动力学", "year": "2023", "doi": "10.1038/s41598-023-48456-z"},
    "P003": {"title": "调节Fe/MgO中Mo含量实现甲烷热解CNT类型可控合成", "year": "2025", "doi": "10.1039/D4CP04231J"},
    "P004": {"title": "高性能镍基催化剂用于沼气制氢和碳纳米管联产", "year": "2022", "doi": "10.1038/s41598-022-19638-y"},
    "P005": {"title": "Ni-Mo碳化物催化沼气联产合成气与CNT", "year": "2023", "doi": "10.1038/s41598-023-38436-8"},
    "P006": {"title": "NiMo/MgO上CO2/CH4联产合成气与碳纳米管", "year": "2024", "doi": "10.1038/s41598-024-66938-6"},
}

TABLE_NAMES = {
    "source_run": "来源与运行",
    "catalyst_system": "催化剂体系",
    "reactor_process_gas": "反应器、工艺与气体程序",
    "yield_quality": "产率与产品品质",
    "cost_scale_review": "成本、规模与待补字段",
}

TABLE_SCOPE = {
    "source_run": "展示来源身份、运行划分、目标路线、催化剂键和提取状态。",
    "catalyst_system": "展示催化剂组成、配比、制备、热处理、结构表征和证据位置。",
    "reactor_process_gas": "按工艺阶段展示反应器、装填量、温度、时间、气体流量、比例和冷却条件。",
    "yield_quality": "展示原始产率口径、CNT类型、尺寸、形貌、Raman、TGA和后处理信息。",
    "cost_scale_review": "展示论文中已报告的规模事实、成本字段、H2或酸洗需求、安全排放信息及缺失项。",
}


EXACT_CN = {
    "": "未报告",
    "not_reported": "未报告",
    "not_applicable": "不适用",
    "qualitative_only": "仅定性",
    "uncertain": "不确定",
    "non_uniform_not_quantified": "不均匀，未定量",
    "yes": "是",
    "no": "否",
    "high": "高",
    "medium": "中",
    "low": "低",
    "needs_review": "待复核",
    "reviewed": "已复核",
    "formal_extract": "正式提取",
    "experimental_run": "实验运行",
    "reported": "论文报告",
    "calculated": "计算值",
    "partial_mixed": "混合产物中的部分组分",
    "acid_complexing_only": "仅酸络合",
    "acid_complexing": "酸络合",
    "none": "无",
    "none reported": "未报告",
    "none performed": "未实施",
    "randomly entangled": "随机缠结",
    "multi-walled nanotubes": "多壁碳纳米管",
    "graphite flakes": "石墨片层",
    "no carbon nanofilaments": "未检出碳纳米丝",
    "laboratory quartz-tube experiment": "实验室石英管实验",
    "CH4_CCVD_t-MWCNT": "甲烷CCVD-薄壁MWCNT",
    "CH4_CCVD_MWCNT": "甲烷CCVD-MWCNT",
    "CH4_catalytic_pyrolysis_CNT": "甲烷催化热解-CNT",
    "biogas_DRM_CDM_MWCNT": "沼气DRM/CDM-MWCNT",
}


PHRASES = [
    ("g-CNTs/g-catalysts", "g CNT/g催化剂"),
    ("g-CNTs/g-catalyst", "g CNT/g催化剂"),
    ("carbon yield based on carbon feed", "以碳进料量为基准的碳产率"),
    ("Ni:Mo=1:1 mass; total metals 30 wt%", "Ni:Mo质量比1:1；总金属30 wt%"),
    ("MWCNT-reported heterogeneous CNT/carbon product; exact wall-count distribution uncertain", "报道为MWCNT的异质CNT/碳产物；确切壁数分布不确定"),
    ("not_applicable for reported as-synthesized characterization", "报告原始合成态表征，不适用纯化条件"),
    ("not_applicable for as-prepared product", "原始制备产物，不适用纯化条件"),
    ("not_applicable", "不适用"),
    ("stable gas conversions over 3 h despite CO2-rich oxidation", "尽管存在富CO2氧化，3 h内气体转化保持稳定"),
    ("initial 6 h deactivation then nearly constant operation through 20 h", "初始6 h发生失活，随后至20 h基本稳定运行"),
    ("NM-C stable for 24 h; NM-R active about 1 h then declined", "NM-C稳定运行24 h；NM-R约1 h后活性下降"),
    ("Fe-1Mo active beyond 1 h; Fe/MgO and Fe-0.1Mo plateau within 30 min", "Fe-1Mo活性持续超过1 h；Fe/MgO和Fe-0.1Mo在30 min内进入平台"),
    ("deactivation associated with Co/Fe oxidation", "失活与Co/Fe氧化有关"),
    ("3 h temperature test", "3 h温度试验"),
    ("3 h activity test", "3 h活性试验"),
    ("stable over 3 h", "3 h内稳定"),
    ("effluent vent and water trap shown; unreacted CH4/H2 and emissions not quantified", "展示了尾气出口和水阱；未量化未反应CH4/H2及排放"),
    ("effluent gas analyzed and vented; emissions not quantified", "尾气经分析后排放；未量化排放"),
    ("unreacted gases and hydrogenation products not quantified", "未量化未反应气体和加氢产物"),
    ("high H2 feed and unreacted gases not quantified", "未量化高H2进料和未反应气体"),
    ("CH4/CO formed during hydrogenation behavior; emissions not quantified", "加氢过程中形成CH4/CO；未量化排放"),
    ("spent Ni/Mo/MgO and Mo oxide structures", "废Ni/Mo/MgO及Mo氧化物结构残留"),
    ("spent Ni/Mo/MgO remains in product", "废Ni/Mo/MgO残留于产物"),
    ("spent MgO/Ni/Mo catalyst remains in product", "废MgO/Ni/Mo催化剂残留于产物"),
    ("energy use; catalyst cost; gas consumption per kg CNT; catalyst reuse; batch reproducibility; purified-product residual metal", "能耗；催化剂成本；每kg CNT气体消耗；催化剂复用；批次重复性；纯化产品残余金属"),
    ("yield conflict", "产率冲突"),
    ("yield decreases with lower CH4 fraction", "降低CH4比例后产率下降"),
    ("carbon yield based on 碳进料量", "以碳进料量为基准的碳产率"),
    ("TGA carbon", "TGA碳含量"),
    ("catalyst cost", "催化剂成本"),
    ("gas consumption per kg CNT", "每kg CNT气体消耗"),
    ("catalyst reuse", "催化剂复用"),
    ("purified-product residual metal", "纯化产品残余金属"),
    ("residual Fe/Mo", "残余Fe/Mo"),
    ("verified lifetime", "经验证寿命"),
    ("methane conversion", "甲烷转化率"),
    ("cost impact", "成本影响"),
    ("not separately quantified for this run", "本运行未单独定量"),
    ("not separately quantified", "未单独定量"),
    ("reported separately quantified", "论文另行定量报告"),
    ("broad/weak DTG peak", "宽而弱的DTG峰"),
    ("non-homogeneous carbon", "非均相碳"),
    ("low; slight surface deposits noted by HRTEM", "低；HRTEM观察到少量表面沉积"),
    ("low by TGA/SEM description", "TGA/SEM描述为低"),
    ("present", "存在"),
    ("study-wide", "全研究范围"),
    ("TEM described", "描述了TEM"),
    ("SEM diameter analysis", "SEM直径分析"),
    ("other run-specific characterization not reported", "未报告该运行的其他专项表征"),
    ("N2 adsorption", "N2吸附"),
    ("N2 sorption", "N2吸附"),
    ("Production process", "生产过程"),
    ("Pretreatment of catalyst", "催化剂预处理"),
    ("Catalytic evaluation", "催化评价"),
    ("CNTs synthesis", "CNT合成"),
    ("H2 concentration section", "H2浓度章节"),
    ("stability section", "稳定性章节"),
    ("Durability section", "耐久性章节"),
    ("biogas composition section", "沼气组成章节"),
    ("He heating atmosphere", "He升温气氛"),
    ("He cooling atmosphere", "He冷却气氛"),
    ("He cooling", "He冷却"),
    ("pure CH4", "纯CH4"),
    ("O2 pretreatment", "O2预处理"),
    ("H2 pretreatment", "H2预处理"),
    ("CH4 pretreatment", "CH4预处理"),
    ("H2 reduction", "H2还原"),
    ("Ar only", "仅Ar"),
    ("N2 only", "仅N2"),
    ("flow not reported", "流量未报告"),
    ("[calculated]", "[计算值]"),
    ("atmospheric", "大气压"),
    ("total metals", "总金属"),
    ("qualitative_only", "仅定性"),
    ("qualitative only", "仅定性"),
    ("nitrate precursor", "硝酸盐前驱体"),
    ("not uniform, not quantified", "不均匀，未定量"),
    ("citric acid", "柠檬酸"),
    ("nitric acid", "硝酸"),
    ("NiMo=1:1 mass; total metals 30 wt%", "NiMo质量比1:1；总金属30 wt%"),
    ("NiMo=1:1 mass; 总金属 30 wt%", "NiMo质量比1:1；总金属30 wt%"),
    ("Ni:Mo=1:1 mass; 总金属 30 wt%", "Ni:Mo质量比1:1；总金属30 wt%"),
    ("H2 75 mL/min while heating to 1000 C", "升温至1000 ℃期间通入H2 75 mL/min"),
    ("H2, 75 mL/min, heated to 1000 C", "H2 75 mL/min，升温至1000 ℃"),
    ("25 mL DI water per precursor solution shown in Fig. 1", "图1所示每份前驱体溶液使用25 mL去离子水"),
    ("Ni/Co/Fe nitrates and ammonium molybdate as applicable", "按催化剂组成使用Ni/Co/Fe硝酸盐和钼酸铵"),
    ("Ni(NO3)2.6H2O; ammonium molybdate", "Ni(NO3)2·6H2O；钼酸铵"),
    ("MgO fine particles", "MgO细颗粒"),
    ("DI water", "去离子水"),
    ("as applicable", "按实际组成使用"),
    ("stir/dry at 90 ℃ to paste; oven dry at 90 ℃ for 4 h", "90 ℃搅拌干燥成糊状；90 ℃烘箱干燥4 h"),
    ("90 ℃ to paste; oven 90 ℃ for 4 h", "90 ℃浓缩成糊状；90 ℃烘箱干燥4 h"),
    ("after hydrothermal treatment", "水热处理后"),
    ("hotplate evaporation at 80 C", "80 ℃热板蒸发"),
    ("hotplate drying at 80 C", "80 ℃热板干燥"),
    ("incipient/wet impregnation by slowly adding Mo solution into Fe solution, then depositing mixed solution on MgO", "等体积/湿法浸渍：将Mo溶液缓慢加入Fe溶液，再沉积于MgO"),
    ("impregnation; slowly add Mo solution into Fe solution, deposit on MgO", "浸渍：将Mo溶液缓慢加入Fe溶液并负载于MgO"),
    ("impregnation followed by hydrothermal treatment", "浸渍后水热处理"),
    ("citrate precursor sol-gel", "柠檬酸前驱体溶胶-凝胶法"),
    ("wetness impregnation", "湿法浸渍"),
    ("impregnation", "浸渍"),
    ("citrate precursor thermally decomposed in air", "柠檬酸前驱体在空气中热分解"),
    ("citrate precursor thermally decomposed in Ar", "柠檬酸前驱体在Ar中热分解"),
    ("citrate precursor thermally decomposed in H2", "柠檬酸前驱体在H2中热分解"),
    ("duration conflict: 3 h in text vs 5 h in Fig. 1", "时间冲突：正文为3 h，图1为5 h"),
    ("3 h in text vs 5 h in Fig. 1", "正文为3 h，图1为5 h"),
    ("not applied before growth", "生长前未实施"),
    ("no separate reduction reported; heated in He before CH4", "未报告独立还原步骤；通入CH4前在He中升温"),
    ("while heating from 30 to 900", "从30升温至900"),
    ("while heating to 1000", "升温至1000期间"),
    ("fresh nanosheets", "新鲜纳米片"),
    ("separate MgMoO4/MgMo2O7/MoO3 phases observed; Fe mainly oxidized", "观察到独立MgMoO4/MgMo2O7/MoO3相；Fe主要为氧化态"),
    ("no separate Fe2O3 or MoOx phase detected; Fe-Mo nanoclusters dispersed in MgO", "未检出独立Fe2O3或MoOx相；Fe-Mo纳米簇分散于MgO"),
    ("Fe-Mo nanoclusters dispersed in MgO; Mo2C phase observed under reducing decomposition", "Fe-Mo纳米簇分散于MgO；还原分解条件下观察到Mo2C"),
    ("calcined oxide precursor; Fe3C and Mo2C reported in products from non-reduced processes", "煅烧氧化物前驱体；未预还原工艺产物中报告Fe3C和Mo2C"),
    ("non-reduced oxide precursor; carbide-phase behavior inferred from non-reduced comparison", "未预还原氧化物前驱体；由对比推断碳化物相行为"),
    ("Fe3C and Mo2C observed for non-reduced process products", "未预还原工艺产物中观察到Fe3C和Mo2C"),
    ("non-reduced oxide precursor; excess H2 during growth shifts reaction equilibrium", "未预还原氧化物前驱体；生长阶段过量H2改变反应平衡"),
    ("metallic FeMo after H2 pre-reduction; Fe3C observed after growth", "H2预还原后为金属FeMo；生长后观察到Fe3C"),
    ("metallic FeMo after pre-reduction; Fe3C observed after growth", "预还原后为金属FeMo；生长后观察到Fe3C"),
    ("metallic phases after reduction; oxide formation after reaction strongest for Co/Fe-containing catalysts", "还原后形成金属相；含Co/Fe催化剂反应后氧化最明显"),
    ("oxide Ni-Mo/MgO", "氧化态Ni-Mo/MgO"),
    ("metallic Ni-Mo/MgO", "金属态Ni-Mo/MgO"),
    ("Ni-Mo2C/MgO carbide-rich surface", "富Ni-Mo2C/MgO碳化物表面"),
    ("reduced Ni-Mo/MgO; Mo carbide/oxide phases depend on reaction condition", "还原态Ni-Mo/MgO；Mo碳化物/氧化物相随反应条件变化"),
    ("Carbon yield (%) = [(product weight - catalyst weight) / carbon feed]", "碳产率(%)=[(产物质量-催化剂质量)/碳进料量]"),
    ("C_weight-gain (%)", "碳增重(%)"),
    ("carbon weight gain relative to catalyst", "相对催化剂的碳增重"),
    ("Eq. (2)", "公式(2)"),
    ("Eq. (3)", "公式(3)"),
    ("product weight", "产物质量"),
    ("catalyst weight", "催化剂质量"),
    ("carbon feed", "碳进料量"),
    ("g-CNTs/g-catalysts = (product - catalyst)/catalyst", "g CNT/g催化剂=(产物质量-催化剂质量)/催化剂质量"),
    ("TGA-derived total deposited carbon mass per initial catalyst mass after 30 min", "由TGA得到30 min后总沉积碳质量/初始催化剂质量"),
    ("gram yield=(mproduct-mcatalyst)/(mcatalyst*time)", "克产率=(产物质量-催化剂质量)/(催化剂质量×时间)"),
    ("percent yield based on methane in feed", "百分比产率以进料甲烷为基准"),
    ("percent yield based on carbon in methane", "百分比产率以甲烷中的碳为基准"),
    ("carbon yield based on methane carbon", "碳产率以甲烷碳为基准"),
    ("carbon yield based on carbon feed", "碳产率以碳进料为基准"),
    ("Fig. 11 graph; no exact tabulated numeric value in extracted main text", "图11曲线；主文未列表给出精确数值"),
    ("CNT production observed throughout durability test", "耐久性试验期间持续观察到CNT生成"),
    ("non-uniform mixture of thick CNTs, carbon fibers and some t-MWCNTs", "粗CNT、碳纤维及少量t-MWCNT的不均匀混合物"),
    ("uniform, entangled t-MWCNTs; isolated tubes and bundles; clean surfaces", "均匀缠结t-MWCNT；存在单管和管束；表面洁净"),
    ("uniform, entangled t-MWCNTs with clean surfaces", "均匀缠结且表面洁净的t-MWCNT"),
    ("dense CNTs with some amorphous carbon; highly non-uniform diameter distribution", "致密CNT伴少量无定形碳；直径分布高度不均匀"),
    ("highly distributed CNT diameter; product mixture not fully quantified", "CNT直径分布宽；混合产物未完全定量"),
    ("dense CNTs with some amorphous carbon; broad diameter distribution", "致密CNT伴少量无定形碳；直径分布较宽"),
    ("highly distributed CNT diameter", "CNT直径分布较宽"),
    ("SWCNTs erect or lying on catalyst surface", "SWCNT竖立或平卧于催化剂表面"),
    ("dense well-aligned MWCNTs", "致密且排列较好的MWCNT"),
    ("MWCNTs with broader walls/diameters", "壁数和直径分布较宽的MWCNT"),
    ("MWCNTs including bamboo-type structures", "含竹节结构的MWCNT"),
    ("small amount of MWCNTs; severe oxidation/deactivation", "少量MWCNT；氧化/失活严重"),
    ("bamboo-like MWCNTs; irregular larger particles", "竹节状MWCNT；颗粒较大且不规则"),
    ("bamboo-like MWCNTs; smaller uniform diameter", "竹节状MWCNT；直径较小且均匀"),
    ("no carbon nanofilaments; broad catalyst/particle features", "未检出碳纳米丝；催化剂颗粒分布较宽"),
    ("MWCNTs; reduced catalyst deactivated after about 1 h", "MWCNT；还原态催化剂约1 h后失活"),
    ("smaller, narrower MWCNTs; stable carbide catalyst", "更细且分布更窄的MWCNT；碳化态催化剂稳定"),
    ("distorted/rough MWCNTs; amorphous-carbon deactivation", "弯曲/粗糙MWCNT；无定形碳导致失活"),
    ("dense distorted/rough MWCNTs; narrow distribution", "致密弯曲/粗糙MWCNT；分布较窄"),
    ("dense straight/rough MWCNTs", "致密、笔直但表面粗糙的MWCNT"),
    ("straight/smooth MWCNTs; smallest diameter", "笔直光滑MWCNT；直径最小"),
    ("straight/smooth but broad MWCNTs; Ni agglomeration", "笔直光滑但分布较宽的MWCNT；Ni团聚"),
    ("small amount of MWCNTs only at catalyst edge", "仅催化剂边缘有少量MWCNT"),
    ("CNTs extremely scarce or absent; Mo oxide rods observed", "CNT极少或未检出；观察到Mo氧化物棒"),
    ("dense entangled MWCNT network; longer tubes", "致密缠结MWCNT网络；管长较大"),
    ("none before SEM/TEM/TGA/Raman characterization", "SEM/TEM/TGA/Raman表征前未处理"),
    ("none before reported as-prepared characterization", "原样表征前未处理"),
    ("none before as-prepared characterization", "原样表征前未处理"),
    ("HCl dissolution used only for separated-CNT diameter analysis", "仅在分离CNT直径分析时使用HCl溶解"),
    ("none reported; acid leaching discussed as a general option", "未实施；仅将酸浸作为一般选项讨论"),
    ("none performed; acid leaching mentioned as possible purification", "未实施；提及酸浸可用于纯化"),
    ("Authors describe a large-scale reactor (~100 mm i.d.); actual run used 0.1 g catalyst.", "作者称反应器内径约100 mm；实际运行使用0.1 g催化剂"),
    ("Authors describe large-scale synthesis and a ~100 mm i.d. reactor; actual run used 0.1 g catalyst.", "作者称为大规模合成且反应器内径约100 mm；实际运行使用0.1 g催化剂"),
    ("0.5 g catalyst batch in quartz tube; scale-up discussed only as motivation for kinetic study", "石英管内0.5 g催化剂批次；放大仅作为动力学研究动机"),
    ("0.5 g catalyst lab batch; selected by authors for kinetic study", "0.5 g实验室批次；作者选用于动力学研究"),
    ("0.5 g catalyst lab batch; 300 min stability comparison discussed separately", "0.5 g实验室批次；另行讨论300 min稳定性对比"),
    ("0.5 g catalyst lab batch", "0.5 g实验室批次"),
    ("actual throughput", "实际处理量"),
    ("gas utilization", "气体利用率"),
    ("catalyst lifetime", "催化剂寿命"),
    ("continuous operation", "连续运行"),
    ("batch reproducibility", "批次重复性"),
    ("batch stability", "批次稳定性"),
    ("pressure drop", "压降"),
    ("pressure-drop", "压降"),
    ("reactor dimensions", "反应器尺寸"),
    ("purification mass balance", "纯化物料衡算"),
    ("residual metal", "残余金属"),
    ("energy consumption", "能耗"),
    ("energy use", "能耗"),
    ("quantified cost", "量化成本"),
    ("quantified Mo cost impact", "Mo成本影响量化"),
    ("carbon efficiency", "碳效率"),
    ("CH4 conversion", "CH4转化率"),
    ("CNT length", "CNT长度"),
    ("purification", "纯化"),
    ("scale-up", "放大"),
    ("scale up", "放大"),
    ("metal coarsening at high Mo loading", "高Mo负载下金属粗化"),
    ("carbon growth may plug reactor; Co/Fe oxidation and particle agglomeration", "碳生长可能堵塞反应器；Co/Fe氧化及颗粒团聚"),
    ("carbon coverage; reduced catalyst sintering; oxide catalyst inactivity", "碳覆盖；还原态催化剂烧结；氧化态催化剂无活性"),
    ("700 C carbon deactivation; high-temperature metal sintering; tube plugging risk noted", "700 ℃碳沉积失活；高温金属烧结；存在管路堵塞风险"),
    ("CO2-rich feed suppresses CNT and forms Mo oxides", "富CO2进料抑制CNT并形成Mo氧化物"),
    ("CNT network hinders gas diffusion; lower bed thickness/flow changed CNT diameter", "CNT网络阻碍气体扩散；较低床层厚度/流量改变CNT直径"),
    ("no formal safety analysis", "未进行正式安全分析"),
    ("unreacted gases not quantified", "未量化未反应气体"),
    ("emissions not quantified", "未量化排放"),
    ("spent MgO/metal catalyst remains in as-synthesized solid", "废MgO/金属催化剂残留于原始固体产物"),
    ("spent MgO/Ni/Mo catalyst remains in product", "废MgO/Ni/Mo催化剂残留于产物"),
    ("spent Ni/Mo/MgO remains in product", "废Ni/Mo/MgO残留于产物"),
    ("Mo present; cost impact not quantified", "含Mo；成本影响未量化"),
    ("no external H2 for this run", "本运行无需外加H2"),
    ("during growth", "生长阶段"),
    ("during pre-reduction only", "仅预还原阶段"),
    ("in pre-reduction and growth", "用于预还原和生长阶段"),
    ("H2 reduction", "H2还原"),
    ("only NM-R requires external H2 pretreatment; NM-C uses CH4", "仅NM-R需要外加H2预处理；NM-C使用CH4"),
    ("HCl dissolution used for characterization; production purification need not assessed", "表征时使用HCl溶解；未评估生产纯化需求"),
    ("not performed; acid leaching discussed as possible purification", "未实施；讨论了酸浸纯化的可能性"),
    ("not performed; acid leaching discussed", "未实施；讨论了酸浸"),
    ("not performed", "未实施"),
    ("not_reported", "未报告"),
    ("not quantified", "未量化"),
    ("not reported", "未报告"),
    ("author_claimed_large_scale", "作者声称大规模"),
    ("actual_0.1g_lab_batch", "实际0.1 g实验室批次"),
    ("actual_0.5g_lab_batch", "实际0.5 g实验室批次"),
    ("actual_0.150g_lab_batch", "实际0.150 g实验室批次"),
    ("actual_0.5g_lab_fixed_bed", "实际0.5 g实验室固定床"),
    ("actual_0.2g_lab_fixed_bed", "实际0.2 g实验室固定床"),
    ("actual_0.25g_lab_fixed_bed", "实际0.25 g实验室固定床"),
    ("kinetic_scale_up_motivation_only", "仅动力学放大研究动机"),
    ("scale_up_motivation_only", "仅放大研究动机"),
    ("heating", "升温"),
    ("pretreatment", "预处理"),
    ("reduction", "还原"),
    ("growth", "生长"),
    ("cooling", "冷却"),
    ("quartz tube reactor in tube furnace", "管式炉内石英管反应器"),
    ("quartz tube reactor in furnace", "炉内石英管反应器"),
    ("fixed-bed horizontal quartz tube", "卧式石英管固定床"),
    ("horizontal quartz tube reactor", "卧式石英管反应器"),
    ("horizontal quartz tube", "卧式石英管"),
    ("lab_batch_large_diameter_tube", "实验室批次大直径管"),
    ("lab_batch_0.5g_tube_reactor", "0.5 g实验室管式反应器"),
    ("lab_fixed_bed", "实验室固定床"),
    ("lab_batch", "实验室批次"),
    ("laboratory_fixed_bed", "实验室固定床"),
    ("CH4_CO2_biogas", "CH4-CO2沼气"),
    ("cooled to room temperature in Ar", "在Ar中冷却至室温"),
    ("cooled to room temperature in N2", "在N2中冷却至室温"),
    ("cooled to room temperature in He", "在He中冷却至室温"),
    ("cooled to room temperature under He 50 mL/min", "在50 mL/min He下冷却至室温"),
    ("cooled under He 50 mL/min", "在50 mL/min He下冷却"),
    ("cooled to room temperature under He", "在He下冷却至室温"),
    ("ambient", "室温"),
    ("no_CNT_or_trace", "未检出或仅痕量CNT"),
    ("no_CNT_graphite", "未检出CNT，仅石墨"),
    ("no_CNT", "未检出CNT"),
    ("MWCNT-containing sparse product", "含少量MWCNT的稀疏产物"),
    ("mixed SWCNT/DWCNT", "SWCNT/DWCNT混合物"),
    ("mixed t-MWCNT/MWCNT/carbon fiber", "t-MWCNT/MWCNT/碳纤维混合物"),
    ("graphene walls", "层石墨烯壁"),
    ("section", "节"),
    ("Experimental", "实验部分"),
    ("Results", "结果"),
    ("caption", "图注"),
    ("Table", "表"),
    ("Fig.", "图"),
    ("Figs.", "图"),
    ("throughput", "处理量"),
    ("lifetime", "寿命"),
    ("pressure", "压力"),
    ("catalyst", "催化剂"),
    ("Actual", "实际"),
    ("were 未报告", "均未报告"),
    (" and ", "和"),
]


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont(FONT, r"C:\Windows\Fonts\msyh.ttc"))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\msyhbd.ttc"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _reported(value: str | None) -> bool:
    return bool(value and value not in {"not_reported", "not_applicable", "not_assessed"})


def _join_reported(*values: str | None) -> str:
    return "; ".join(str(value) for value in values if _reported(value))


def _evidence_for(evidence_rows, table_name, record_id):
    row = next(
        (
            item
            for item in evidence_rows
            if item.get("target_table") == table_name
            and item.get("target_record_id") == record_id
        ),
        None,
    )
    if not row:
        return "not_reported", "not_reported"
    return row.get("source_locator", "not_reported"), row.get("confidence", "not_reported")


def _legacy_views(directory: Path) -> dict[str, list[dict[str, str]]]:
    """Adapt the normalized v0.4 tables to the existing five-section PDF layout."""
    source_master = read_csv(directory / "source_master.csv")
    source_runs = read_csv(directory / "source_run.csv")
    catalysts = read_csv(directory / "catalyst_system.csv")
    processes = read_csv(directory / "reactor_process_gas.csv")
    products = read_csv(directory / "yield_quality.csv")
    costs = read_csv(directory / "cost_scale_review.csv")
    evidence = read_csv(directory / "evidence_index.csv")
    catalyst_by_run = {row["run_id"]: row for row in catalysts}

    source_run_view = []
    for row in source_runs:
        catalyst = catalyst_by_run.get(row["run_id"], {})
        source_run_view.append(
            {
                **row,
                "catalyst_key": _join_reported(
                    catalyst.get("active_metals"), catalyst.get("support_material")
                )
                or "not_reported",
            }
        )

    catalyst_view = []
    for row in catalysts:
        location, confidence = _evidence_for(evidence, "catalyst_system", row["catalyst_id"])
        size = _join_reported(
            row.get("catalyst_particle_size_mean_nm"),
            row.get("catalyst_particle_size_range_nm"),
            row.get("catalyst_particle_size_qualifier"),
        )
        catalyst_view.append(
            {
                **row,
                "acid_treatment_flag": row.get("preparation_modifier", "not_reported"),
                "acid_treatment_type": row.get("preparation_modifier", "not_reported"),
                "complexing_agent": row.get("preparation_detail", "not_reported"),
                "precursor_summary": row.get("precursor_summary", "not_reported"),
                "preparation_method": row.get("preparation_method", "not_reported"),
                "catalyst_particle_size_nm": size or "not_reported",
                "evidence_location": location,
                "confidence": confidence,
            }
        )

    process_view = []
    for row in processes:
        location, confidence = _evidence_for(
            evidence, "reactor_process_gas", row["process_stage_id"]
        )
        inert = row.get("inert_gas", "")
        process_view.append(
            {
                **row,
                "start_temperature_C": "not_reported",
                "temperature_actual_C": "not_reported",
                "CH4_flow_original": row.get("carbon_source_flow_original", "not_reported")
                if row.get("carbon_source") == "CH4"
                else "not_reported",
                "H2_flow_original": row.get("reducing_gas_flow_original", "not_reported")
                if row.get("reducing_gas") == "H2"
                else "not_reported",
                "N2_flow_original": row.get("inert_gas_flow_original", "not_reported")
                if "N2" in inert
                else "not_reported",
                "Ar_flow_original": row.get("inert_gas_flow_original", "not_reported")
                if "Ar" in inert
                else "not_reported",
                "other_gas_flow_original": _join_reported(
                    row.get("cofeed_or_reactive_gas"), row.get("cofeed_flow_original")
                )
                or "not_reported",
                "gas_ratio_summary": row.get("gas_composition_summary", "not_reported"),
                "evidence_location": location,
                "confidence": confidence,
            }
        )

    product_view = []
    for row in products:
        location, confidence = _evidence_for(evidence, "yield_quality", row["product_id"])
        mixed = _reported(row.get("product_mixture_summary"))
        confirmed = row.get("CNT_type_confirmed", "")

        def flag(label):
            if label.lower() in confirmed.lower():
                return "partial_mixed" if mixed else "yes"
            return "no"

        ratio_type = row.get("Raman_ratio_type")
        ratio_value = row.get("Raman_ratio_value", "not_reported")
        product_view.append(
            {
                **row,
                "methane_conversion_percent": row.get(
                    "carbon_source_conversion_percent", "not_reported"
                ),
                "carbon_efficiency_percent": "not_reported",
                "is_SWCNT": flag("SWCNT"),
                "is_DWCNT": flag("DWCNT"),
                "is_t_MWCNT": flag("t-MWCNT"),
                "is_MWCNT": flag("MWCNT"),
                "inner_diameter_or_wall_number": row.get(
                    "wall_number_summary", "not_reported"
                ),
                "wall_number_mean": "not_reported",
                "Raman_ID_IG": ratio_value if ratio_type == "ID/IG" else "not_reported",
                "Raman_IG_ID": ratio_value if ratio_type == "IG/ID" else "not_reported",
                "purity_wt_percent": row.get(
                    "TGA_carbon_content_wt_percent", "not_reported"
                ),
                "ash_content_wt_percent": "not_reported",
                "metal_residue_wt_percent": row.get("residue_summary", "not_reported"),
                "evidence_location": location,
                "confidence": confidence,
            }
        )

    cost_view = []
    for row in costs:
        location, confidence = _evidence_for(evidence, "cost_scale_review", row["run_id"])
        cost_view.append(
            {
                **row,
                "scale_signal_reported": row.get("scale_evidence_summary", "not_reported"),
                "catalyst_cost_signal": row.get("cost_driver_summary", "not_reported"),
                "purification_cost_signal": "not_reported",
                "needs_H2": "see process table",
                "needs_acid_washing": "see catalyst/product tables",
                "contains_expensive_metal": "see catalyst table",
                "missing_critical_fields": row.get("review_note", "not_reported"),
                "evidence_location": location,
                "confidence": confidence,
            }
        )

    return {
        "source_master": source_master,
        "source_run": source_run_view,
        "catalyst_system": catalyst_view,
        "reactor_process_gas": process_view,
        "yield_quality": product_view,
        "cost_scale_review": cost_view,
    }


def load_sources() -> list[dict]:
    sources = []
    for directory in sorted(DATA_ROOT.glob("P00[1-6]_*")):
        if not directory.is_dir():
            continue
        code = directory.name[:4]
        sources.append({"code": code, "directory": directory, **_legacy_views(directory)})
    return sources


def cn(value) -> str:
    if value is None:
        return "未报告"
    text = str(value).strip()
    if text in EXACT_CN:
        return EXACT_CN[text]
    text = text.replace("｡紊", "℃").replace("°C", "℃")
    text = text.replace(" ｡ﾁ ", " × ").replace("｡ﾁ", "×")
    for old, new in PHRASES:
        text = text.replace(old, new)
    text = re.sub(r"\bnone before\b", "此前无处理", text, flags=re.I)
    text = re.sub(r"\bnone\b", "无", text, flags=re.I)
    text = re.sub(r"\byes\b", "是", text, flags=re.I)
    text = re.sub(r"\bno\b", "否", text, flags=re.I)
    return text or "未报告"


def cn_label(value: str) -> str:
    text = cn(value)
    replacements = {
        "air-decomposed citrate precursor": "空气分解柠檬酸前驱体",
        "Ar-decomposed citrate precursor": "Ar分解柠檬酸前驱体",
        "H2-decomposed citrate precursor": "H2分解柠檬酸前驱体",
        "non-pre-reduced": "未预还原",
        "pre-reduced": "预还原",
        "no H2 co-feed": "无H2共进料",
        "H2 co-feed": "H2共进料",
        "oxide": "氧化态",
        "reduced": "还原态",
        "carbide": "碳化态",
        "durability": "耐久性",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def compact(values: list[str], sep="；") -> str:
    cleaned = [cn(v) for v in values if v is not None and str(v).strip()]
    return sep.join(cleaned) if cleaned else "未报告"


def styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle("cover_title", parent=base["Title"], fontName=FONT_BOLD, fontSize=25, leading=34, textColor=WHITE, alignment=TA_LEFT),
        "cover_sub": ParagraphStyle("cover_sub", parent=base["BodyText"], fontName=FONT, fontSize=12, leading=19, textColor=HexColor("#C4E8EB")),
        "cover_table": ParagraphStyle("cover_table", parent=base["BodyText"], fontName=FONT, fontSize=8, leading=11, textColor=WHITE),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=FONT_BOLD, fontSize=17, leading=22, textColor=NAVY, spaceAfter=3),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=FONT_BOLD, fontSize=9.5, leading=13, textColor=NAVY, spaceBefore=4, spaceAfter=4),
        "lead": ParagraphStyle("lead", parent=base["BodyText"], fontName=FONT, fontSize=8.5, leading=13, textColor=MUTED, spaceAfter=5),
        "meta": ParagraphStyle("meta", parent=base["BodyText"], fontName=FONT, fontSize=7.3, leading=10, textColor=INK),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=FONT, fontSize=7.2, leading=9.7, textColor=INK),
        "body_small": ParagraphStyle("body_small", parent=base["BodyText"], fontName=FONT, fontSize=5.7, leading=7.3, textColor=INK),
        "head": ParagraphStyle("head", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=6.2, leading=7.8, textColor=WHITE, alignment=TA_CENTER),
        "foot": ParagraphStyle("foot", parent=base["BodyText"], fontName=FONT, fontSize=6.7, leading=9, textColor=MUTED),
    }


def p(text, style):
    return Paragraph(str(text), style)


class AccentRule(Flowable):
    def __init__(self):
        super().__init__()
        self.width = 46 * mm
        self.height = 2.2 * mm

    def draw(self):
        self.canv.setFillColor(TEAL)
        self.canv.roundRect(0, 0, 34 * mm, 1.7 * mm, 0.8 * mm, fill=1, stroke=0)
        self.canv.setFillColor(ORANGE)
        self.canv.roundRect(36 * mm, 0, 10 * mm, 1.7 * mm, 0.8 * mm, fill=1, stroke=0)


def make_table(rows, widths, s, small=False):
    body_style = s["body_small"] if small else s["body"]
    wrapped = []
    for i, row in enumerate(rows):
        style = s["head"] if i == 0 else body_style
        wrapped.append([cell if isinstance(cell, Flowable) else p(cell, style) for cell in row])
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.6),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
    ]
    for i in range(2, len(rows), 2):
        commands.append(("BACKGROUND", (0, i), (-1, i), PALE))
    return Table(wrapped, colWidths=widths, repeatRows=1, hAlign="LEFT", style=TableStyle(commands))


def meta_band(code: str, s: dict):
    meta = SOURCE_META[code]
    return Table([[
        p(f"<b>论文编号</b><br/>{code}", s["meta"]),
        p(f"<b>年份</b><br/>{meta['year']}", s["meta"]),
        p(f"<b>中文题名</b><br/>{meta['title']}", s["meta"]),
        p(f"<b>DOI</b><br/>{meta['doi']}", s["meta"]),
        p("<b>提取状态</b><br/>待复核", s["meta"]),
    ]], colWidths=[20 * mm, 18 * mm, 115 * mm, 70 * mm, 35 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SKY),
        ("BOX", (0, 0), (-1, -1), 0.5, TEAL),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))


def section_header(code: str, key: str, s: dict):
    return [
        p(f"{code}  {TABLE_NAMES[key]}", s["h1"]),
        p(TABLE_SCOPE[key], s["lead"]),
        AccentRule(),
        Spacer(1, 2.5 * mm),
        meta_band(code, s),
        Spacer(1, 3 * mm),
    ]


def source_run_story(source, s):
    rows = [["运行ID", "运行标签", "数据类型", "目标路线", "催化剂键", "相关性", "提取状态", "置信度"]]
    for r in source["source_run"]:
        rows.append([
            r["run_id"], cn_label(r["run_label"]), cn(r["data_type"]), cn(r["target_track"]), r["catalyst_key"],
            cn(r["relevance_class"]), cn(r["extraction_status"]), cn(r["extraction_confidence"]),
        ])
    return section_header(source["code"], "source_run", s) + [
        make_table(rows, [38 * mm, 56 * mm, 25 * mm, 43 * mm, 43 * mm, 23 * mm, 24 * mm, 20 * mm], s),
        Spacer(1, 3 * mm),
        p("字段说明：组合键和运行摘要保留在原始CSV中；本展示页聚焦运行身份和分类字段。", s["foot"]),
    ]


def catalyst_story(source, s):
    rows = [["运行ID", "催化剂", "组成", "配比/前驱体", "制备/络合/干燥", "煅烧与还原", "结构与物相", "证据"]]
    for r in source["catalyst_system"]:
        pore = compact([
            f"BET {r['BET_surface_area_m2_g']} m²/g" if r.get("BET_surface_area_m2_g") else "",
            f"孔径 {r['pore_diameter_nm']} nm" if r.get("pore_diameter_nm") else "",
            f"孔容 {r['pore_volume_cm3_g']} cm³/g" if r.get("pore_volume_cm3_g") else "",
        ])
        acid = compact([r.get("acid_treatment_flag"), r.get("acid_treatment_type"), r.get("complexing_agent")])
        rows.append([
            r["run_id"],
            cn_label(r["catalyst_label"]),
            compact([f"活性金属 {r['active_metals']}", f"载体 {r['support_material']}", f"助剂 {r['promoter']}" if r.get("promoter") else ""]),
            compact([r.get("metal_ratio_original"), r.get("precursor_summary")]),
            compact([r.get("preparation_method"), acid, r.get("drying_condition")]),
            compact([r.get("calcination_condition"), r.get("reduction_condition")]),
            compact([f"颗粒 {r['catalyst_particle_size_nm']}" if r.get("catalyst_particle_size_nm") else "", pore, r.get("phase_or_state_summary")]),
            f"{cn(r['evidence_location'])}；{cn(r['confidence'])}",
        ])
    return section_header(source["code"], "catalyst_system", s) + [
        make_table(rows, [25 * mm, 26 * mm, 32 * mm, 38 * mm, 38 * mm, 45 * mm, 48 * mm, 20 * mm], s, small=True),
    ]


def process_story(source, s):
    rows = [["运行ID", "阶段", "反应器/规模", "装填量", "温度/时间/升温", "气体流量", "比例/压力", "冷却/证据"]]
    for r in source["reactor_process_gas"]:
        temp = compact([
            f"起始 {r['start_temperature_C']} ℃" if r.get("start_temperature_C") else "",
            f"设定 {r['temperature_setpoint_C']} ℃" if r.get("temperature_setpoint_C") else "",
            f"实际 {r['temperature_actual_C']} ℃" if r.get("temperature_actual_C") else "",
            r.get("temperature_range_reported_C", ""),
        ])
        time = f"{r['holding_time_min']} min" if r.get("holding_time_min") else "未报告"
        scale = compact([r.get("reactor_type"), r.get("scale_level")])
        stage = f"第{r.get('stage_order', '')}阶段<br/>{cn(r.get('stage_type', ''))}"
        flows = compact([
            f"CH4 {r['CH4_flow_original']}" if r.get("CH4_flow_original") else "",
            f"H2 {r['H2_flow_original']}" if r.get("H2_flow_original") else "",
            f"N2 {r['N2_flow_original']}" if r.get("N2_flow_original") else "",
            f"Ar {r['Ar_flow_original']}" if r.get("Ar_flow_original") else "",
            f"其他 {r['other_gas_flow_original']}" if r.get("other_gas_flow_original") else "",
        ])
        gas = compact([f"碳源 {r['carbon_source']}" if r.get("carbon_source") else "", flows, f"总流量 {r['total_flow_original']}" if r.get("total_flow_original") else ""])
        rows.append([
            r["run_id"], stage, scale, cn(r["catalyst_loading_mass_g"]),
            compact([temp, time, f"升温 {r['heating_rate_C_min']} ℃/min" if r.get("heating_rate_C_min") else ""]),
            gas,
            compact([r.get("gas_ratio_summary"), r.get("pressure_original"), f"{r['pressure_kPa']} kPa" if r.get("pressure_kPa") else ""]),
            compact([r.get("cooling_condition"), r.get("evidence_location")]),
        ])
    return section_header(source["code"], "reactor_process_gas", s) + [
        make_table(rows, [25 * mm, 23 * mm, 35 * mm, 22 * mm, 38 * mm, 65 * mm, 35 * mm, 29 * mm], s, small=True),
    ]


def cn_yield(value: str) -> str:
    text = cn(value)
    replacements = {
        "approximately": "约",
        "carbon weight gain": "碳增重",
        "carbon yield based on carbon feed": "按碳进料计的碳产率",
        "carbon yield": "碳产率",
        "g carbon/g catalyst": "g碳/g催化剂",
        "g-CNTs/g-catalysts": "g CNT/g催化剂",
        "gCNT/gCat": "g CNT/g催化剂",
        "gProduct/gCat-h": "g产物/(g催化剂·h)",
        "in Table 3": "表3",
        "in Table 4": "表4",
        "for same": "同一",
        "condition": "条件",
        "in both tables": "两表均为",
        "read from": "读取自",
        "no CNT yield detected": "未检出CNT产率",
        "qualitative only; yield decreases with lower CH4 fraction": "仅定性：降低CH4比例后产率下降",
        "qualitative continuous CNT growth; exact 20 h yield not tabulated": "持续观察到CNT生长；20 h精确产率未列表",
        "qualitative continuous CNT 生长; exact 20 h yield not tabulated": "持续观察到CNT生长；20 h精确产率未列表",
        "C_weight-gain (%)": "碳增重(%)",
        "Eq. (2)": "公式(2)",
        "Eq. (3)": "公式(3)",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def yield_story(source, s):
    rows = [["运行ID", "原始产率", "定义/标准化", "CNT类型/标志", "尺寸", "形貌", "Raman/TGA", "表征/后处理/证据"]]
    for r in source["yield_quality"]:
        standardized = compact([r.get("yield_value_standardized"), r.get("yield_unit_standardized")])
        conversion = compact([
            f"CH4转化 {r['methane_conversion_percent']}%" if r.get("methane_conversion_percent") else "",
            f"碳效率 {r['carbon_efficiency_percent']}%" if r.get("carbon_efficiency_percent") else "",
            f"CNT/催化剂 {r['CNT_yield_per_catalyst_g_gcat']} g/g" if r.get("CNT_yield_per_catalyst_g_gcat") else "",
            f"生产率 {r['CNT_productivity_g_gcat_h']} g/(g·h)" if r.get("CNT_productivity_g_gcat_h") else "",
        ])
        flags = compact([
            f"SWCNT:{cn(r.get('is_SWCNT'))}", f"DWCNT:{cn(r.get('is_DWCNT'))}",
            f"t-MWCNT:{cn(r.get('is_t_MWCNT'))}", f"MWCNT:{cn(r.get('is_MWCNT'))}",
        ])
        dimensions = compact([
            f"外径均值 {r['outer_diameter_mean_nm']} nm" if r.get("outer_diameter_mean_nm") else "",
            f"外径范围 {r['outer_diameter_range_nm']} nm" if r.get("outer_diameter_range_nm") else "",
            f"内径均值 {r['inner_diameter_mean_nm']} nm" if r.get("inner_diameter_mean_nm") else "",
            r.get("inner_diameter_or_wall_number", ""),
            f"平均壁数 {r['wall_number_mean']}" if r.get("wall_number_mean") else "",
        ])
        raman = compact([
            f"ID/IG={r['Raman_ID_IG']}" if r.get("Raman_ID_IG") else "",
            f"IG/ID={r['Raman_IG_ID']}" if r.get("Raman_IG_ID") else "",
            f"激光 {r['Raman_laser_wavelength_nm']} nm" if r.get("Raman_laser_wavelength_nm") else "",
        ])
        tga = compact([
            f"TGA碳含量 {r['purity_wt_percent']}%" if r.get("purity_wt_percent") else "",
            f"灰分 {r['ash_content_wt_percent']}%" if r.get("ash_content_wt_percent") else "",
            f"金属残余 {r['metal_residue_wt_percent']}%" if r.get("metal_residue_wt_percent") else "",
            f"无定形碳 {cn(r['amorphous_carbon_level'])}" if r.get("amorphous_carbon_level") else "",
        ])
        rows.append([
            r["run_id"],
            cn_yield(r["yield_original"]),
            compact([r.get("yield_definition_original"), standardized, conversion]),
            compact([r.get("CNT_type_confirmed"), flags]),
            dimensions,
            cn(r["morphology"]),
            compact([raman, tga]),
            compact([r.get("characterization_methods"), r.get("post_treatment_or_purification"), r.get("purification_condition"), r.get("evidence_location")]),
        ])
    return section_header(source["code"], "yield_quality", s) + [
        make_table(rows, [25 * mm, 44 * mm, 33 * mm, 35 * mm, 30 * mm, 35 * mm, 32 * mm, 38 * mm], s, small=True),
        Spacer(1, 2 * mm),
        p("说明：TGA字段表示未纯化产物的碳含量，不等同于应用级纯度。", s["foot"]),
    ]


def cost_story(source, s):
    rows = [["运行ID", "成本/规模事实", "连续运行/复用", "H2/酸洗/金属", "声称规模/放大问题", "安全/排放", "缺失关键字段"]]
    for r in source["cost_scale_review"]:
        operations = compact([
            f"连续 {r['continuous_operation_time_h']} h" if r.get("continuous_operation_time_h") else "",
            f"复用 {r['catalyst_reuse_cycles']} 次" if r.get("catalyst_reuse_cycles") else "",
            r.get("batch_stability", ""),
        ])
        cost_signal = compact([r.get("catalyst_cost_signal"), r.get("purification_cost_signal")])
        rows.append([
            r["run_id"],
            compact([f"量化成本 {r['quantitative_cost_reported']}", r.get("scale_signal_reported"), cost_signal]),
            operations,
            compact([f"H2 {r['needs_H2']}", f"酸洗 {r['needs_acid_washing']}", r.get("contains_expensive_metal")]),
            compact([r.get("scale_level_claimed"), r.get("scale_up_issue")]),
            compact([r.get("safety_risk"), r.get("emission_or_waste")]),
            cn(r["missing_critical_fields"]),
        ])
    return section_header(source["code"], "cost_scale_review", s) + [
        make_table(rows, [25 * mm, 45 * mm, 30 * mm, 42 * mm, 55 * mm, 42 * mm, 33 * mm], s, small=True),
        Spacer(1, 2 * mm),
        p("说明：工业评分、复现实验优先级和推荐动作在首轮提取中保持空值，因此不在展示表中填入。", s["foot"]),
    ]


def cover_story(sources, s):
    rows = [[p("编号", s["head"]), p("年份", s["head"]), p("中文题名", s["head"]), p("DOI", s["head"]), p("展示内容", s["head"])]]
    for source in sources:
        code = source["code"]
        meta = SOURCE_META[code]
        rows.append([
            p(code, s["cover_table"]), p(meta["year"], s["cover_table"]), p(meta["title"], s["cover_table"]),
            p(meta["doi"], s["cover_table"]), p("5个运行事实主题", s["cover_table"]),
        ])
    table = Table(rows, colWidths=[22 * mm, 20 * mm, 122 * mm, 70 * mm, 35 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("BACKGROUND", (0, 1), (-1, -1), NAVY_2),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#43728A")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [
        Spacer(1, 25 * mm),
        p("CNT-PatSight<br/>论文运行数据展示", s["cover_title"]),
        Spacer(1, 6 * mm),
        p("按论文逐篇展示来源与运行、催化剂体系、反应工艺与气体程序、产率品质、成本规模五个主题；数据来自八表原始数据库。", s["cover_sub"]),
        Spacer(1, 14 * mm),
        table,
        Spacer(1, 10 * mm),
        p("全部记录为首轮提取数据，状态为待复核。本PDF不包含分析、排名或统计结论。", s["cover_sub"]),
        NextPageTemplate("content"),
        PageBreak(),
    ]


def build_story(sources, s):
    story = cover_story(sources, s)
    builders = [source_run_story, catalyst_story, process_story, yield_story, cost_story]
    first = True
    for source in sources:
        for builder in builders:
            if not first:
                story.append(PageBreak())
            story.extend(builder(source, s))
            first = False
    return story


def cover_page(canvas, doc):
    w, h = PAGE
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(NAVY_2)
    canvas.circle(w - 22 * mm, h - 10 * mm, 48 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(HexColor("#1F6680"))
    for radius in (16, 27, 39):
        canvas.circle(w - 25 * mm, 22 * mm, radius * mm, fill=0, stroke=1)
    canvas.setFillColor(TEAL)
    canvas.roundRect(14 * mm, h - 18 * mm, 20 * mm, 3.5 * mm, 1.7 * mm, fill=1, stroke=0)
    canvas.setFont(FONT_BOLD, 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(39 * mm, h - 17 * mm, "CNT-PatSight")
    canvas.restoreState()


def content_page(canvas, doc):
    w, h = PAGE
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(12 * mm, h - 10 * mm, w - 12 * mm, h - 10 * mm)
    canvas.setFont(FONT_BOLD, 7)
    canvas.setFillColor(NAVY)
    canvas.drawString(12 * mm, h - 7.5 * mm, "CNT-PatSight  论文运行数据展示")
    canvas.setFont(FONT, 6.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(w - 12 * mm, h - 7.5 * mm, "首轮提取数据 - 待人工复核")
    canvas.line(12 * mm, 9 * mm, w - 12 * mm, 9 * mm)
    canvas.drawString(12 * mm, 5.5 * mm, "仅展示运行事实与数据，不包含分析统计")
    canvas.drawRightString(w - 12 * mm, 5.5 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def build_pdf() -> Path:
    register_fonts()
    sources = load_sources()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    s = styles()
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=PAGE,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=13 * mm,
        bottomMargin=12 * mm,
        title="CNT-PatSight论文运行数据展示",
        author="CNT-PatSight",
        subject="逐篇展示八表数据库中的运行事实与数据",
    )
    cover_frame = Frame(12 * mm, 12 * mm, PAGE[0] - 24 * mm, PAGE[1] - 24 * mm, id="cover_frame", showBoundary=0)
    content_frame = Frame(12 * mm, 11 * mm, PAGE[0] - 24 * mm, PAGE[1] - 23 * mm, id="content_frame", showBoundary=0)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=cover_page),
        PageTemplate(id="content", frames=[content_frame], onPage=content_page),
    ])
    doc.build(build_story(sources, s))
    return OUTPUT


if __name__ == "__main__":
    print(build_pdf())
