# Phase 6 成熟教案风格学习与三节样板重写总结

## 完成范围

本阶段只处理 C01-L03、C05-L05、C06-L07 三节样板，没有生成其余课时。

## 输入资料

- 三份成熟教案已原样复制到 `references/mature_lessonplans/`，根目录原件未修改。
- 结构化抽取、媒体文件、Word 只读导出 PDF、逐页 PNG 和 source contact sheet 位于 `build/mature_lessonplan_analysis/`。
- 七年级数学内容只核对教材指定页段：数轴 8—11 页、移项 122—124 页、角的比较与运算 173—175 页。

## 风格与结构

- 新增 `config/lessonplan_style.yml`，状态为 `frozen_for_pilot_review`。
- 新增 `reports/guolihua_lessonplan_style_guide.md`。
- 三份 `lessons/<id>/lessonplan.yml` 已升级为结构化教师问题、动作、说明、纠错、例练、学生动作、预期回答、设计意图和估时。
- `scripts/build_lessonplans_v2.py` 已改为从 YAML 读取内容，不再硬编码教案正文。

## 四页模板

- 使用根目录 `blank.pdf` 的项目副本 `templates/lessonplan/hepingjie_blank.pdf`。
- 两文件 SHA-256 均为 `65317D6AF090646018F2EA02FBE4BF9C2625303F551CF222B9A02F764228F1EA`。
- 背景 PDF 未修改、未重绘。
- 生成时分别叠加背景第 1、2、3、4 页。

## 输出

- `dist/lessonplans_v2/C01-L03_数轴_教案_v2.pdf`
- `dist/lessonplans_v2/C05-L05_移项解一元一次方程_教案_v2.pdf`
- `dist/lessonplans_v2/C06-L07_角的比较与运算_教案_v2.pdf`

每节在 `build/lessonplans_v2/<课时编号>/` 保留：

- `lessonplan.yml`
- `lessonplan.tex`
- `lessonplan.pdf`
- 4 张 `page-*.png`
- `contact-sheet.png`
- `lessonplan.compile.log`
- `v1_v2_difference.md`

## 验证结果

| 课时 | 页数 | A4纵向 | 估时 | PNG | Overfull | 编译错误 | 反思空白 | 人工逐页审阅 |
|---|---:|---|---:|---:|---:|---:|---|---|
| C01-L03 | 4 | 是 | 45 | 4 | 0 | 0 | 是 | 通过 |
| C05-L05 | 4 | 是 | 45 | 4 | 0 | 0 | 是 | 通过 |
| C06-L07 | 4 | 是 | 45 | 4 | 0 | 0 | 是 | 通过 |

编译日志有少量 `cmex` 数学扩展字体在 10.5pt 下的尺寸替代警告，未造成字符缺失、公式错位或可见版面问题。

## 报告

- `reports/mature_lessonplan_analysis.md`
- `reports/mature_lessonplan_structure.csv`
- `reports/pilot_lessonplan_v1_v2_comparison.md`
- `reports/pilot_lessonplan_v1_v2_comparison.csv`
- `reports/mature_style_adoption_report.md`
- `reports/pilot_lessonplan_human_review.md`
- `reports/phase6_summary.md`

## 结论与停止条件

v2 比 v1 更适合作为后续批量生成的候选标准：教学链条完整、例练相邻、提问具体、学生任务真实、设计意图简短、板书可用，且能稳定放入四页模板。是否正式冻结并批量生产，仍需郭老师按人工审阅清单确认。

本阶段到此停止。未生成其余全部教案，未生成学生学案，未修改教材 PDF 或成熟教案原件。
