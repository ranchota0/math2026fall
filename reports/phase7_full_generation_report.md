# Phase 7 全量教案批量生成报告

完成时间：2026-08-01T23:04:51+08:00

## 结果摘要

- 课程清单总课时数：53
- Phase 6.1 已验收样例：3
- 本阶段新生成：50
- 成功通过：53
- 阻塞项：0
- 版面例外：0
- 页数分布：{4: 53}
- 课堂时长分布：{45: 53}
- 完整例题总数：213
- 课堂练习与反馈题总数：477
- 结构化图形总数：22

## 冻结保护

- 公共样式、冻结生成器、风格配置和 Phase 6.1 报告 SHA-256 与基线一致。
- 三份已验收 PDF 直接复制进入正式目录，SHA-256 与 Phase 6.1 基线完全一致。
- 当前目录不是 Git 仓库，因此未创建冻结提交；使用 `reports/phase7_freeze_baseline.md` 的 SHA-256 基线提供回滚核对依据。

## 检查结果

- 编译：53/53 成功；LaTeX Error=0，Undefined control sequence=0，Fatal error=0，Overfull hbox=0。
- 文件：53 PDF、53 TeX、53 YAML、212 PNG、53 单课 contact sheet、6 批次 contact sheet。
- 版式：53/53 为 A4 纵向 4 页；45 分钟总时长准确；课后反思保持空白。
- 结构：例题、具体练习、10 分反馈测试、答案与达标标准、A/B/C 分层作业均已检查。
- 禁用结构：未发现 itemize 黑点、textbullet、负间距或零宽盒子。
- 图形：未发现如图无图、图形缺失、超栏或文字重叠。
- 人工视觉：6 批次共 212 页已通过 contact sheet 审阅；疑似页面已放大复核。
- Phase 7 专项验收：`python scripts/validate_phase7_lessonplans.py` 通过，53/53。
- 通用基础设施验收：`python scripts/validate_project.py` 的 YAML、模板和 sample 检查通过；其第一阶段规则仍禁止 `dist/` 中出现正式教案，因此对 Phase 3--6 已验收 PDF 产生 10 项兼容性误报。

## 逐课统计

| 课时 ID | 课题 | 课型 | 页数 | 分钟 | 例题 | 练习/检测 | 图形 | 状态 |
|---|---|---|---:|---:|---:|---:|---:|---|
| C01-L01 | 正数和负数 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C01-L02 | 有理数的概念与分类 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C01-L03 | 数轴 | 概念形成课 | 4 | 45 | 3 | 8 | 3 | approved |
| C01-L04 | 相反数与绝对值 | 运算技能课 | 4 | 45 | 4 | 9 | 1 | generated |
| C01-L05 | 有理数的大小比较 | 概念形成课 | 4 | 45 | 4 | 9 | 1 | generated |
| C01-L06 | 有理数数学活动 | 数学活动课 | 4 | 45 | 4 | 9 | 0 | generated |
| C01-L07 | 有理数章末小结与复习 | 章末复习课 | 4 | 45 | 4 | 9 | 1 | generated |
| C02-L01 | 有理数加法法则 | 运算技能课 | 4 | 45 | 4 | 9 | 1 | generated |
| C02-L02 | 有理数加法运算律与应用 | 应用建模课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L03 | 有理数减法法则 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L04 | 有理数加减混合运算 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L05 | 有理数乘法法则 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L06 | 多个有理数相乘与乘法运算律 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L07 | 有理数除法 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L08 | 有理数乘除混合运算 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L09 | 有理数的乘方 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L10 | 科学记数法 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L11 | 近似数 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L12 | 有理数运算数学活动 | 数学活动课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L13 | 有理数运算章末小结与复习 | 章末复习课 | 4 | 45 | 4 | 9 | 0 | generated |
| C02-L14 | 进位制的认识与探究 | 综合实践课 | 4 | 45 | 4 | 9 | 1 | generated |
| C03-L01 | 用字母表示数与列代数式 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C03-L02 | 列代数式表示数量关系 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C03-L03 | 代数式的值 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C03-L04 | 代数式数学活动 | 数学活动课 | 4 | 45 | 4 | 9 | 0 | generated |
| C03-L05 | 代数式章末小结与复习 | 章末复习课 | 4 | 45 | 4 | 9 | 0 | generated |
| C04-L01 | 整式 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C04-L02 | 合并同类项 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C04-L03 | 去括号与整式加减 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C04-L04 | 整式加减数学活动 | 数学活动课 | 4 | 45 | 4 | 9 | 0 | generated |
| C04-L05 | 整式加减章末小结与复习 | 章末复习课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L01 | 从算式到方程 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L02 | 方程的解与一元一次方程 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L03 | 等式的性质 | 概念形成课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L04 | 合并同类项解一元一次方程 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L05 | 移项解一元一次方程 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | approved |
| C05-L06 | 去括号解一元一次方程 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L07 | 去分母解一元一次方程 | 运算技能课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L08 | 实际问题与一元一次方程一 | 应用建模课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L09 | 实际问题与一元一次方程二 | 应用建模课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L10 | 一元一次方程数学活动 | 数学活动课 | 4 | 45 | 4 | 9 | 0 | generated |
| C05-L11 | 一元一次方程章末小结与复习 | 章末复习课 | 4 | 45 | 4 | 9 | 0 | generated |
| C06-L01 | 立体图形与平面图形 | 几何探究课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L02 | 点线面体 | 几何探究课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L03 | 直线射线线段 | 几何探究课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L04 | 线段的比较与基本事实 | 几何探究课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L05 | 线段的运算与中点 | 几何探究课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L06 | 角的概念与度量 | 几何探究课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L07 | 角的比较与运算 | 几何探究课 | 4 | 45 | 6 | 10 | 4 | approved |
| C06-L08 | 余角和补角 | 几何探究课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L09 | 几何图形数学活动 | 数学活动课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L10 | 几何图形初步章末小结与复习 | 章末复习课 | 4 | 45 | 4 | 9 | 1 | generated |
| C06-L11 | 设计学校田径运动会比赛场地 | 综合实践课 | 4 | 45 | 4 | 9 | 1 | generated |

## 未解决问题

- 无阻塞课时或版面例外。
- 当前目录缺少 Git 元数据；本阶段未擅自初始化仓库。
- `validate_project.py` 尚未按项目阶段区分基础设施期与正式生产期；Phase 7 使用专项验收脚本作为交付判定，未改动这一旧规则。

## 交付位置

- PDF：`output/lesson_plans_final/pdf/`
- TeX：`output/lesson_plans_final/tex/`
- YAML：`output/lesson_plans_final/yaml/`
- 逐页 PNG：`output/lesson_plans_final/png/`
- contact sheet：`output/lesson_plans_final/contact_sheets/`
- manifest：`output/lesson_plans_final/manifests/`
- 自动验收：`reports/phase7_automatic_validation.md`
- 人工审阅：`output/lesson_plans_final/reports/phase7_visual_review.md`

## 最终结论

Phase 7 达到整体交付标准。未生成学生学案、试卷、PPT 或其他材料；未修改教材、原始成熟教案或三份 Phase 6.1 已验收样例。
