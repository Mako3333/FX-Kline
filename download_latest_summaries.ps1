#!/usr/bin/env pwsh

# 最新の Daily OHLC Analysis のサマリーを取得して、
# プロジェクト直下の summary_reports を最新化するだけのシンプルスクリプト。

$ErrorActionPreference = "Stop"

# このスクリプトが置かれているディレクトリ（= プロジェクトルート）に移動
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "🔍 最新のワークフロー実行を取得中..." -ForegroundColor Cyan
$runId = gh run list --workflow=daily_ohlc_analysis.yml --limit 1 --json databaseId --jq '.[0].databaseId'

if (-not $runId) {
    Write-Host "❌ 実行が見つかりませんでした" -ForegroundColor Red
    exit 1
}

$artifactName = "ohlc-daily-$runId"
Write-Host "✅ 実行ID: $runId (artifact: $artifactName)" -ForegroundColor Green

# 一時ダウンロード先
$tempDir = Join-Path $root "download_$runId"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# 一時ディレクトリ内でアーティファクトをダウンロード
Push-Location $tempDir
Write-Host "📥 アーティファクトをダウンロード中..." -ForegroundColor Cyan
$downloadOutput = gh run download $runId --repo Mako3333/FX-Kline --name $artifactName 2>&1
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -ne 0) {
    Write-Host "❌ gh run download が失敗しました" -ForegroundColor Red
    Write-Host $downloadOutput -ForegroundColor Red
    exit $exitCode
}

# summary_reports の場所を特定
# パターン1: download_{runId}/summary_reports
$artifactSummary = Join-Path $tempDir "summary_reports"

# パターン2: download_{runId}/ohlc-daily-{runId}/summary_reports
if (-not (Test-Path $artifactSummary)) {
    $artifactSummary = Join-Path $tempDir "$artifactName/summary_reports"
}

if (-not (Test-Path $artifactSummary)) {
    Write-Host "❌ アーティファクト内に summary_reports が見つかりません" -ForegroundColor Red
    Write-Host "  探索パス候補:" -ForegroundColor Yellow
    Write-Host "    " (Join-Path $tempDir "summary_reports") -ForegroundColor Yellow
    Write-Host "    " (Join-Path $tempDir "$artifactName/summary_reports") -ForegroundColor Yellow
    exit 1
}

# 既存の summary_reports を置き換え
if (Test-Path (Join-Path $root "summary_reports")) {
    Remove-Item -Path (Join-Path $root "summary_reports") -Recurse -Force
}
Copy-Item -Path $artifactSummary -Destination (Join-Path $root "summary_reports") -Recurse -Force

Write-Host "✅ 最新のサマリーを summary_reports/ に展開しました" -ForegroundColor Green
