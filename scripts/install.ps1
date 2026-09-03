[CmdletBinding(SupportsShouldProcess)]
param(
    [string[]]$Skills,
    [string]$Destination = (Join-Path $env:USERPROFILE ".codex\skills")
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$manifest = @(
    "context-budget",
    "evidence-research",
    "financial-analyst",
    "memory-curator",
    "research-summarizer",
    "stock-analysis"
)

$selectedSkills = if ($Skills -and $Skills.Count -gt 0) { $Skills } else { $manifest }
$unknownSkills = @($selectedSkills | Where-Object { $_ -notin $manifest })

if ($unknownSkills.Count -gt 0) {
    throw "Unknown skills: $($unknownSkills -join ', '). Available skills: $($manifest -join ', ')"
}

if ($PSCmdlet.ShouldProcess($Destination, "创建 Codex Skills 目录")) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

foreach ($skillName in $selectedSkills) {
    $sourcePath = Join-Path $repositoryRoot $skillName
    $targetPath = Join-Path $Destination $skillName

    if (-not (Test-Path -LiteralPath (Join-Path $sourcePath "SKILL.md"))) {
        throw "技能入口不存在：$sourcePath\SKILL.md"
    }

    if ($PSCmdlet.ShouldProcess($targetPath, "安装或更新 $skillName")) {
        Copy-Item -LiteralPath $sourcePath -Destination $Destination -Recurse -Force
    }
}

Write-Host "Processed $($selectedSkills.Count) skills. Restart Codex or start a new task to reload them."
