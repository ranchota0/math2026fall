# 教案 PDF 背景模板与三节样板验证报告

生成时间：2026-07-19T23:17:09

## 背景模板

- 原始 PDF：`blank.pdf`
- 项目副本：`templates/lessonplan/hepingjie_blank.pdf`
- SHA-256 一致：`True`
- SHA-256：`65317D6AF090646018F2EA02FBE4BF9C2625303F551CF222B9A02F764228F1EA`

## 验证结果

| 课时 | PDF | 页数 | A4纵向 | 时间45分钟 | 课后反思空白 | 数据越界估算 | 日志错误 | 结论 |
|---|---|---:|---|---|---|---|---:|---|
| C01-L03 | `build/lessonplans/C01-L03/lessonplan.pdf` | 4 | True | True | True | 通过 | 0 | 通过 |
| C05-L05 | `build/lessonplans/C05-L05/lessonplan.pdf` | 4 | True | True | True | 通过 | 0 | 通过 |
| C06-L07 | `build/lessonplans/C06-L07/lessonplan.pdf` | 4 | True | True | True | 通过 | 0 | 通过 |

## 坐标系统

- 坐标文件：`tex/lessonplan/hepingjie_coordinates.tex`
- 原点：A4 页面左上角。
- 单位：毫米。
- 第 4 页教学过程盒高度限制在课后反思区域上方，验证时不得进入课后反思区域。

## 结论

- 背景 PDF 已作为唯一版式模板使用，未重新绘制表格。
- 三节样板均按 4 页 A4 纵向生成。
- 自动检查通过后仍需人工核对打印视觉效果、学校留白习惯和个别长句换行。