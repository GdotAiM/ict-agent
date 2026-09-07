
## Deploy Configuration (configured by /setup-deploy)
- Platform: GitHub Actions (cron-based)
- Production URL: N/A (CLI tool, no web server)
- Deploy workflow: .github/workflows/ict-agent-weekly.yml
- Deploy status command: GitHub Actions run status
- Merge method: squash
- Project type: CLI trading agent
- Post-deploy health check: N/A

### Custom deploy hooks
- Pre-merge: `python -m pytest` (when tests exist)
- Deploy trigger: automatic on push to main OR manual dispatch
- Deploy schedule: Mon 06:30 UTC (forward test), Fri 14:30 UTC (TGIF), daily 06:55 UTC (pre-London)
- Health check: N/A (no web endpoint)
- Artifacts: session JSONL files uploaded to GitHub Actions artifacts for 14 days
