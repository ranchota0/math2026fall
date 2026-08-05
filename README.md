# 人教版七年级数学上册教学资源

我是陶圣叶

本项目用于长期维护“人教版七年级数学上册逐课时教学设计与学生学案”。后续每一个实际教学课时将分别生成教师教学设计和学生配套学案两个独立 XeLaTeX 文件。

当前阶段只完成基础设施：目录结构、配置文件、LaTeX 公共组件、Jinja2 模板、示例占位文件和检查脚本。`lessons/_sample` 仅用于验证工程流程，不能用于课堂教学。

## 教材文件

教材 PDF 是唯一教材版本依据。确认教材后，应放置或复制为：

```text
references/textbook.pdf
```

不要修改教材 PDF。教材 PDF 是否加入 Git 由团队自行决定；若文件较大或版权不允许，建议不提交 PDF，只提交 `references/source_info.md`。

## 推荐环境

- Python 3.10 或更高版本
- TeX Live 或 MiKTeX
- XeLaTeX
- latexmk

## 安装依赖

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 基本使用

检查环境：

```bash
python scripts/check_environment.py
```

验证项目：

```bash
python scripts/validate_project.py
```

渲染示例：

```bash
python scripts/render_lesson.py
```

编译示例和冒烟测试：

```bash
python scripts/compile_all.py
```

生成编译报告：

```bash
python scripts/generate_report.py
```

如果当前系统没有 `python` 命令，可尝试 `py` 或 `python3`。

## 输出目录

- `build/`：临时渲染和编译产物。
- `dist/tex/`：后续正式导出的独立 `.tex` 文件。
- `dist/pdf/`：后续正式导出的 PDF 文件。
- `logs/`：编译日志与检查日志。
- `reports/`：项目报告、编译报告和审核清单。

当前 sample 文件只输出到 `build/sample/`，不会进入正式 `dist/`。

## 后续正式流程

1. 确认 `references/textbook.pdf` 的教材版本。
2. 基于教材建立正式课时清单。
3. 人工审核课时边界。
4. 制作一个黄金样板课时。
5. 分章批量生成、编译和审核。

不得在未确认教材和课时清单前生成正式课程内容。
