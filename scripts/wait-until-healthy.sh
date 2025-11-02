#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

set -o errexit -o nounset -o pipefail # "strict mode"

script_path="$(realpath -- "${BASH_SOURCE[0]}")" || exit $?
declare -r script_name="${script_path##*/}"

declare -r -A log_levels=([DEBUG]=1 [INFO]=2 [WARN]=3 [ERROR]=4)
apprise() {
  if ((${log_levels[$level]} >= log_level)); then
    printf >&2 "[%s] %s\n" "$1" "$2"
  fi
}

declare -i max_wait=60
declare -i poll_interval=1
declare -i log_level=2

declare -r description="\
Description:
  Polls 'docker compose ps' until all services are healthy.
"

declare -r usage="\
Usage:
  $script_name --help
  $script_name [OPTIONS]

Options:
  -h, --help       Show this message and exit.
  -t, --timeout    Max total number of seconds to wait (default: $max_wait).
  -p, --poll       Time to wait between successive checks (default: $poll_interval).
  -v  --verbose    Decrement log level threshold, repeatable (default level: INFO).
  -q  --quiet      Increment log level threshold, repeatable (default level: INFO).
"

while (($# > 0)); do
  case "$1" in
    --)
      break
      ;;
    -h | --help)
      printf '%s\n%s\n%s\n' "$script_name" "$description" "$usage"
      exit 0
      ;;
    --timeout=*)
      max_wait="${1#--timeout=}"
      ;;
    -t | --timeout)
      max_wait="$2"
      shift
      ;;
    --poll=*)
      poll_interval="${1#--poll=}"
      ;;
    -p | --poll)
      poll_interval="$2"
      shift
      ;;
    -v | --verbose)
      ((log_level--))
      ;;
    -q | --quiet)
      ((log_level++))
      ;;
    *)
      apprise ERROR "Unexpected argument: '$1'\n\n$usage\n"
      exit 2
      ;;
  esac
done

check_health() {
  # Example `docker compose ps` output:
  # NAME  IMAGE     COMMAND     SERVICE   STATUS              PORTS
  # db   mongo:8   docker-...  mongo     running (healthy)   0.0.0.0:8000->8000/tcp
  local ps_output
  ps_output=$(docker compose ps >&2 || return $?) # Fail this function if this fails.
  # Count lines after the header that don't contain "running (healthy)".
  tail -n +2 <<< "$ps_output" | grep --count --invert-match --fixed-strings "running (healthy)"
}

check_until() {
  local -i max_wait=$1
  local -i poll_interval=$2
  apprise INFO "⏳ Waiting (max $max_wait s) for Docker services to become healthy..."
  local -i waited=0, wait_for=0, n_unhealthy=0
  while true; do
    apprise DEBUG "⏵ Checking health status at $waited s..."
    # Assume the check itself takes no time.
    n_unhealthy=$(check_health || return $?)
    if ((n_unhealthy == 0)); then
      apprise INFO "✅ All services are healthy."
      return 0
    elif ((waited > max_wait)); then
      apprise ERROR "❌ Timeout: $n_unhealthy services not healthy at $max_wait s."
      apprise INFO "$ps_output"
      return 1
    else
      apprise DEBUG "$n_unhealthy service(s) not healthy at $waited s."
    fi
    wait_for=$((waited - max_wait < poll_interval ? waited - max_wait : poll_interval))
    sleep $wait_for
    waited=$((wait_for + 1))
  done
}

check_until $max_wait $poll_interval || exit $?
