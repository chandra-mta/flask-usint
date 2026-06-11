# Target Search

This is the legacy target search web interface operating with a Perl CGI frontend framework.
For this script to operate, special considerations must be made to ensure that the Perl database connection library can interpret the file containing the password authenticating our database connection. However, we cannot control the apache web server file permissions, password settings, nor can we locate the password file inside a file location downstream of the web server root.

## Installation Locations

*Note slight differences in cgi-bin and cgi-gen.*

- **Directory:** /proj/web-cxc/cgi-bin/target_search
    - **Link:** https://cxc.cfa.harvard.edu/cgi-bin/target_search/search.html

- **Directory:** /proj/web-icxc/cgi-bin/target_search
    - **Link:** https://icxc.cfa.harvard.edu/cgi-bin/target_search/search.html

- **Directory:** /proj/web-cxc-dmz-test/cgi-gen/target_search
    - **Link:** https://cxc-test.cfa.harvard.edu/cgi-gen/target_search/search.html