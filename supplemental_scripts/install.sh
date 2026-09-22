#!/bin/bash

# Install the supplemental scripts into their respective directories

SOURCE_DIR="$(dirname "${BASH_SOURCE[0]}")"

case "$1" in
  prod)
    OBS_SS_ROOT=/data/mta4/obs_ss
    ;;
  home)
    OBS_SS_ROOT="$HOME/cus"
    ;;
  *)
    echo "Usage: $0 {prod|home}"
    exit 1
    ;;
esac

#: Make the *_ROOT directories if they don't exist. (only for home setting)
mkdir -p $OBS_SS_ROOT

#: OBS_SS stage
rsync -av --delete --exclude-from="$SOURCE_DIR/deploy-exclude-supplemental.txt" "$SOURCE_DIR/obs_ss/" "$OBS_SS_ROOT/"
