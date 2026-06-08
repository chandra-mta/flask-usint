# Overview

This file is meant to store individual application package installation configuration files. This means that no module in this directory is *directly used* by any python code.

Instead, this directory contains configuration files meant for individual installations of the app, located in the app's *instance* subdirectory in its file location.
For example, the cxc-test web servers will use the application package installed in the `/proj/web-cxc-dmz-test/wsgi-scripts/cus` directory.
This means that copying the `configurations/cxc_test/config.py` file into the `/proj/web-cxc-dmz-test/wsgi-scripts/cus/instance` directory will configure the application only running on cxc-test, leaving your local host, cxc-web or r2d2-v version of the usint application unchanged.