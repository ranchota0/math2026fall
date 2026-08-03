$ErrorActionPreference = 'Stop'

$project = if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    (Get-Location).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
}
$lessonRoot = Join-Path $project 'lessons'
$reportDir = Join-Path $project 'build\7b_batch'
[System.IO.Directory]::CreateDirectory($reportDir) | Out-Null
$reportCsv = Join-Path $reportDir 'word_pdf_export.csv'

$documents = Get-ChildItem -LiteralPath $lessonRoot -Recurse -Filter '*.docx' -File |
    Where-Object {
        $_.FullName -match '\\第(07|08|09|10|11|12)章_' -and
        ($_.Name -like '*_教学设计.docx' -or $_.Name -like '*_学生学案.docx' -or $_.Name -like '*_学案教师版.docx')
    } |
    Sort-Object FullName

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$records = New-Object System.Collections.Generic.List[object]
$failed = 0
$exported = 0
$skipped = 0

try {
    foreach ($file in $documents) {
        $docxPath = $file.FullName
        $pdfPath = [System.IO.Path]::ChangeExtension($docxPath, '.pdf')
        if ([System.IO.File]::Exists($pdfPath)) {
            $records.Add([pscustomobject]@{ Docx=$docxPath; Pdf=$pdfPath; Pages=''; ExpectedPages=''; Status='SKIP_EXISTING'; Message='preserved existing output' })
            $skipped++
            continue
        }
        $doc = $null
        try {
            $doc = $word.Documents.Open($docxPath, $false, $false)
            $lessonDir = $file.Directory.Parent.FullName
            $asset = Join-Path $lessonDir '素材\diagram_topic.png'
            $marker = '[[DIAGRAM_TOPIC]]'
            while ($true) {
                $range = $doc.Content.Duplicate
                $find = $range.Find
                $find.ClearFormatting()
                $find.Text = $marker
                $find.Forward = $true
                $find.Wrap = 0
                if (-not $find.Execute()) { break }
                if (-not [System.IO.File]::Exists($asset)) { throw "Missing topic diagram: $asset" }
                $range.Text = ''
                $range.Collapse(1)
                $shape = $doc.InlineShapes.AddPicture($asset, $false, $true, $range)
                $shape.LockAspectRatio = -1
                $shape.Width = 205
            }
            $doc.Fields.Update() | Out-Null
            $doc.Repaginate()
            $doc.Save()
            $pages = [int]$doc.ComputeStatistics(2)
            $expected = if ($file.Name -like '*_教学设计.docx') { 4 } else { 3 }
            $doc.ExportAsFixedFormat($pdfPath, 17)
            $status = if ($pages -eq $expected) { 'PASS' } else { 'PAGE_MISMATCH' }
            $records.Add([pscustomobject]@{ Docx=$docxPath; Pdf=$pdfPath; Pages=$pages; ExpectedPages=$expected; Status=$status; Message='' })
            $exported++
            Write-Output "[PDF] $($file.Name) pages=$pages expected=$expected"
        }
        catch {
            $failed++
            $records.Add([pscustomobject]@{ Docx=$docxPath; Pdf=$pdfPath; Pages=''; ExpectedPages=''; Status='FAIL'; Message=$_.Exception.Message })
            Write-Output "[FAIL] $docxPath :: $($_.Exception.Message)"
        }
        finally {
            if ($doc -ne $null) {
                $doc.Close($false)
                [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc) | Out-Null
            }
        }
    }
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$records | Export-Csv -LiteralPath $reportCsv -NoTypeInformation -Encoding UTF8
$pageMismatch = @($records | Where-Object { $_.Status -eq 'PAGE_MISMATCH' }).Count
Write-Output "[SUMMARY] documents=$($documents.Count) exported=$exported skipped=$skipped failed=$failed page_mismatch=$pageMismatch report=$reportCsv"
if ($failed -gt 0) { exit 1 }
