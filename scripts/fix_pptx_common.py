from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from pptx_audit_lib import pptx_files


ROOT = Path(__file__).resolve().parents[1]


def ps_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def copy_sources(input_root: Path, output_root: Path) -> list[dict]:
    output_root.mkdir(parents=True, exist_ok=True)
    jobs = []
    for src in pptx_files(input_root):
        rel = src.relative_to(input_root)
        dst = output_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        jobs.append({"source": str(src.resolve()), "target": str(dst.resolve()), "relative": str(rel)})
    return jobs


def run_powershell_editor(jobs_json: Path, log_path: Path) -> None:
    script = r"""
param([string]$JobsJson, [string]$LogPath)
$ErrorActionPreference = 'Stop'
$jobs = Get-Content -Raw -Encoding UTF8 $JobsJson | ConvertFrom-Json
$log = New-Object System.Collections.Generic.List[string]

function Add-Log($msg) {
  $script:log.Add(("$(Get-Date -Format s) " + $msg))
}

function Replace-InTextRange($tr, $repls, [string]$context) {
  if ($null -eq $tr) { return }
  $txt = $tr.Text
  if ($null -eq $txt) { return }
  $new = $txt
  foreach ($pair in $repls) {
    $key = [string]$pair[0]
    $value = [string]$pair[1]
    if ($new.Contains($key)) {
      $new = $new.Replace($key, $value)
    }
  }
  if ($new -ne $txt) {
    $tr.Text = $new
    Add-Log("text replacement in $context")
  }
}

function Replace-InShape($shape, $repls, [string]$context) {
  try {
    if ($shape.Type -eq 6) {
      for ($i = 1; $i -le $shape.GroupItems.Count; $i++) {
        Replace-InShape $shape.GroupItems.Item($i) $repls "$context/group$i"
      }
      return
    }
    if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
      Replace-InTextRange $shape.TextFrame.TextRange $repls $context
    }
  } catch {
    Add-Log("shape skipped in ${context}: $($_.Exception.Message)")
  }
}

function Replace-InSlide($slide, $repls, [string]$context) {
  for ($i = 1; $i -le $slide.Shapes.Count; $i++) {
    Replace-InShape $slide.Shapes.Item($i) $repls "$context/shape$i"
  }
  try {
    for ($i = 1; $i -le $slide.NotesPage.Shapes.Count; $i++) {
      Replace-InShape $slide.NotesPage.Shapes.Item($i) $repls "$context/notes$i"
    }
  } catch {}
}

function Slide-Text($slide) {
  $parts = New-Object System.Collections.Generic.List[string]
  for ($i = 1; $i -le $slide.Shapes.Count; $i++) {
    try {
      $s = $slide.Shapes.Item($i)
      if ($s.HasTextFrame -eq -1 -and $s.TextFrame.HasText -eq -1) {
        $parts.Add($s.TextFrame.TextRange.Text)
      }
    } catch {}
  }
  return ($parts -join "`n")
}

function Add-TextBox($slide, [double]$left, [double]$top, [double]$width, [double]$height, [string]$text, [int]$fontSize) {
  $box = $slide.Shapes.AddTextbox(1, $left, $top, $width, $height)
  $box.TextFrame.TextRange.Text = $text
  $box.TextFrame.TextRange.Font.Size = $fontSize
  $box.TextFrame.WordWrap = -1
  return $box
}

function Add-ContentSlide($pres, [int]$index, [string]$title, [string[]]$bullets, [string]$notes) {
  $slide = $pres.Slides.Add($index, 12)
  Add-TextBox $slide 48 34 840 48 $title 28 | Out-Null
  $body = ($bullets | ForEach-Object { "• " + $_ }) -join "`n"
  Add-TextBox $slide 70 115 820 360 $body 22 | Out-Null
  try {
    Add-TextBox $slide.NotesPage 40 40 620 150 $notes 14 | Out-Null
  } catch {}
  Add-Log("inserted slide '$title'")
}

function Remove-Watermark($slide, [string]$context) {
  $w = $slide.Parent.PageSetup.SlideWidth
  $h = $slide.Parent.PageSetup.SlideHeight
  for ($i = $slide.Shapes.Count; $i -ge 1; $i--) {
    $s = $slide.Shapes.Item($i)
    $delete = $false
    try {
      if ($s.HasTextFrame -eq -1 -and $s.TextFrame.HasText -eq -1 -and $s.TextFrame.TextRange.Text.Contains("豆包AI生成")) { $delete = $true }
    } catch {}
    try {
      $alt = [string]$s.AlternativeText
      if ($alt.Contains("豆包") -or $alt.Contains("AI生成")) { $delete = $true }
    } catch {}
    if (-not $delete) {
      try {
        if ($s.Left -gt $w * 0.70 -and $s.Top -gt $h * 0.78 -and $s.Width -lt 190 -and $s.Height -lt 90) {
          if ($s.Type -eq 13 -or $s.Type -eq 11) { $delete = $true }
        }
      } catch {}
    }
    if ($delete) {
      $s.Delete()
      Add-Log("removed possible watermark in $context")
    }
  }
}

$globalRepls = @(
  @('完成教材 Pxx 页 练习题', '完成教材本节练习题 1、2、3'),
  @('完成教材 PXX 页 习题 2.2', '完成教材习题 2.2'),
  @('完成教材 PXX 页 习题2.2', '完成教材习题 2.2'),
  @('完成教材 Pxx 页《习题3.1》', '完成教材《习题3.1》第1、2、3题'),
  @('比较 -3 和 -π 的大小', '比较 -3 和 -3.14 的大小'),
  @('比较-3和-π的大小', '比较 -3 和 -3.14 的大小'),
  @('张老师', '郭立华'),
  @('主讲人：XXX', ''),
  @('XXX', ''),
  @('豆包AI生成', ''),
  @('`', ''),
  @('$', ''),
  @('\frac{x+1}{2}', '(x+1)/2'),
  @('\frac{2-x}{4}', '(2-x)/4'),
  @('\frac{12}{4}', '12/4'),
  @('\frac{b}{a}', 'b/a'),
  @('\frac{1}{2}', '1/2'),
  @('\times', '×'),
  @('\(', ''),
  @('\)', ''),
  @('a^2-b/a', 'a²-b/a'),
  @('a^2 - b/a', 'a²-b/a'),
  @('AC = CB = 1/2AB = 1/2 × 10 = 5', 'AC=CB=1/2 AB=5 cm'),
  @('CD = 1/2BC = 1/2 × 5 = 2.5', 'CD=1/2 BC=2.5 cm'),
  @('ab + ac = a(b+c)', 'ab+ac=a(b+c)')
)

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = 1
foreach ($job in $jobs) {
  $path = [string]$job.target
  Add-Log("open $path")
  $pres = $ppt.Presentations.Open($path, $false, $false, $false)
  $name = [System.IO.Path]::GetFileNameWithoutExtension($path)
  try {
    for ($sidx = 1; $sidx -le $pres.Slides.Count; $sidx++) {
      $slide = $pres.Slides.Item($sidx)
      Replace-InSlide $slide $globalRepls "$name/slide$sidx"
    }
    Remove-Watermark $pres.Slides.Item($pres.Slides.Count) "$name/last"

    if ($name -eq '1.2 有理数及其大小比较') {
      if ($pres.Slides.Count -ge 4) {
        $noteText = '“一个数不是正数就是负数”这句话不对，因为0既不是正数，也不是负数。'
        try { Add-TextBox $pres.Slides.Item(4).NotesPage 40 40 620 120 $noteText 14 | Out-Null } catch {}
        Add-Log('updated 1.2 slide 4 notes')
      }
    }

    if ($name -eq '2.2') {
      if ($pres.Slides.Count -ge 5) {
        Add-TextBox $pres.Slides.Item(5) 60 120 460 150 "01  8×(-1)`n02  (-1/2)×(-2)`n03  (-2/3)×(-5/7)" 24 | Out-Null
        Add-Log('added corrected 2.2 slide 5 exercise text')
      }
    }

    if ($name -eq '2.3') {
      $insert = [Math]::Max(2, $pres.Slides.Count)
      Add-ContentSlide $pres $insert '科学记数法：大数的简洁表示' @('形式：a×10ⁿ', '条件：1≤|a|<10，n为整数', '例：696000=6.96×10⁵') '本页补齐教材同节科学记数法。'
      Add-ContentSlide $pres ($insert + 1) '科学记数法例题' @('把 3400000 写成科学记数法', '把 -120000 写成科学记数法', '把 7.05×10⁴ 还原为普通数', '课堂练习：独立完成并说明 n 的意义') '强调指数与小数点移动的关系。'
      Add-ContentSlide $pres ($insert + 2) '近似数与精确度' @('准确数、近似数与四舍五入', '精确到个位、十分位、百分位', '例：3.14159≈3.14') '补齐教材同节近似数内容。'
      Add-ContentSlide $pres ($insert + 3) '综合练习' @('计算含乘方的式子', '用科学记数法表示或还原数', '按要求取近似数') '将乘方、科学记数法和近似数合并小结。'
    }

    if ($name -eq '3.2' -and $pres.Slides.Count -ge 7) {
      Add-TextBox $pres.Slides.Item(7) 520 135 330 210 "当 a=-3，b=2 时：`na²-b/a`n=(-3)²-2/(-3)`n=9+2/3`n=29/3" 22 | Out-Null
      try { Add-TextBox $pres.Slides.Item(7).NotesPage 40 40 620 130 '右侧示范用于说明代入时先加括号，再按运算顺序计算。' 14 | Out-Null } catch {}
      Add-Log('added 3.2 slide 7 worked example')
    }

    if ($name -eq '4.1') {
      for ($sidx = 1; $sidx -le $pres.Slides.Count; $sidx++) {
        $txt = Slide-Text $pres.Slides.Item($sidx)
        if ($txt.Contains('整式是代数式的基础组成')) {
          Add-TextBox $pres.Slides.Item($sidx) 70 120 780 120 '单项式和多项式统称为整式。单项式由数或字母的积组成，多项式由若干单项式的和组成。' 24 | Out-Null
          Add-Log('added corrected definition on 4.1')
        }
      }
    }

    if ($name -eq '5.1') {
      if ($pres.Slides.Count -ge 1) {
        Add-TextBox $pres.Slides.Item(1) 60 35 620 55 '5.1 方程' 32 | Out-Null
        Add-TextBox $pres.Slides.Item(1) 70 95 620 35 '从算式到方程' 20 | Out-Null
      }
      $insert = [Math]::Max(2, $pres.Slides.Count)
      Add-ContentSlide $pres $insert '等式的基本事实' @('若 a=b，则 b=a', '若 a=b，b=c，则 a=c', '等式表达的是两个式子相等的关系') '补齐等式基本事实。'
      Add-ContentSlide $pres ($insert + 1) '等式的性质 1' @('等式两边同时加或减同一个数或式子，结果仍相等', 'a=b → a±c=b±c', '用天平图理解左右同时操作') '配合两道填空题讲解。'
      Add-ContentSlide $pres ($insert + 2) '等式的性质 2' @('等式两边同时乘同一个数，结果仍相等', '等式两边同时除以同一个非零数，结果仍相等', '除数不能为 0') '强调非零条件。'
      Add-ContentSlide $pres ($insert + 3) '利用等式的性质解方程' @('x+7=26', '-5x=20', '求出结果后代入检验') '把性质落实到解方程。'
    }

    if ($name -eq '5.2' -and $pres.Slides.Count -ge 7) {
      Add-TextBox $pres.Slides.Item(7) 520 120 330 220 "(x+1)/2-1=2+(2-x)/4`nx`nx+3`nx-3`n2(x+3)=2.5(x-3)`nx=27" 22 | Out-Null
      Add-Log('added stable ordinary math text on 5.2 slide 7')
    }

    if ($name -eq '6.2' -and $pres.Slides.Count -ge 7) {
      Add-TextBox $pres.Slides.Item(7) 500 120 360 180 "2a-b`nAC=CB=1/2 AB=5 cm`nCD=1/2 BC=2.5 cm`nAD=7.5 cm" 22 | Out-Null
      Add-Log('added stable ordinary math text on 6.2 slide 7')
    }

    if ($name -eq '6.3') {
      $insert = $pres.Slides.Count
      for ($sidx = 1; $sidx -le $pres.Slides.Count; $sidx++) {
        if ((Slide-Text $pres.Slides.Item($sidx)).Contains('角平分线')) { $insert = $sidx + 1 }
      }
      Add-ContentSlide $pres $insert '余角和补角' @('和为90°的两个角互为余角', '和为180°的两个角互为补角', '这是数量关系，不要求位置相邻') '补齐教材后续余角补角内容。'
      Add-ContentSlide $pres ($insert + 1) '余角和补角的重要性质' @('同角或等角的余角相等', '同角或等角的补角相等', '用简单等式说明性质来源') '给出简洁推导。'
      Add-ContentSlide $pres ($insert + 2) '例题与练习' @('已知一个角求余角、补角', '根据两个角的数量关系列式', '结合图形判断角度关系') '课堂练习注意图形条件。'
    }

    if ($name -eq '6.4') {
      if ($pres.Slides.Count -ge 1) {
        Add-TextBox $pres.Slides.Item(1) 60 110 520 35 '主讲人：郭立华' 20 | Out-Null
      }
      for ($sidx = 1; $sidx -le $pres.Slides.Count; $sidx++) {
        $txt = Slide-Text $pres.Slides.Item($sidx)
        if ($txt.Contains('401.26') -or $txt.Contains('起跑线前伸')) {
          $slide = $pres.Slides.Item($sidx)
          Add-TextBox $slide 50 45 820 45 '动手查一查、算一算：400米跑道' 28 | Out-Null
          Add-TextBox $slide 70 115 800 300 "• 查阅或测量标准跑道的直道长度、分道宽度和比赛测量线位置`n• 明确内沿半径不一定等于比赛测量线半径`n• 用 总长=2×直道长+2πr 验证第一分道长度`n• 用 ΔL=2πΔr 探究相邻分道弯道长度差`n• 起跑线前伸只用于补偿各分道距离差" 22 | Out-Null
          Add-Log("replaced invalid 6.4 running-track explanation on slide $sidx")
        }
      }
    }

    $pres.Save()
  } finally {
    $pres.Close()
  }
}
$ppt.Quit()
$log | Set-Content -Encoding UTF8 $LogPath
"""
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8-sig") as handle:
        handle.write(script)
        ps1 = handle.name
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, "-JobsJson", str(jobs_json), "-LogPath", str(log_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            print(completed.stdout)
            raise subprocess.CalledProcessError(completed.returncode, completed.args, completed.stdout)
    finally:
        try:
            os.unlink(ps1)
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy and conservatively revise all PPTX files.")
    parser.add_argument("--input", default="郭立华2026秋数学PPT")
    parser.add_argument("--output", default="dist/ppt_revised")
    parser.add_argument("--log", default="reports/phase4_revision_log.md")
    args = parser.parse_args()

    input_root = Path(args.input)
    output_root = Path(args.output)
    jobs = copy_sources(input_root, output_root)
    Path("build").mkdir(exist_ok=True)
    jobs_json = Path("build/phase4_ppt_jobs.json")
    jobs_json.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_log = Path("build/phase4_revision_log_raw.txt")
    run_powershell_editor(jobs_json, tmp_log)

    lines = ["# 第四阶段 PPT 修订日志", ""]
    lines.append(f"原始目录：`{input_root}`")
    lines.append(f"修订输出：`{output_root}`")
    lines.append("")
    lines.append("## 修订记录")
    if tmp_log.exists():
        for line in tmp_log.read_text(encoding="utf-8", errors="replace").splitlines():
            lines.append(f"- {line}")
    Path(args.log).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] revised {len(jobs)} pptx files into {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
