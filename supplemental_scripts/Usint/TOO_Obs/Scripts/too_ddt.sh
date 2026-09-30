#!/bin/bash

${USINT_ROOT}/TOO_Obs/Scripts/update_tooddt_prop_list.py

${USINT_ROOT}/TOO_Obs/Scripts/update_obs_lists.py

${USINT_ROOT}/TOO_Obs/Scripts/new_too_ddt_notifier.py

chgrp mtagroup ${USINT_ROOT}/ocat/Info_save/too_contact_info/ddt_list 
chgrp mtagroup ${USINT_ROOT}/ocat/Info_save/too_contact_info/too_list 
chgrp mtagroup ${USINT_ROOT}/ocat/Info_save/too_contact_info/propno_poc_list 
chgrp mtagroup ${USINT_ROOT}/ocat/Info_save/too_contact_info/new_obs_list 
chgrp mtagroup ${USINT_ROOT}/ocat/Info_save/too_contact_info/obs_in_30days 
chgrp mtagroup ${USINT_ROOT}/ocat/Info_save/too_contact_info/new_obs_list.txt
