param(
    [Parameter(Mandatory=$true)][string]$DocxPath,
    [Parameter(Mandatory=$true)][string]$PdfPath,
    [Parameter(Mandatory=$true)][string]$AssetRoot
)

$ErrorActionPreference = 'Stop'

$resolvedDocx = (Resolve-Path -LiteralPath $DocxPath).Path
$resolvedAssets = (Resolve-Path -LiteralPath $AssetRoot).Path
$resolvedPdf = [System.IO.Path]::GetFullPath($PdfPath)
$pdfDirectory = [System.IO.Path]::GetDirectoryName($resolvedPdf)
if (-not [System.IO.Directory]::Exists($pdfDirectory)) {
    [System.IO.Directory]::CreateDirectory($pdfDirectory) | Out-Null
}

$replacements = @(
    @{ Marker = '[[DIAGRAM_ABCD]]'; File = [System.IO.Path]::Combine($resolvedAssets, 'diagram_abcd.png'); Width = 205 },
    @{ Marker = '[[DIAGRAM_NUMBERED]]'; File = [System.IO.Path]::Combine($resolvedAssets, 'diagram_numbered.png'); Width = 205 },
    @{ Marker = '[[DIAGRAM_TOPIC]]'; File = [System.IO.Path]::Combine($resolvedAssets, 'diagram_topic.png'); Width = 205 }
)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $null
try {
    $doc = $word.Documents.Open($resolvedDocx, $false, $false)
    foreach ($replacement in $replacements) {
        while ($true) {
            $range = $doc.Content.Duplicate
            $find = $range.Find
            $find.ClearFormatting()
            $find.Text = $replacement.Marker
            $find.Forward = $true
            $find.Wrap = 0
            if (-not $find.Execute()) { break }
            if (-not [System.IO.File]::Exists($replacement.File)) {
                throw "Diagram marker $($replacement.Marker) found but asset is missing: $($replacement.File)"
            }
            $range.Text = ''
            $range.Collapse(1)
            $shape = $doc.InlineShapes.AddPicture($replacement.File, $false, $true, $range)
            $shape.LockAspectRatio = -1
            $shape.Width = $replacement.Width
        }
    }
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    $doc.Save()
    $pages = $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat($resolvedPdf, 17)
    Write-Output "[OK] $resolvedDocx -> $resolvedPdf pages=$pages"
}
finally {
    if ($doc -ne $null) { $doc.Close($false) }
    $word.Quit()
    if ($doc -ne $null) { [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc) | Out-Null }
    [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
