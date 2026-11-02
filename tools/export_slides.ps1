# 사용법: powershell -File tools/export_slides.ps1 -Pptx docs/presentation_1st.pptx -OutDir build/slides_presentation
param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$OutDir
)
$pptxFull = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null
$outFull = (Resolve-Path $OutDir).Path
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($pptxFull, $true, $true, $false)
$pres.Export($outFull, "PNG", 1280, 720)
$pres.Close()
$ppt.Quit()
