#!/usr/bin/env bash
set -euo pipefail

# Static assemble only — no pip/python on Vercel (PEP 668 / uv-managed env).
# Payload is committed at data/processed/dashboard_payload.json for offline deploys.
mkdir -p _site
rm -rf _site/dashboard
cp -R dashboard _site/dashboard
mkdir -p _site/data/processed
cp data/processed/dashboard_payload.json _site/data/processed/dashboard_payload.json
# Also under /dashboard/ so either relative or absolute fetch works
mkdir -p _site/dashboard/data/processed
cp data/processed/dashboard_payload.json _site/dashboard/data/processed/dashboard_payload.json
if [[ -f artifacts/latest_dashboard_build_report.md ]]; then
  cp artifacts/latest_dashboard_build_report.md _site/latest_dashboard_build_report.md
fi
test -f _site/data/processed/dashboard_payload.json
test -f _site/dashboard/index.html
printf %s '<!doctype html><meta http-equiv=refresh content=0;url=/dashboard/>' > _site/index.html
echo "vercel_build: assembled _site with dashboard + payload"
