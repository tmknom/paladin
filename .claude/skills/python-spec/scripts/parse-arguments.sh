#!/usr/bin/env bash
#
# parse-arguments.sh - Parse python-spec arguments and output JSON
#
# Usage: parse-arguments.sh "$1"
#
# Parses arguments:
# - $1: module-path (required) - モジュールのパス (例: src/xxxx/extract)
#
# Output: JSON object with parsing results
# Error: Exits with code 1 and error message to stderr

set -euo pipefail

# Input validation
if [ $# -lt 1 ] || [ -z "$1" ]; then
  echo "Error: module-path is required" >&2
  exit 1
fi

module_path="$1"

# Validate path exists
if [ ! -d "$module_path" ]; then
  echo "Error: directory not found: $module_path" >&2
  exit 1
fi

# Extract module name by removing "src/<project>/" prefix
# src/xxxx/yyyy -> yyyy
# src/xxxx/yyyy/zzzz -> yyyy/zzzz
module_name="$(echo "$module_path" | sed 's|^src/[^/]*/||')"

# Compute output paths
requirements_path="docs/specs/${module_name}/requirements.md"
design_path="docs/specs/${module_name}/design.md"

# Determine mode for each document
if [ -f "$requirements_path" ]; then
  requirements_mode="modify"
else
  requirements_mode="create"
fi

if [ -f "$design_path" ]; then
  design_mode="modify"
else
  design_mode="create"
fi

# Generate JSON output
cat <<EOF
{
  "module_path": "$module_path",
  "module_name": "$module_name",
  "requirements_path": "$requirements_path",
  "design_path": "$design_path",
  "requirements_mode": "$requirements_mode",
  "design_mode": "$design_mode"
}
EOF
