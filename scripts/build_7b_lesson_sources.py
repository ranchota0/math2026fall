"""Create structured Grade 7B lesson sources and topic diagrams.

The manifest remains the curriculum authority.  This script turns every locked
lesson into a concrete, editable lesson source used by Word and PowerPoint
builders.  It intentionally skips C07-L01, which is the reviewed gold-comparison
sample and already has a hand-tuned source.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "curriculum_manifest_7b.yml"
FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")


# Each entry supplies a self-contained worked example and a self-contained exit
# ticket.  Numeric answers were independently recomputed while authoring this
# bank; open tasks include an explicit reference criterion.
PROBLEMS: dict[str, tuple[str, str, str, str]] = {
    "C07-L02": ("点A在直线l外，说明用直尺和三角尺过A画l的垂线的步骤，并标出垂足H。", "一边贴合l，沿直尺平移三角尺直到另一条直角边经过A，沿该边画直线AH；AH⊥l，H为垂足。", "若直线AB、CD相交且∠AOC=90°，写出一组垂直关系并说明其余三个角。", "AB⊥CD；其余三个角也都是90°。"),
    "C07-L03": ("点P到直线l的垂线段PA长5 cm，另有斜线段PB长6 cm、PC长7 cm。点P到l的距离是多少？", "5 cm；点到直线的距离是垂线段的长度。", "河岸l外一点P修一条到河岸的最短道路，应沿什么方向修？", "过P向河岸l作垂线，沿垂线段修，依据是垂线段最短。"),
    "C07-L04": ("直线a、b被截线c所截，∠1和∠5位于a、b同侧且在c同旁，∠3和∠5位于a、b之间且在c两侧。分别判断角的类型。", "∠1与∠5是同位角；∠3与∠5是内错角。", "识别同旁内角时，应同时检查哪三个位置条件？", "两角在两条被截线之间、在截线同侧，并由同一条截线形成。"),
    "C07-L05": ("过直线l外一点P画l的平行线。能画几条？写出依据。", "只能画一条；经过直线外一点，有且只有一条直线与已知直线平行。", "若a∥b，b∥c，可得到什么结论？", "a∥c；平行于同一条直线的两条直线平行。"),
    "C07-L06": ("直线a、b被c所截，一对同位角均为65°。能否判定a∥b？", "能；同位角相等，两直线平行。", "一对同旁内角分别为112°和68°，能否判定两直线平行？", "能；112°+68°=180°，同旁内角互补，两直线平行。"),
    "C07-L07": ("已知a∥b，一对同位角中一个为65°，求与它对应的内错角和同旁内角。", "内错角为65°，同旁内角为115°。", "为什么“同位角相等”在本课是结论，而在上一课可作为条件？", "本课由两直线平行推出角相等，是性质；上一课由角相等推出两直线平行，是判定。"),
    "C07-L08": ("已知∠1=∠2，可判定a∥b；又知∠3=72°且∠3与∠4是同旁内角，求∠4。", "先由同位角相等判定a∥b，再用平行线同旁内角互补，∠4=108°。", "完成几何推理时，怎样判断应该用“判定”还是“性质”？", "已知角关系、要证平行用判定；已知平行、要求角关系用性质。"),
    "C07-L09": ("把命题“对顶角相等”改写成“如果……那么……”并指出题设、结论。", "如果两个角是对顶角，那么这两个角相等。题设：两个角是对顶角；结论：两个角相等。", "判断“相等的角是对顶角”的真假，并说明方法。", "是假命题；可画同一顶点处两个相等但不相对的角作为反例。"),
    "C07-L10": ("三角形ABC向右平移4格、向上平移2格得到A'B'C'。说明AA'、BB'、CC'的关系。", "三条线段平行且相等，方向均向右上，长度等于同一次平移的距离。", "平移后图形的形状、大小和方向是否改变？", "形状和大小不变，对应线段平行且相等；图形方向不改变，只改变位置。"),
    "C07-L11": ("选一个小三角形作为基本图形，设计连续平移图案，并用“方向、距离、次数”说明生成过程。", "示例：每次向右平移3 cm，连续平移5次；各基本图形全等，对应边平行且相等。", "评价一幅平移图案是否合格，至少检查哪三项？", "基本图形明确；每次平移方向和距离明确；图案能由连续平移得到且说明完整。"),
    "C07-L12": ("小组用直尺和三角尺画三条互相平行的直线，比较不同画法并记录依据。", "保持三角尺一边贴住直尺，沿直尺平移后多次画线；各线同垂直于或同平行于同一方向，因此互相平行。", "活动报告应包含哪些证据，才能说明画出的直线确实平行？", "操作步骤、角或垂直关系的测量记录、使用的平行线判定依据及误差说明。"),
    "C07-L13": ("已知a∥b，截线c形成一个68°角，求同位角、内错角和同旁内角。", "同位角68°，内错角68°，同旁内角112°。", "用一句话概括本章“位置关系—角关系—图形变换”的主线。", "由相交研究角，由角关系判定或运用平行，再用平移保持图形的形状和大小。"),
    "C08-L01": ("求49的平方根，并解方程x²=81。", "49的平方根是±7；x=±9。", "0和−9是否有平方根？", "0的平方根是0；−9在实数范围内没有平方根。"),
    "C08-L02": ("计算√64、√0.81，并说明结果为什么不能取负值。", "√64=8，√0.81=0.9；算术平方根规定为非负数。", "若√a=5，求a；若a<0，√a在实数范围内是否有意义？", "a=25；a<0时√a在实数范围内没有意义。"),
    "C08-L03": ("不使用计算器，说明√20在哪两个相邻整数之间；再取到0.1。", "4²<20<5²，所以4<√20<5；√20≈4.5（精确值约4.472）。", "正方形面积为50 cm²，边长在哪两个相邻整数之间？", "边长为√50 cm；7²<50<8²，所以在7 cm与8 cm之间。"),
    "C08-L04": ("计算∛125、∛(−64)、∛0。", "分别为5、−4、0。", "若x³=−216，求x。", "x=−6，因为(−6)³=−216。"),
    "C08-L05": ("把√2、π、0.3、22/7、−√9分类为有理数和无理数。", "无理数：√2、π；有理数：0.3、22/7、−√9=−3。", "数轴上的每一个点都对应什么数？每一个实数是否都能在数轴上找到点？", "每个点对应一个实数；每个实数也都能在数轴上找到唯一对应点。"),
    "C08-L06": ("化简|√5−3|，并比较√10与3的大小。", "√5<3，所以|√5−3|=3−√5；10>9，所以√10>3。", "计算(√3+1)−(√3−2)。", "结果为3；按实数运算法则合并同类项。"),
    "C08-L07": ("尝试用“假设√2=m/n（最简分数）”的思路说明会出现什么矛盾。", "由m²=2n²可得m为偶数，进一步得n也为偶数，与m/n最简矛盾，因此√2不是有理数。", "本活动中反证思路的三个环节是什么？", "先假设结论不成立，再推出矛盾，最后否定假设并确认原结论。"),
    "C08-L08": ("计算√81、∛(−27)，并判断√7在哪两个相邻整数之间。", "√81=9，∛(−27)=−3；2<√7<3。", "概括平方根、算术平方根和立方根的主要区别。", "正数有两个平方根，算术平方根只取非负值；任意实数都有唯一立方根，符号与原数一致。"),
    "C09-L01": ("点A(−3,2)、B(0,−4)、C(5,0)分别在哪里？", "A在第二象限；B在y轴负半轴；C在x轴正半轴。", "第四象限点的横、纵坐标符号分别是什么？", "横坐标为正，纵坐标为负。"),
    "C09-L02": ("矩形四点为A(0,0)、B(4,0)、C(4,3)、D(0,3)。用坐标描述其位置和边长。", "矩形位于第一象限及坐标轴上；AB=4，BC=3。", "建立坐标系描述图形时，怎样选原点和单位长度更简洁？", "选取关键点或对称位置作原点，使坐标多为整数且数值较小；单位长度与实际尺度匹配。"),
    "C09-L03": ("学校在观测点O的北偏东30°方向、距离2 km处。用方向和距离完整描述位置。", "学校位于O点北偏东30°、2 km处；方向和距离缺一不可。", "只说“在东北方向”能否唯一确定一点？", "不能；还缺少距离，且“东北”只给出方向。"),
    "C09-L04": ("点P(−2,3)向右平移5个单位，再向下平移4个单位，求新坐标。", "先得(3,3)，再得(3,−1)，所以新坐标为(3,−1)。", "点(x,y)向左a个单位、向上b个单位后的坐标是什么？", "(x−a, y+b)。"),
    "C09-L05": ("三角形三个顶点的横坐标都加3、纵坐标都减2，图形怎样平移？", "整体向右平移3个单位、向下平移2个单位。", "图形平移后，对应点坐标差是否相同？", "相同；所有对应点的横坐标差、纵坐标差分别等于同一次平移的水平和竖直分量。"),
    "C09-L06": ("在方格纸上设计“寻宝路线”：从(−2,1)出发，右移4、上移3、左移1，写出终点。", "终点依次为(2,1)、(2,4)、(1,4)，最终为(1,4)。", "活动展示时如何验证同伴的坐标路线？", "逐段检查横、纵坐标变化与方向距离是否一致，并在坐标系中标点连线复核。"),
    "C09-L07": ("点A(−1,2)向右3、向下5得到A'，求A'并判断所在象限。", "A'=(2,−3)，在第四象限。", "概括“坐标确定位置”和“坐标变化描述平移”的对应关系。", "有序数对唯一确定点；横坐标变化对应左右平移，纵坐标变化对应上下平移。"),
    "C10-L01": ("判断方程2x+y=7是否为二元一次方程，并检验(2,3)是否为它的解。", "是；含两个未知数且次数为1。代入得2×2+3=7，所以(2,3)是解。", "什么叫二元一次方程组的解？", "同时满足方程组中每一个方程的一对未知数的值。"),
    "C10-L02": ("用代入法解方程组y=2x+1，x+y=7。", "把y代入第二式：x+2x+1=7，x=2，y=5；解为(2,5)。", "代入法中，求出一个未知数后为什么必须回代？", "要得到另一个未知数并检验这对数同时满足两个方程。"),
    "C10-L03": ("用加减法解x+y=7，x−y=1。", "两式相加得2x=8，x=4；代入得y=3。", "何时可以把两个方程直接相加消去一个未知数？", "该未知数的系数互为相反数时。"),
    "C10-L04": ("用加减法解2x+3y=12，3x−2y=5。", "第一式乘2、第二式乘3后相加：13x=39，x=3；代入得y=2。", "代入法和加减法怎样选择更简便？", "有未知数系数为1或易表示时选代入；系数相等或容易配成相反数时选加减。"),
    "C10-L05": ("成人票5元、学生票3元，共售20张收76元。各售多少张？", "设成人票x张、学生票y张：x+y=20，5x+3y=76，解得x=8，y=12。", "应用题方程组求解后为什么要检验实际意义？", "要检查数值是否满足原等量关系以及人数、数量等是否为非负整数。"),
    "C10-L06": ("2元笔和5元本共买50件，花160元。各买多少？", "设笔x支、本y本：x+y=50，2x+5y=160，解得x=30，y=20。", "用表格建模时至少应列出哪些栏目？", "未知量、单位量、数量、总量及题中的两个等量关系。"),
    "C10-L07": ("解方程组x+y+z=6，x−y=0，y−z=0。", "由后两式得x=y=z，代入第一式得3x=6，所以x=y=z=2。", "解三元一次方程组的核心思想是什么？", "逐步消元，把三元化为二元，再化为一元，最后逐级回代。"),
    "C10-L08": ("比较《九章算术》方程术与现代加减消元法的共同思想。", "都通过对方程行进行倍乘、相加或相减，逐步消去未知数；现代方法用符号表达更统一。", "数学史阅读记录应区分哪两类信息？", "史实与年代等客观信息，以及由史实得到的数学方法理解或个人感受。"),
    "C10-L09": ("设计一个含两个未知量的校园消费调查问题，列出方程组并说明数据来源。", "示例：两种午餐共40份，总价360元，单价分别8元和10元；设份数x、y，列x+y=40，8x+10y=360。", "活动报告怎样证明所列方程组与情境对应？", "逐一解释未知数、每个方程左右两边的实际意义，并将解代回原数据检验。"),
    "C10-L10": ("分别用代入法或加减法解y=x+1，2x+y=7。", "代入得2x+x+1=7，x=2，y=3。", "章末复习时怎样选择消元方法？", "先观察系数：易表示选代入，易配系数选加减；复杂问题先整理方程再选择。"),
    "C11-L01": ("不等式x+3>7的解是什么？在数轴上怎样表示？", "x>4；在4处画空心圆，向右画射线。", "x=5是否是不等式2x−1<10的解？", "是；代入得9<10。"),
    "C11-L02": ("由−2x>6求x的范围，并说明不等号为何改变方向。", "两边同除以−2，不等号方向改变，得x<−3。", "若a>b，两边同时加5、同时乘3、同时乘−1后关系怎样？", "a+5>b+5，3a>3b，−a<−b。"),
    "C11-L03": ("某商品每件3元，另付5元包装费，总费用不超过20元，最多买几件？", "3x+5≤20，x≤5；按整数件数，最多5件。", "用求差法比较a和b的大小时看什么？", "看a−b的符号：正则a>b，零则a=b，负则a<b。"),
    "C11-L04": ("解不等式2x−5≤7，并在数轴上表示。", "2x≤12，x≤6；在6处实心圆，向左画射线。", "解不等式与解方程的步骤相似，最关键的不同是什么？", "乘或除以负数时必须改变不等号方向。"),
    "C11-L05": ("每本练习册8元，预算不超过50元，最多买多少本？", "设买x本，8x≤50，x≤6.25；x为非负整数，所以最多6本。", "“至少”“至多”通常分别对应什么不等号？", "至少对应≥，至多或不超过对应≤。"),
    "C11-L06": ("解不等式组x>1，x≤4，并写出整数解。", "公共解集为1<x≤4；整数解为2、3、4。", "数轴法求不等式组解集的实质是什么？", "找各不等式解集在数轴上的公共部分。"),
    "C11-L07": ("设计一个“不超过预算且至少达到数量”的不等式活动，给出解集。", "示例：每件4元，预算30元且至少买5件，得5≤x≤7.5；整数方案x=5、6、7。", "活动中怎样验证整数方案没有遗漏？", "先求连续解集，再结合数量为整数逐一列出，并代回所有限制条件。"),
    "C11-L08": ("解不等式组2x−1>3，x+2≤7。", "x>2且x≤5，所以2<x≤5。", "概括单个不等式与不等式组解集的联系。", "不等式组的解集是组内各不等式解集的公共部分。"),
    "C11-L09": ("某家庭拟把月用电量从260 kWh降至不超过220 kWh，至少需减少多少？", "设减少x kWh，260−x≤220，得x≥40，至少减少40 kWh。", "低碳方案评价除计算减排量外还应考虑什么？", "数据来源、方案可行性、成本、持续性和家庭成员可接受程度。"),
    "C12-L01": ("调查40名学生最喜欢的球类，篮球16人。篮球的频数和百分比分别是多少？", "频数16，百分比16÷40×100%=40%。", "全面调查的一般步骤是什么？", "明确问题、确定对象、设计问卷、收集整理数据、描述分析并得出结论。"),
    "C12-L02": ("从全校1200人中随机抽取60人调查睡眠时间。指出总体、个体、样本和样本容量。", "总体：全校1200人的睡眠时间；个体：每名学生的睡眠时间；样本：抽取60人的睡眠时间；样本容量60。", "简单随机抽样为什么强调每个个体机会均等？", "机会均等有助于减少选择偏差，使样本更有代表性。"),
    "C12-L03": ("要了解一批灯泡寿命，选择全面调查还是抽样调查？说明理由。", "选抽样调查；寿命测试可能具有破坏性且数量大，应取有代表性的样本估计总体。", "样本代表性不足会带来什么后果？", "样本结论可能系统偏离总体，导致用样本估计总体的结果不可靠。"),
    "C12-L04": ("某类占总体的25%，在扇形图中对应的圆心角是多少？", "360°×25%=90°。", "比较各类别数量与展示各部分占总体比例，分别更适合什么图？", "数量比较常用条形图；部分占总体比例常用扇形图。"),
    "C12-L05": ("甲、乙两班连续4次平均分要在同图中比较变化趋势，应选什么图？", "复合折线图；可同时观察两组数据的升降趋势和差距变化。", "复合条形图最适合突出什么信息？", "同一类别下多组数量的直观比较。"),
    "C12-L06": ("数据最大值98、最小值53，取组距10，至少分几组？", "极差45，45÷10=4.5，所以至少分5组。", "频数分布直方图中小长方形的横轴、纵轴分别表示什么？", "横轴表示分组区间，纵轴表示频数（等组距时高度可直接比较频数）。"),
    "C12-L07": ("某样本身高直方图中150≤x<160有12人、160≤x<170有20人，哪组频数更大？", "160≤x<170组更大，频数20，比前一组多8人。", "利用样本直方图估计总体时要保留什么限制？", "结论是估计而非精确值，可靠性取决于抽样的随机性、样本容量和分组合理性。"),
    "C12-L08": ("气温从8时到14时随时间上升，14时后下降。用一句话描述两量关系。", "8—14时气温随时间总体上升，14时后随时间总体下降，转折点约在14时。", "趋势图能否仅凭少量点保证精确预测很远以后的数值？", "不能；趋势只能支持有限范围估计，远期预测还受样本范围和其他因素影响。"),
    "C12-L09": ("同时展示班级人数、各类占比和一周变化趋势，应分别选哪些图？", "人数比较用条形图，占比用扇形图，随时间变化用折线图。", "选择统计图的首要依据是什么？", "研究问题和数据特点：比较数量、表示比例、展示分布或观察变化趋势。"),
    "C12-L10": ("用电子表格制作统计图时，按什么顺序操作并核对？", "录入并核对数据，选中数据区域，选择合适图表类型，完善标题/图例/坐标轴，最后与原数据复核。", "信息技术生成图表后为什么仍需人工检查？", "软件会按输入机械作图，错误数据、选区或图表类型会造成误导，必须核对数据与表达目的。"),
    "C12-L11": ("40人中某组频数为10，求频率；若画扇形图，求圆心角。", "频率10÷40=0.25；圆心角360°×0.25=90°。", "概括统计调查从数据到结论的完整链条。", "确定问题与调查方式—收集数据—整理频数/频率—选择统计表图—分析解释—评价可靠性。"),
    "C12-L12": ("记录某地每月15日白昼时长，选择什么图最适合观察全年变化？", "折线图；月份有顺序，折线能清楚呈现随时间的周期变化。", "对白昼时长规律作结论时，应说明哪些限制？", "地点、年份、采样日期和数据来源；单年单地数据只能描述该样本，不能无限外推。"),
}


def sanitize(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]', "_", value)
    return re.sub(r"\s+", "", value).strip("._")


def lesson_type_label(value: str) -> str:
    return {
        "new_lesson": "新授课",
        "practice_lesson": "练习课",
        "activity_lesson": "活动课",
        "review_lesson": "复习课",
        "integrated_practice": "综合实践课",
    }.get(value, "新授课")


def question(qid: str, prompt: str, answer: str, score: int, error: str, steps: list[str] | None = None) -> dict:
    return {"id": qid, "prompt": prompt, "answer": answer, "steps": steps or [], "score": score, "error": error}


def make_questions(lesson: dict) -> list[dict]:
    lid = lesson["id"]
    if lid not in PROBLEMS:
        raise KeyError(f"Missing problem bank entry: {lid}")
    q4_prompt, q4_answer, q8_prompt, q8_answer = PROBLEMS[lid]
    core = lesson["core_knowledge"]
    prereq = lesson["prerequisites"]
    key = lesson["key_points"]
    difficulty = lesson["difficulties"]
    example = "、".join(lesson["examples"])
    q1 = question(
        "Q1",
        f"回顾“{prereq[0]}”：写出一条与本课有关的定义、性质或计算规则。",
        f"参考要点：正确表述“{prereq[0]}”的核心含义，并说明它与“{core[0]}”的联系。",
        2,
        "只写关键词，没有说明含义或使用条件。",
    )
    q2 = question(
        "Q2",
        f"阅读教材印刷页{lesson['source_pages'][0]}—{lesson['source_pages'][-1]}，圈出“{'、'.join(core)}”，分别用一句话记录它们解决什么问题。",
        "；".join(f"{item}：按教材定义、性质或步骤准确表述" for item in core) + "。",
        3,
        "把概念名称、成立条件和结论混在一起。",
    )
    q3 = question(
        "Q3",
        f"小组探究：围绕“{difficulty[0]}”设计一次观察、操作或推理，记录现象、猜想和验证依据。",
        f"参考思路：先明确条件，再围绕“{key[0]}”形成猜想，最后用定义、计算、图表或反例验证。",
        3,
        "只给结论，没有记录验证过程或依据。",
    )
    q4 = question(
        "Q4",
        f"例题（对应{example}）：{q4_prompt}",
        q4_answer,
        4,
        f"没有先确认“{key[0]}”的条件，或只写结果不写依据。",
        ["提取已知条件与所求", f"选择“{key[0]}”对应的方法", "规范计算或说明并回到原题检验"],
    )
    q5 = question(
        "Q5",
        f"基础辨析：判断“使用‘{core[0]}’时不需要检查条件，只要结论看起来合理即可”，并说明理由。",
        f"错误。必须先核对“{core[0]}”的定义或成立条件，再作出结论。",
        3,
        "只写对错，没有指出需要检查的条件。",
    )
    q6 = question(
        "Q6",
        f"变式练习：把Q4的一个条件、数据或表示方式作合理改变，仍用“{key[-1]}”解决，并写出检验。",
        f"答案不唯一。评价要点：改变后的条件完整；方法仍属于“{key[-1]}”；过程正确；检验与新条件一致。",
        4,
        "改变条件后仍照抄原结果，或新题条件不完整。",
        ["说明改变了什么", "给出完整解答", "核对答案是否满足新条件"],
    )
    q7 = question(
        "Q7",
        f"纠错：“研究{lesson['lesson_title']}时，只记结论，不必区分条件、过程和依据。”这句话对吗？",
        f"不对。应围绕“{key[0]}”写清条件、过程和依据；否则结论可能被误用。",
        3,
        "用“我觉得”代替定义、运算、图形或数据证据。",
    )
    q8 = question(
        "Q8",
        f"当堂检测：{q8_prompt}",
        q8_answer,
        4,
        f"忽略“{difficulty[0]}”，或结果未回到题意检验。",
        ["独立完成并写出关键依据", "用定义、代入、逆算、数轴或图表复核"],
    )
    return [q1, q2, q3, q4, q5, q6, q7, q8]


def make_flow(lesson: dict, questions: list[dict]) -> list[dict]:
    title = lesson["lesson_title"]
    core = lesson["core_knowledge"]
    key = lesson["key_points"]
    difficulty = lesson["difficulties"][0]
    return [
        {"stage": "情境导入", "teacher": [f"呈现与“{title}”有关的教材情境或真实问题。", "追问：题目中哪些量、图形或数据值得研究？"], "student": ["观察并提取信息，提出本课问题。"], "expected": f"能说出本课将研究“{core[0]}”。", "intent": "让知识从教材情境或真实任务中自然产生。", "correction": "若只描述表面现象，追问条件、对象和所求。", "minutes": 3, "ppt": "1—3"},
        {"stage": "旧知回顾", "teacher": [f"组织Q1，回顾“{lesson['prerequisites'][0]}”。", "板书连接新旧知识的关键词。"], "student": ["独立作答后同桌核对。"], "expected": "能准确调用一条前置定义、性质或规则。", "intent": "激活本课必需的前置知识。", "correction": "对条件缺失的表述补充反例或完整定义。", "minutes": 4, "ppt": "4"},
        {"stage": "自主探究", "teacher": ["布置Q2、Q3，提供图形、数据或操作材料。", f"围绕难点“{difficulty}”巡视提问。"], "student": ["阅读、操作、记录并在小组内形成猜想。"], "expected": f"能从活动中提取“{'、'.join(core[:2])}”的共同特征。", "intent": "经历从具体材料到数学关系的抽象过程。", "correction": "若直接抄结论，要求补写现象、猜想和验证。", "minutes": 8, "ppt": "5"},
        {"stage": "概念形成", "teacher": [f"依据学生记录形成“{'、'.join(core)}”的规范表述。", "用正例、反例或边界情形检查成立条件。"], "student": ["补全学案概念栏，并用自己的话解释。"], "expected": "能区分概念名称、条件、结论和表示方法。", "intent": "把探究经验提升为可使用的数学知识。", "correction": "对关键词遗漏的答案回到教材原句逐项核对。", "minutes": 6, "ppt": "6—7"},
        {"stage": "性质推导", "teacher": [f"追问“为什么”，围绕“{key[0]}”组织说明。", "强调每一步的依据和适用条件。"], "student": ["完成Q3的验证，口头说明推理或计算链。"], "expected": "能把结论与定义、运算、图形或数据证据连接。", "intent": "发展推理、运算、模型或数据分析能力。", "correction": "若用结论证明自身，要求重新寻找前置依据。", "minutes": 6, "ppt": "8—9"},
        {"stage": "例题示范", "teacher": [f"出示Q4（对应{'、'.join(lesson['examples'])}），先遮住解答。", "按“条件—方法—过程—检验”板演。"], "student": ["独立尝试，再对照规范解答订正。"], "expected": questions[3]["answer"], "intent": "示范把概念和方法落实到完整解题过程。", "correction": questions[3]["error"], "minutes": 7, "ppt": "10—11"},
        {"stage": "分层练习", "teacher": ["安排Q5—Q7，巡视记录概念、过程和表达三类问题。", "选择正确答案和典型错误进行互评。"], "student": ["完成基础、变式和纠错任务，按评分点互评。"], "expected": f"能运用“{'、'.join(key)}”解决同类问题。", "intent": "用梯度练习巩固知识并暴露易错点。", "correction": "对只写结果的答案要求补全依据和检验。", "minutes": 7, "ppt": "12—13"},
        {"stage": "检测小结", "teacher": ["组织Q8独立检测。", f"用“{'—'.join(core[:3])}”梳理知识结构并布置分层作业。"], "student": ["独立作答、自评目标达成情况。"], "expected": "能写出本课关键词、方法和一条需要继续订正的问题。", "intent": "即时评价目标达成并形成结构化认识。", "correction": "若总结只列名词，要求补充条件、作用或步骤。", "minutes": 4, "ppt": "14—15"},
    ]


def make_source(lesson: dict, chapter: dict) -> dict:
    pages = lesson["source_pages"]
    section = str(lesson["source_section"])
    prefix_base = section if section and section[0].isdigit() else lesson["id"]
    file_prefix = sanitize(f"{prefix_base}_{lesson['lesson_title']}")
    questions = make_questions(lesson)
    core = lesson["core_knowledge"]
    key = lesson["key_points"]
    difficulty = lesson["difficulties"]
    source = {
        "meta": {
            "lesson_id": lesson["id"],
            "section": section,
            "title": lesson["lesson_title"],
            "file_prefix": file_prefix,
            "chapter": f"第{chapter['chapter_number']}章 {chapter['chapter_title']}",
            "lesson_type": lesson_type_label(lesson["lesson_type"]),
            "textbook": "人教版《义务教育教科书·数学七年级下册》",
            "period": "第1课时",
            "grade": "七年级",
            "printed_pages": f"{pages[0]}—{pages[-1]}" if len(pages) > 1 else str(pages[0]),
            "pdf_pages": f"{pages[0] + 7}—{pages[-1] + 7}" if len(pages) > 1 else str(pages[0] + 7),
            "needs_figure": bool(lesson["needs_figure"]),
        },
        "curriculum_basis": f"通过观察、操作、运算、推理或数据分析理解{lesson['lesson_title']}，能用数学语言表达过程和依据，在解决教材问题中发展抽象能力、推理能力、运算能力、模型观念、几何直观或数据意识。",
        "textbook_analysis": {
            "position": f"本课位于{chapter['chapter_title']}，核心内容是{'、'.join(core)}，是本章知识链中的重要一环。",
            "connection": f"以前置知识“{'、'.join(lesson['prerequisites'])}”为基础，并为后续本章综合应用、章末复习和相关知识学习提供方法支撑。",
            "intent": f"教材通过{'、'.join(lesson['examples'])}与{'、'.join(lesson['exercises'])}，按情境—探究—结论—应用的路径组织学习。",
        },
        "student_analysis": {
            "foundation": f"学生已经学习{'、'.join(lesson['prerequisites'])}，具备基本观察、计算、作图或整理数据的经验。",
            "difficulties": f"学生可能在“{difficulty[0]}”处出现条件遗漏、表示不规范或方法选择不当。",
            "misconceptions": [f"只记“{core[0]}”的结论，不检查适用条件。", f"把“{key[0]}”与相近概念或逆命题混淆。", "只写结果，不写过程、依据或检验。"],
        },
        "objectives": [
            f"通过阅读、观察或操作，准确说出{'、'.join(core)}的含义、表示或基本步骤。",
            f"在Q2—Q4中运用“{key[0]}”，能用完整语言、式子、图形或图表说明依据。",
            f"在基础与变式练习中运用“{key[-1]}”解决同类问题，并对结果进行检验。",
            f"在合作探究和互评中形成先审条件、再选方法、规范表达、主动复核的学习习惯。",
        ],
        "key_point": "；".join(key),
        "difficulty": "；".join(difficulty),
        "methods": ["问题驱动", "自主学习", "合作探究", "例练结合", "同伴互评"],
        "preparation": {
            "teacher": ["教材PDF对应页面", "课堂教学PPT", "学生学案", "实物投影或展示工具"],
            "student": ["教材", "学案", "直尺与必要学习工具"],
        },
        "blackboard": [lesson["lesson_title"], *[f"{i + 1}. {item}" for i, item in enumerate(core)], f"方法：{' → '.join(key)}", f"易错：{difficulty[0]}"],
        "flow": make_flow(lesson, questions),
        "questions": questions,
        "homework": {
            "basic": [f"完成{'、'.join(lesson['exercises'])}中的基础题并订正Q5、Q7", f"把本课“{'、'.join(core)}”整理成三行知识卡"],
            "advanced": [questions[7]["prompt"], f"从{'、'.join(lesson['homework_scope'])}中选择一题，写出完整依据和检验"],
        },
        "evaluation": ["目标1：Q1、Q2共5分，达到4分视为达成。", "目标2：Q3、Q4共7分，达到5分视为达成。", "目标3：Q5—Q8共14分，达到11分视为达成。", "过程评价：记录完整、交流有依据、订正能说明错误原因。"],
        "worksheet": {
            "section_titles": {"self_study": "三、自主学习：阅读教材并提取信息", "inquiry": "四、合作探究：观察、猜想与验证"},
            "concept_teacher": [f"{item}：按教材明确其定义、条件、表示、性质或步骤。" for item in core],
            "concept_student": [f"{item}：____________________________________________________________。" for item in core[:3]],
            "notice": f"易错提醒：{difficulty[0]}。先审条件，再使用结论。",
            "method": "提取条件 → 选择概念或方法 → 规范求解/作图/整理 → 写出依据 → 回到题意检验。",
            "method_student": "提取________ → 选择________ → 规范完成 → 写出依据 → ________检验。",
            "summary": f"小结参考：本课围绕“{lesson['lesson_title']}”，掌握{'、'.join(core)}，并能运用{'、'.join(key)}。",
        },
    }
    return source


def draw_topic_diagram(path: Path, lesson: dict) -> None:
    width, height = 1200, 430
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_BOLD), 42)
    font = ImageFont.truetype(str(FONT), 30)
    small = ImageFont.truetype(str(FONT), 24)
    green, dark, orange, pale = "#1B8F77", "#334155", "#E4793B", "#F1FAF7"
    draw.rounded_rectangle((20, 20, width - 20, height - 20), radius=28, fill=pale, outline="#B8D7CB", width=3)
    draw.text((50, 40), lesson["lesson_title"], font=title_font, fill=dark)
    chapter = lesson["chapter_id"]
    if chapter == "C07":
        draw.line((150, 310, 680, 145), fill=green, width=8)
        draw.line((160, 140, 670, 315), fill=dark, width=8)
        draw.ellipse((408, 218, 432, 242), fill=orange)
        draw.text((700, 155), "观察位置", font=font, fill=green)
        draw.text((700, 220), "写出关系", font=font, fill=dark)
        draw.text((700, 285), "说明依据", font=font, fill=orange)
    elif chapter == "C08":
        draw.line((120, 270, 1080, 270), fill=dark, width=5)
        for i, value in enumerate(["−2", "−1", "0", "1", "√2", "2"]):
            x = 180 + i * 160
            draw.line((x, 250, x, 290), fill=dark, width=4)
            draw.text((x - 25, 305), value, font=small, fill=green if value == "√2" else dark)
        draw.ellipse((810, 252, 828, 270), fill=orange)
    elif chapter == "C09":
        draw.line((150, 245, 710, 245), fill=dark, width=5)
        draw.line((430, 105, 430, 365), fill=dark, width=5)
        draw.polygon([(710, 245), (690, 235), (690, 255)], fill=dark)
        draw.polygon([(430, 105), (420, 125), (440, 125)], fill=dark)
        draw.ellipse((535, 165, 557, 187), fill=orange)
        draw.text((565, 150), "P(x, y)", font=font, fill=green)
        draw.text((740, 190), "横坐标 ↔ 左右", font=small, fill=dark)
        draw.text((740, 250), "纵坐标 ↔ 上下", font=small, fill=dark)
    elif chapter == "C10":
        draw.rounded_rectangle((110, 145, 470, 315), radius=20, fill="white", outline=green, width=4)
        draw.text((150, 175), "方程①", font=font, fill=dark)
        draw.text((150, 245), "方程②", font=font, fill=dark)
        draw.line((500, 230, 720, 230), fill=orange, width=7)
        draw.polygon([(720, 230), (690, 212), (690, 248)], fill=orange)
        draw.text((520, 165), "消元", font=font, fill=orange)
        draw.rounded_rectangle((760, 170, 1080, 290), radius=20, fill="white", outline=dark, width=4)
        draw.text((820, 205), "一元方程", font=font, fill=green)
    elif chapter == "C11":
        draw.line((120, 260, 1080, 260), fill=dark, width=5)
        for i in range(7):
            x = 180 + i * 140
            draw.line((x, 245, x, 275), fill=dark, width=4)
            draw.text((x - 10, 295), str(i - 2), font=small, fill=dark)
        draw.ellipse((590, 244, 622, 276), outline=green, width=6)
        draw.line((622, 260, 1010, 260), fill=green, width=10)
        draw.polygon([(1010, 260), (980, 242), (980, 278)], fill=green)
        draw.text((520, 150), "解集", font=font, fill=orange)
    else:
        values = [90, 150, 215, 120, 260]
        for i, val in enumerate(values):
            x0 = 120 + i * 150
            draw.rectangle((x0, 340 - val, x0 + 85, 340), fill=green if i != 4 else orange)
        draw.line((90, 340, 920, 340), fill=dark, width=4)
        pts = [(980, 295), (1030, 240), (1080, 175), (1130, 210)]
        draw.line(pts, fill=dark, width=6)
        for x, y in pts:
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=orange)
        draw.text((950, 110), "比较 · 分布 · 趋势", font=small, fill=dark)
    draw.text((50, height - 55), "教材任务 → 自主记录 → 合作验证 → 规范表达", font=small, fill="#536B62")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, quality=95)


def main() -> int:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    chapters = {chapter["chapter_id"]: chapter for chapter in manifest["chapters"]}
    created = 0
    for lesson in manifest["lessons"]:
        if lesson["id"] == "C07-L01":
            continue
        chapter = chapters[lesson["chapter_id"]]
        source = make_source(lesson, chapter)
        chapter_dir = ROOT / "lessons" / f"第{chapter['chapter_number']:02d}章_{chapter['chapter_title']}"
        lesson_dir = chapter_dir / source["meta"]["file_prefix"]
        for subdir in ["教学设计", "PPT", "学案", "素材", "构建文件"]:
            (lesson_dir / subdir).mkdir(parents=True, exist_ok=True)
        source_path = lesson_dir / "构建文件" / "lesson.yml"
        source_path.write_text(yaml.safe_dump(source, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
        draw_topic_diagram(lesson_dir / "素材" / "diagram_topic.png", lesson)
        created += 1
    print(f"[OK] structured_sources={created} skipped_gold_sample=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
