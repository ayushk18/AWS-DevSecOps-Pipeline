#!/usr/bin/env bash
# Pulls recent logs from the ECS CloudWatch log group and writes them to a
# local file that Promtail tails and ships into Loki.
#
# Run this manually, or on a schedule (e.g. every 5 minutes via cron / Task
# Scheduler) to keep log data flowing into Grafana.
#
# Usage: ./fetch-logs.sh

set -euo pipefail

LOG_GROUP="/ecs/aws-devsecops-pipeline"
OUTPUT_DIR="$(dirname "$0")/logs"
OUTPUT_FILE="${OUTPUT_DIR}/app.log"

mkdir -p "${OUTPUT_DIR}"

echo "Fetching logs from ${LOG_GROUP}..."
aws logs tail "${LOG_GROUP}" --since 10m --format short >> "${OUTPUT_FILE}"

echo "Done. Logs appended to ${OUTPUT_FILE}"
echo "Promtail will pick up new lines automatically."
