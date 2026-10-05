# Check TOO/DDT observations and update related information

Dir: /data/mta4/CUS/www/Usint/TOO_Obs
also see: https://cxc.cfa.harvard.edu/mta_days/mta_script_list/USINT/ti_too_ddt_update.html

## Scripts:

too_ddt_wrap_script
too_ddt_main_script         --- control scripts

update_obs_lists.py         --- find triggered ddt/too and update related files
                                input:  <obs_ss>/sot_ocat.out
                                        <too_dir>/special_obsid_poc_list
                                output: <too_dir>/too_list
                                        <too_dir>/ddt_list
                                        <too_dir>/new_obs_list
                                        <too_dir>/new_obs_list.txt
                                        <too_dir>/obs_in_30days

new_too_ddt_notifier.py     --- notify poc that they got new ddt/too observations
                                input : <too_dir>/too_list
                                        <too_dir>/ddt_list
                                output: email to poc

update_tooddt_prop_list.py  --- update tooddt_prop_obsid_list/propno_poc_list
                                input:  /proj/web-icxc/htdocs/uspp/TOO/cycle*_toos.html
                                        <obs_ss>/sot_ocat.out
                                        <too_dir>/new_obs_list
                                        saql bdatabase access (see readSQL.py)
                                output: <too_dir>/tooddt_prop_obsid_list
                                        <too_dir>/propno_poc_list

read_sql.py                  --- read data from sql database
                                input: obsid

                                output :(group_id, pre_id, pre_min_lead, pre_max_lead, grating, type, instrument,   \
                                obs_ao_str, status, seq_nbr, ocat_propid, soe_st_sched_date, lts_lt_plan,targname)

DBI.py                      --- Ska.DBI:  methods for database access and data insertion


## Directories:

'/data/mta4/obs_ss/':                                           obs_ss
'/data/mta4/CUS/authorization/':                           pass_dir
'/data/mta4/CUS/www/Usint/ocat/Working_dir/cus/':               ctemp_dir
'/data/mta4/CUS/www/Usint/ocat/Working_dir/http/':              htemp_dir
'/data/mta4/CUS/www/Usint/ocat/Working_dir/mta/':               mtemp_dir
'/data/mta4/CUS/www/Usint/ocat/Info_save/':                     data_dir
'/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/':    too_dir
'/data/mta4/CUS/www/Usint/ocat/house_keeping/':                 house_keeping
'/data/mta4/CUS/www/Usint/ocat/':                               ocat_dir
'/data/mta4/CUS/www/Usint/':                                    cusdir
'/usr/bin/':                                                    op_dir
'/data/mta4/CUS/www/Usint/TOO_Obs':                             bin_dir
'/data/mta/Script/Python3.6/MTA/':                              mta_dir


## Input

<obs_ss>/sot_cat.out                --- ascii version of sql database
sql database                        --- accessed by readSQL.py
<too_dir>/special_obsid_poc_list    --- special assignment of poc to obsids


## Output

In: <too_dir>

too_list                --- a list of too observations, recently observed, scheduled, or unobserved.
                            Example:
                            too 502978  20279   unobserved  vkashyap    19  Jun 27 2018 12:00AM

ddt_list                --- a list of ddt observations, recently observed, scheduled, or unobserved.

new_obs_list            --- a list of all observations

new_obs_list.txt        --- same as above but with the headers

tooddt_prop_obsid_list  --- a list of proposal number <--> obsids under that proposal number
                            Example:
                            18400411<>19599:19600:19601:19602:19603

propno_poc_list         --- a list of proposal numbers and poc ids connected to that proposal number
                            if POC is not assigned, TBD is assigned. all entries are either too or ddt 
                            Example:
                            18400411<>jeanconn
