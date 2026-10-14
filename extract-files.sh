#!/bin/bash
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

MY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ANDROID_ROOT="$(cd -- "${MY_DIR}/../../.." && pwd)"
export PYTHONPATH="${ANDROID_ROOT}/tools/extract-utils${PYTHONPATH:+:${PYTHONPATH}}"

exec python3 "${MY_DIR}/extract-files.py" "$@"
