# Supplemental Scripts.

Certain Usint tasks are not handled by internal CLI tools operating with the application code and instead depend on additional python scripts. These scripts are located in the supplemental_scripts subdirectory and are installed in various locations on the HEAD file system.

Consult the cronjobs.md documentation file for a list of the cronjobs calling these supplemental scripts.

## Scripts

### obs_ss
This directory contains the scripts for filling the legacy /data/mta4/obs_ss data directory. When time allows, these data directory should be deprecated.

sot_data.sh runs the sot_data.sql SQL statement to fetch the data columns used for sot_answer.cgi

Needs Sybase access and ocat authentication login located at `/data/mta4/CUS/authorization`
#### Script Files
- /data/mta4/obs_ss/sot_data.sh
    - /data/mta4/obs_ss/sot_data.sql

#### Data Files
- /data/mta4/obs_ss/sot_ocat.out
- /data/mta4/obs_ss/sot_ocat_ra.out