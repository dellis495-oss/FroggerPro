#!/usr/bin/env bash
# CP2A build with bounded host concurrency and explicit Go resource controls.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../../.."
export GOMEMLIMIT="${GOMEMLIMIT:-14GiB}"
export GOGC="${GOGC:-50}"
export FROGGER_BUILD_JOBS="${FROGGER_BUILD_JOBS:-8}"
export GOMAXPROCS="${GOMAXPROCS:-$FROGGER_BUILD_JOBS}"
cpu_list=$(python3 -c 'import os; print(",".join(map(str, sorted(os.sched_getaffinity(0))[:int(os.environ["FROGGER_BUILD_JOBS"])])))')
if [ "$#" -eq 0 ]; then set -- bacon; fi
exec taskset -c "$cpu_list" nice -n 5 bash -c '
  source build/envsetup.sh &&
  lunch lineage_FroggerPro-cp2a-userdebug &&
  m -j"$FROGGER_BUILD_JOBS" "$@"
' frogger-build "$@"
