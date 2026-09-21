"""
Example instance configuration for the CLI interface.
Locate this file (with desired customizations) inside the instance directory of the installation.
"""
import os
_PORT = os.getenv("PORT", "32119") #: Use a registered (non-ephemeral) TCP port: Range 1024-49151
_DOMAIN = os.getenv("DOMAIN", "127.0.0.1") #: Serve Locally, and Apache web server with reverse proxy to backend port.

#: Must manually set the server name for the CLI tools which use the server domain as a variable. Does not impact live web application.
SERVER_NAME = f"{_DOMAIN}:{_PORT}"
#SERVER_NAME = "cxc-test.cfa.harvard.edu/wsgi/cus/usint"
#SERVER_NAME = "cxc.cfa.harvard.edu/wsgi/cus/usint"
#SERVER_NAME = "r2d2-v.cfa.harvard.edu/wsgi/cus/usint"

#: Use http non secured for local host
#: Use http secured for apache web servers
PREFERRED_URL_SCHEME = "http"
#PREFERRED_URL_SCHEME = "https"