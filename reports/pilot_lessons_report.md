# 第三阶段样板课开发与 LaTeX 生产标准冻结报告

生成日期：2026-07-12

## 一、阶段边界

本轮只完成 3 节正式样板课开发、LaTeX 生产标准文件补充、编译与质量校验。未生成全册 53 课时内容，未修改 `references/textbook.pdf`，未重新规划 `config/curriculum_manifest.yml`，未删除 `lessons/_sample/` 或既有 smoke test。

## 二、选取的三节样板课

| lesson_id | 课题 | 类型 | 选择理由 |
|---|---|---|---|
| C01-L03 | 数轴 | new_lesson | 第一章典型概念形成课，适合检验概念抽象、数形结合、数轴 TikZ 图和学生作图空间。 |
| C05-L05 | 移项解一元一次方程 | new_lesson | 第五章典型方程推理课，适合检验计算推理、步骤化板书、错因分析和题号答案一致性。 |
| C06-L07 | 角的比较与运算 | new_lesson | 第六章含正式几何图形的新授课，适合检验角图 TikZ 资产、几何说理和教师学生共用图源。 |

## 三、新增和修改的主要文件

新增文件：

- `tex/course.sty`
- `tex/commands.tex`
- `templates/teacher_template.tex`
- `templates/student_template.tex`
- `scripts/compile_pilot_lessons.py`
- `scripts/validate_pilot_lessons.py`
- `lessons/C01-L03/lesson.yml`
- `lessons/C01-L03/teacher.tex`
- `lessons/C01-L03/student.tex`
- `lessons/C05-L05/lesson.yml`
- `lessons/C05-L05/teacher.tex`
- `lessons/C05-L05/student.tex`
- `lessons/C06-L07/lesson.yml`
- `lessons/C06-L07/teacher.tex`
- `lessons/C06-L07/student.tex`
- `lessons/C06-L07/assets/angle_figures.tex`
- `reports/pilot_build_report.csv`
- `reports/pilot_lessons_report.md`

修改文件：

- `scripts/validate_project.py`：允许仅本阶段三节 pilot lesson 的 `teacher.tex`、`student.tex`、局部 `assets/*.tex` 和对应 `dist/<lesson_id>/*.pdf`。

## 四、输出 PDF 与编译结果

| lesson_id | 教师版 PDF | 页数 | 学生版 PDF | 页数 | 状态 | warning | Overfull hbox |
|---|---|---:|---|---:|---|---:|---:|
| C01-L03 | `dist/C01-L03/teacher.pdf` | 3 | `dist/C01-L03/student.pdf` | 3 | success | 0 | 0 |
| C05-L05 | `dist/C05-L05/teacher.pdf` | 3 | `dist/C05-L05/student.pdf` | 3 | success | 0 | 0 |
| C06-L07 | `dist/C06-L07/teacher.pdf` | 3 | `dist/C06-L07/student.pdf` | 3 | success | 0 | 0 |

编译报告已写入 `reports/pilot_build_report.csv`。详细编译日志位于 `logs/pilot/`。

## 五、使用的主要宏包与样式

主要宏包集中在 `tex/course.sty`：

- `amsmath`
- `amssymb`
- `geometry`
- `array`
- `tabularx`
- `longtable`
- `enumitem`
- `tikz`
- `fancyhdr`
- `lastpage`
- `xcolor`

排版原则：A4、XeLaTeX、`ctexart`、黑白打印友好、不指定商业字体、不使用大面积装饰框、不使用教材截图。

## 六、几何图形生成方式

第六章样板课 `C06-L07` 的角图统一放在 `lessons/C06-L07/assets/angle_figures.tex`，教师版与学生版共用同一 TikZ 图源。当前包含：

- `\AngleSumFigure`
- `\StraightAngleFigure`
- `\AngleBisectorFigure`
- `\AnglePracticeFigure`

所有几何图形均为 TikZ 重绘，未使用教材截图。

## 七、自动校验结果

已执行：

1. `python scripts/validate_project.py`
   - 结果：通过。
2. `python scripts/compile_pilot_lessons.py`
   - 结果：3 节样板课、6 个 PDF 全部编译成功。
   - warning：0。
   - Overfull hbox：0。
3. `python scripts/validate_pilot_lessons.py`
   - 结果：通过。
   - 已检查三节 `lesson_id` 均来自正式 manifest。
   - 已检查 `teacher.tex` 与 `student.tex` 均存在。
   - 已检查 `lesson.yml` 字段完整。
   - 已检查学生题号与教师答案题号一致。
   - 已检查学生版无明显答案泄露。
   - 已检查教学流程总时间均为 45 分钟。
   - 已检查引用的 TikZ 文件存在。
   - 已检查 `dist/` 只包含本阶段三节样板课 PDF。

补充核验：`pdftotext` 可读取样板 PDF 文本；当前 `pdfinfo.cmd` 在本机路径下返回 “The system cannot find the path specified.”，页数以 XeLaTeX 编译日志和 `pilot_build_report.csv` 为准。

## 八、需要人工重点审核的内容

1. 三节样板课的教学容量是否适合 45 分钟课堂。
2. 学生学案留白是否满足真实书写需要。
3. 教师版答案详略是否符合备课使用习惯。
4. `C06-L07` 的角图标注位置和题目条件是否满足人工审美与课堂投影需求。
5. 当前版式是否可作为后续全册批量生成的冻结标准。
6. 教学活动和练习是否需要结合学校实际进度微调。

## 九、是否建议进入全册批量生产

从工程角度看，当前样板已具备进入批量生产前人工审核的条件：结构稳定、三类样板覆盖概念形成、方程推理和几何图形，编译与校验均通过。

建议下一步先由人工审阅 6 个 PDF 和本报告。人工确认后，再冻结 `tex/`、`templates/` 和 `scripts/validate_pilot_lessons.py` 的规则，然后进入分章批量生产。
