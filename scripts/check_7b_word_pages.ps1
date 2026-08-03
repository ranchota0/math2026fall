$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$lessonRoot = Join-Path $projectRoot 'lessons'
$outputDir = Join-Path $projectRoot 'build\7b_acceptance'
$outputCsv = Join-Path $outputDir 'word_live_page_check.csv'
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$lessonDirs = Get-ChildItem -LiteralPath $lessonRoot -Recurse -Filter 'lesson.yml' |
    ForEach-Object {
        $candidate = $_.Directory.Parent
        if ($candidate.Name -ne 'lessons') { $candidate.FullName }
    } |
    Sort-Object -Unique
$documents = foreach ($lessonDir in $lessonDirs) {
    Get-ChildItem -LiteralPath $lessonDir -Recurse -Filter '*.docx'
}
$documents = @($documents | Sort-Object FullName)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$rows = New-Object System.Collections.Generic.List[object]

try {
    $index = 0
    foreach ($file in $documents) {
        $index++
        $doc = $null
        try {
            $doc = $word.Documents.Open($file.FullName, $false, $true, $false)
            $doc.Repaginate()
            $pages = [int]$doc.ComputeStatistics(2)
            $rows.Add([pscustomobject]@{
                Docx = $file.FullName
                Pages = $pages
                Status = if ($pages -gt 0) { 'PASS' } else { 'FAIL' }
                Message = ''
            })
        }
        catch {
            $rows.Add([pscustomobject]@{
                Docx = $file.FullName
                Pages = 0
                Status = 'ERROR'
                Message = $_.Exception.Message
            })
        }
        finally {
            if ($null -ne $doc) {
                $doc.Close($false)
                [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc)
            }
        }
        if (($index % 10) -eq 0 -or $index -eq $documents.Count) {
            Write-Output "checked $index/$($documents.Count) Word files"
        }
    }
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$rows | Export-Csv -LiteralPath $outputCsv -NoTypeInformation -Encoding UTF8
$failed = @($rows | Where-Object { $_.Status -ne 'PASS' })
Write-Output "files=$($rows.Count) failed=$($failed.Count) report=$outputCsv"
if ($failed.Count -gt 0) { exit 1 }
