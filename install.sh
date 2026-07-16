#!/bin/bash

SOURCE_DIR="$(dirname "${BASH_SOURCE[0]}")"

case "$1" in
  prod)
    APP_ROOT=/proj/web-cxc/wsgi-scripts/cus
    ;;
  test)
    APP_ROOT=/proj/web-cxc-dmz-test/wsgi-scripts/cus
    ;;
  r2d2)
    APP_ROOT=/proj/web-r2d2-v/wsgi-scripts/cus
    ;;
  home)
    APP_ROOT="$HOME/cus"
    ;;
  *)
    echo "Usage: $0 {prod|test|r2d2|home}"
    exit 1
    ;;
esac

#: Make the APP_ROOT directory if it doesn't exist. (only for home setting)
mkdir -p $APP_ROOT
rsync -av --delete --exclude-from="$SOURCE_DIR/deploy-exclude.txt" "$SOURCE_DIR/" "$APP_ROOT/"