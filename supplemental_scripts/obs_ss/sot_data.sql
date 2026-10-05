
/* 
 * GET INFORMATION IN AXAFOCAT + PI NAME, PROPOSAL #, AND TITLE FROM 
 * PROPOSAL DB WHICH NEEDED FOR SOT_ANSWER.CGI
 * THIS IS A SLIMMED VERSION OF JOHN.SQL IN /data/udoc2/targets/
 *
 * THIS SQL SCRIPT IS MAINTAINED BY W. Aaron (william.sao.si.edu)
 *
 * LAST UPDATE DEC 15, 2016
 *
 */ 

use axafocat;

/* CREATE ONE BIG TABLE WITH ALL THE COLUMNS FROM TARGET, HRCPARAM,
 ACISPARAM, AND PHASEREQ SIM */ 

create table #sot_ocat ( 
/* 
 *TARGET COLUMNS 
 */ 
	obsid int NULL,
	targid int NULL,
	seq_nbr nchar(6) NULL,
	targname varchar(50) NULL,
	obj_flag varchar(1) NULL,
	object varchar(12) NULL,
	ra float NULL,
	dec float NULL,
	approved_exposure_time float NULL,
	ocat_propid int NULL,
	grating varchar(5) NULL,
	instrument varchar(7) NULL,
	soe_st_sched_date datetime NULL,
	type varchar(30) NULL,
	lts_lt_plan datetime NULL,
	status varchar(20) NULL,
/* 
 *FROM PROPOSAL DB
 */ 
	PI_name varchar(27) NULL,
	Observer varchar(27) NULL,
	proposal_number varchar(10) NULL,
	proposal_title varchar(120) NULL,
	ao_string varchar(10) NULL,
	joint_flag varchar(20) NULL);
/* 
 *INSERT TARGET STUFF IN TABLE
 */
insert #sot_ocat ( 
	obsid,
	targid,
	seq_nbr,
	targname,
	obj_flag,
	object,
	ra,
	dec,
	approved_exposure_time,
	ocat_propid,
	grating,
	instrument,
	soe_st_sched_date,
	type,
	lts_lt_plan,
	status) 
select 
	obsid,
	targid,
	seq_nbr,
	targname,
	obj_flag,
	object,
	ra,
	dec,
	approved_exposure_time,
	ocat_propid,
	grating,
	instrument,
	soe_st_sched_date,
	type,
	lts_lt_plan,
	status
from 
	target;

/* ADD PROPOSAL STUFF */

/* (updated for new database structure -- 2/22/99)

update #sot_ocat set proposal_number = p.proposal_number, proposal_title = p.title, PI_name = s.last from #sot_ocat j, proposal..proposal p, proposal..scientist s where j.ocat_propid = p.ocat_propid and p.piid = s.scid; */

update 
	#sot_ocat 
set 
	proposal_number = p.prop_num,
	proposal_title = p.title, 
	ao_string = p.ao_str,
        joint_flag = p.joint
from	
	#sot_ocat j,
	prop_info p 
where 
	j.ocat_propid = p.ocat_propid;

update 
	#sot_ocat 
set 
	PI_name = s.last 
from 
	#sot_ocat j,
/*
	axafusers..person_short s,
	prop_info p 
*/
    view_pi s,
	prop_info p 
where 
	j.ocat_propid = p.ocat_propid;
/*
	j.ocat_propid = p.ocat_propid and 
	p.piid = s.pers_id;
*/

/* (adding observer name -- 7/6/99 ) */

update 
	#sot_ocat 
set 
	Observer = s.last 
from 
	#sot_ocat j,
/*
	axafusers..person_short s,
	prop_info p 
*/
    view_coi s,
	prop_info p 
where 
	j.ocat_propid = p.ocat_propid;
/*
	p.coi_contact = 'Y' and
	j.ocat_propid = p.ocat_propid and 
	p.coin_id = s.pers_id;
*/

/* 
 * Observer same as PI when coi_contact = N
 */

/*    
update 
	#sot_ocat 
set 
	Observer = PI_name
from 
	#sot_ocat j,
	axafusers..person_short s,
	prop_info p 
    view_coi
	prop_info p 
where 
	p.coi_contact = 'N' and
	j.ocat_propid = p.ocat_propid;
*/


/* 
 * DISPLAY TABLE
 */

select * from #sot_ocat order by seq_nbr; >           /data/mta4/obs_ss/sot_ocat.out
select * from #sot_ocat order by ra, dec; >           /data/mta4/obs_ss/sot_ocat_ra.out
/*
 *select * from #sot_ocat order by soe_st_sched_date; > /data/mta4/obs_ss/sot_ocat_date.out
 */
