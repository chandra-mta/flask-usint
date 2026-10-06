#!/bin/bash

# Install the supplemental scripts into their respective directories

SOURCE_DIR="$(dirname "${BASH_SOURCE[0]}")"

PROJECT_ROOT="$(cd "${SOURCE_DIR}/.." && pwd)"
# Set the version variables
source "$PROJECT_ROOT/version.conf"
#: Build ISO 8601 timestamp
BUILD=$(date -u +"%Y%m%dT%H%M%SZ")

case "$1" in
  prod)
    OBS_SS_ROOT=/data/mta4/obs_ss
    USINT_ROOT=/data/mta4/CUS/www/Usint
    ;;
  home)
    OBS_SS_ROOT="$HOME/cus/obs_ss"
    USINT_ROOT="$HOME/cus/Usint"
    ;;
  *)
    echo "Usage: $0 {prod|home}"
    exit 1
    ;;
esac

#: Make the *_ROOT directories if they don't exist. (only for home setting)
mkdir -p "$OBS_SS_ROOT"
mkdir -p "$USINT_ROOT"

#: OBS_SS stage
rsync -av --delete --exclude-from="$SOURCE_DIR/deploy-exclude-supplemental.txt" "$SOURCE_DIR/obs_ss/" "$OBS_SS_ROOT/"
echo "${VERSION}+${BUILD}" > "$OBS_SS_ROOT/.version"

#: USINT stage
rsync -av --delete --exclude-from="$SOURCE_DIR/deploy-exclude-supplemental.txt" "$SOURCE_DIR/Usint/" "$USINT_ROOT/"
echo "${VERSION}+${BUILD}" > "$USINT_ROOT/.version"
