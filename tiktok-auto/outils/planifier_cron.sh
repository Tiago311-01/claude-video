#!/usr/bin/env bash
# OPTION LOCALE (macOS / Linux) — relance Claude Code toutes les 6 h sur CE dossier.
# Inutile si la tâche planifiée cloud (claude.ai) est active : ne pas activer les deux.
# Installation : bash outils/planifier_cron.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_BIN="$(command -v claude)"
LINE="7 */6 * * * cd \"$DIR\" && \"$CLAUDE_BIN\" -p \"Lis CLAUDE.md et fais un cycle\" --allowedTools \"Bash Read Write Edit Glob Grep WebSearch WebFetch\" >> \"$DIR/cache/cycles.log\" 2>&1"
mkdir -p "$DIR/cache"
( crontab -l 2>/dev/null | grep -v 'fais un cycle' ; echo "$LINE" ) | crontab -
echo "Tâche cron installée :"; crontab -l | grep 'fais un cycle'
