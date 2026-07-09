#!/bin/bash

#!/bin/bash

case "$1" in
  prod)
    APP_ROOT=/proj/web-cxc/wsgi-scripts/cus
    ;;
  test)
    APP_ROOT=/proj/web-cxc-dmz-test/wsgi-scripts/cus
    ;;
  *)
    echo "Usage: $0 {prod|test}"
    exit 1
    ;;
esac

rsync -av --delete --exclude-from=deploy-exclude.txt ./ "$APP_ROOT/"