# Cronjobs

Note that the following cronjobs reflect system needs for the v1.1 to v2.1 transition. These will need to be updated and reformatted
once the v2.1 application version is live.


**cus@r2d2-v**
```
#: Add rolling schedule horizon to the TOO schedule
#: Disabled at the moment as the __migrate_old_database.py script overrides the schedule table with our live production data set
#: which means that we don't need this job to add new weekly sign-up periods.
#0 2 * * * cd /proj/web-cxc-dmz-test/wsgi-scripts/cus; /proj/sot/mta/envs/python_web_apps/bin/python cli.py schedule maintain-schedule

#: Update the v2.1 usint.db database to reflect the usint revision database used by the production v1.1 application.
#: This script will not need to be used following the transition of the production to v2.1
17 3 * * * cd /proj/web-cxc-dmz-test/wsgi-scripts/cus; /proj/sot/mta/envs/python_web_apps/bin/python __migrate_old_database.py

#: Sync the test usint database with the live usint database.
30 3 * * * cd /proj/web-cxc-dmz-test/wsgi-scripts/cus; /proj/sot/mta/envs/python_web_apps/bin/python cli.py database sync-test-database -f
```