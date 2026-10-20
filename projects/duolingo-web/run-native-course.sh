#!/usr/bin/env bash
# Build failure must never fall through to an old candidate binary.
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo 'Usage: run-native-course.sh FRESH_OUTPUT_DIR FIXTURE [observer flags...]' >&2
  exit 2
fi
project_root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$project_root"
output_dir="$1"
fixture="$2"
shift 2
if [[ -e "$output_dir/progress.json" ]]; then
  echo 'Choose a fresh output directory; existing evidence is preserved.' >&2
  exit 2
fi
mkdir -p "$output_dir"
swift build --package-path projects/education-swift --product LingoSeed
swiftc projects/duolingo-web/observe-frontend.swift -o "$output_dir/observe-frontend"
exec "$output_dir/observe-frontend" "$output_dir" "$fixture" "$@"
