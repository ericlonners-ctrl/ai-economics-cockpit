#!/usr/bin/env bash
set -euo pipefail

python3 -m ai_economics_cockpit all --online
mkdir -p _site
cp -R dashboard _site/dashboard
mkdir -p _site/data/processed
cp data/processed/dashboard_payload.json _site/data/processed/dashboard_payload.json
cp artifacts/latest_dashboard_build_report.md _site/latest_dashboard_build_report.md
printf %s '<!doctype html><meta http-equiv=refresh content=0;url=/dashboard/>' > _site/index.html
