# Cronjobs

Note that the following cronjobs reflect system needs for the v1.1 to v2.1 transition. These will need to be updated and reformatted
once the v2.1 application version is live.


**cus@r2d2-v**
```
# Crontab Environment Variables
ENV_CUS=/proj/sot/mta/envs/python_web_apps
USINT_APPLICATION_ROOT=/proj/web-cxc/wsgi-scripts/cus
USINT_ROOT=/data/mta4/CUS/www/Usint
OBS_SS_ROOT=/data/mta4/obs_ss

# TOO Schedule Related

#: Add rolling schedule horizon and update upcoming order to the TOO schedule
0 2 * * * cd ${USINT_APPLICATION_ROOT}; ${ENV_CUS}/bin/python cli.py schedule maintain-schedule >> ${HOME}/Logs/too_contact.cron 2>&1

#: Legacy script for text files of too ddt information.
50 *  * * * cd ${USINT_ROOT}/TOO_Obs/Scripts; ${USINT_ROOT}/TOO_Obs/Scripts/too_ddt.sh >> ${HOME}/Logs/too_ddt_update.cron

# Usint Related

#: Sync the test usint database with the live usint database.
30 3 * * * cd ${USINT_APPLICATION_ROOT}; ${ENV_CUS}/bin/python cli.py database sync-test-database -f >> ${HOME}/Logs/sync_test_usint_database.cron 2>&1

#: Send out Signoff Reminder emails
0 4 * * 0-6 cd ${USINT_APPLICATION_ROOT}; ${ENV_CUS}/bin/python cli.py signoffs send-reminder-emails >> ${HOME}/Logs/signoff_request.cron 2>&1

#: Usint Revision Archive Webpages. Nonfunctional as of 2026-09-30. Needs refactor to v2.1 usint.db paradigm.
#20 2,10,12,14,16,18,20 * * * cd ${USINT_ROOT}; ${USINT_ROOT}/updated_fill_wrap_script  > ${HOME}/Logs/updated_fill_cus.cron 2>&1

# obs_ss Related

#: Writes the sot_ocat.out and sot_ocat_ra.out files to /data/mta4/obs_ss
30 * * * * cd ${OBS_SS_ROOT}/; ${OBS_SS_ROOT}/sot_data.sh >> ${HOME}/Logs/sot_data.cron 2>&1

#: Read MP Long Term Web Page and Extract OBSID and Planned Roll Angle
8 1 * * * cd ${OBS_SS_ROOT}; ${ENV_CUS}/bin/python find_planned_roll.py >> ${HOME}/Logs/find_planned_roll.cron 2>&1

#: Find the scheduled obsids through the MP OR Logs.
35 * * * * cd ${OBS_SS_ROOT}/; ${ENV_CUS}/bin/python find_scheduled_obs.py >> ${HOME}/Logs/find_scheduled_obs.cron 2>&1

#: Create the legacy files
*/10 * * * * cd ${USINT_ROOT}; ${ENV_CUS}/bin/python legacy_usint_files.py >> ${HOME}/Logs/legacy_usint_files.cron 2>&1
*/10 * * * * cd ${USINT_ROOT}; ${ENV_CUS}/bin/python legacy_too_files.py >> ${HOME}/Logs/legacy_too_files.cron 2>&1
```