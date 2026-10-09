#!/usr/bin/env bash
# Turns incident_events.json (written by monitor.py) into GitHub issues:
# one issue opens when an incident opens, and closes when it resolves.
# Needs: gh (authenticated via GH_TOKEN) and jq. Both are preinstalled on
# GitHub's ubuntu runners.
set -euo pipefail

EVENTS="${1:-incident_events.json}"
STATUS_URL="https://serolinen.github.io/chaski-link/status.html"

if [ ! -f "$EVENTS" ]; then
  echo "No events file; nothing to notify."
  exit 0
fi

central() {  # UTC 'YYYY-MM-DD HH:MM:SS' -> Central time, falls back to the raw string
  TZ=America/Chicago date -d "$1 UTC" '+%Y-%m-%d %I:%M %p %Z' 2>/dev/null || echo "$1 UTC"
}

jq -c '.opened[]' "$EVENTS" | while read -r e; do
  id=$(jq -r '.Incident_ID' <<<"$e")
  server=$(jq -r '.Server' <<<"$e")
  severity=$(jq -r '.Severity' <<<"$e")
  start=$(jq -r '.Start_Time' <<<"$e")
  reading=$(jq -r '.Reading' <<<"$e")
  gh issue create \
    --title "Incident #$id: $server $severity" \
    --body "**$server** is **$severity** (reading: \`$reading\`).

Started: $(central "$start")

This issue closes automatically when the server recovers.
Status page: $STATUS_URL"
done

jq -c '.closed[]' "$EVENTS" | while read -r e; do
  id=$(jq -r '.Incident_ID' <<<"$e")
  server=$(jq -r '.Server' <<<"$e")
  end=$(jq -r '.End_Time' <<<"$e")
  duration=$(jq -r '.Duration_Minutes' <<<"$e")
  number=$(gh issue list --state open --limit 100 --json number,title \
    --jq "[.[] | select(.title | startswith(\"Incident #$id: \")) | .number] | first // empty")
  if [ -n "$number" ]; then
    gh issue close "$number" \
      --comment "Resolved. **$server** recovered at $(central "$end") after $duration minutes."
  else
    echo "No open issue found for incident #$id; skipping."
  fi
done
