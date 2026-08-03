# 北京市和平街第一中学课时教学设计 LaTeX 模板

## 文件

- `tex/hepingjie_lessonplan.cls`：模板类文件。
- `templates/hepingjie_lessonplan/blank.tex`：与纸质表格对应的四页空白模板。
- `templates/hepingjie_lessonplan/example.tex`：填写方式示例。
- `dist/templates/hepingjie_lessonplan_blank.pdf`：空白模板编译预览。
- `dist/templates/hepingjie_lessonplan_example.pdf`：示例编译预览。

## 编译

要求使用 XeLaTeX。项目根目录执行：

```bash
TEXINPUTS=tex//: xelatex -interaction=nonstopmode -halt-on-error \
  -output-directory=dist/templates \
  templates/hepingjie_lessonplan/blank.tex

TEXINPUTS=tex//: xelatex -interaction=nonstopmode -halt-on-error \
  -output-directory=dist/templates \
  templates/hepingjie_lessonplan/example.tex
```

## 新建一份教案

复制 `example.tex`，然后修改：

```tex
\lessonplansetup{
  topic         = {课题名称},
  type          = {新授课/复习课/习题课},
  chapter-total = {单元总课时},
  topic-hours   = {本课题课时},
  lesson-no     = {本节是第几课时},
  year          = {2026},
  month         = {9},
  day           = {10},
  record-page   = {1}
}
```

正文依次调用：

```tex
\MakeLessonOverview{教学目标}{教学重点}{教学难点}{教学方法}{教学手段}{板书设计}
\MakeTeachingProcessPage{教师活动}{学生活动}{估时}
\MakeTeachingProcessPage{教师活动}{学生活动}{估时}
\MakeTeachingProcessReflectionPage{教师活动}{学生活动}{估时}{课后反思}
```

## 批量生成建议

后续每节课单独保存一个 `.tex` 文件，共用同一个类文件。建议目录：

```text
lessons/<课时编号>/lesson_plan.tex
tex/hepingjie_lessonplan.cls
```

编译脚本只需为每个课时设置 `TEXINPUTS=tex//:`，即可统一调用类文件。

## 设计说明

- A4 纵向，四页结构。
- 第1页：课题信息、目标、重点、难点、方法、手段、板书设计。
- 第2—3页：教学过程。
- 第4页：教学过程与课后反思。
- 页面尺寸与栏目比例按用户提供的和平街第一中学纸质表格照片复刻。
- 所有内容区采用固定高度，以保持学校标准格式；若内容过多，应精简或调整字号，不应无限扩展表格。
