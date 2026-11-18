# OPTION LOCALE (Windows) — relance Claude Code toutes les 6 h sur CE dossier.
# Inutile si la tâche planifiée cloud (claude.ai) est active : ne pas activer les deux.
# Installation (PowerShell) : powershell -ExecutionPolicy Bypass -File outils\planifier_windows.ps1
$Dir = Split-Path -Parent $PSScriptRoot
$Claude = (Get-Command claude -ErrorAction Stop).Source
New-Item -ItemType Directory -Force -Path "$Dir\cache" | Out-Null
$Cmd = "Set-Location '$Dir'; & '$Claude' -p 'Lis CLAUDE.md et fais un cycle' --allowedTools 'Bash Read Write Edit Glob Grep WebSearch WebFetch' *>> '$Dir\cache\cycles.log'"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command `"$Cmd`""
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName "TikTok-Auto-Cycle" -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null
Write-Host "Tâche 'TikTok-Auto-Cycle' installée (toutes les 6 h)."
