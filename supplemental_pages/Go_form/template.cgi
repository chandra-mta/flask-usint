#!/home/ascds/DS.release/bin/perl

BEGIN
  {
#    $ENV{SYBASE} = "/soft/sybase";
    $ENV{SYBASE} = "/soft/SYBASE16.0";
#    $ENV{PATH} = "/soft/sybase:/usr/bin:/usr/local/bin";
  }

use DBI;
use DBD::Sybase;
use CGI ':standard';

#################################################################################################
#                                                                                               #
#   cycle<#>.cgi: template of cycle<#>.cgi page.                                                #
#                                                                                               #
#       author: Jennifer Posson-Brown (jpbrown@head.cfa.harvard.edu)                            #
#               updated/maintained by t. isobe (tisobe@cfa.harvard.edu)                         #
#                                                                                               #
#       also works if it is used with /data/mpcrit1/bin/perl with no .htaccess file             #
#                                                                                               #
#       Last Update: Jun 28, 2021                                                               #
#                                                                                               #
# Jul 16, 2022 MS                                                                               #
# /soft/ascds/DS.release/ots/bin/perl -> /home/ascds/DS.release/ots/bin/perl                    #
#################################################################################################

print "Content-type: text/html\n\n";

#----------------------------------------------------------
#
#--- for the test, set "$test" to yes
#
#$test   = 'yes';
$test   = 'no';
#$tester = 'isobe@head.cfa.harvard.edu';
#$tester = 'swolk@head.cfa.harvard.edu';
$tester = 'william.aaron@cfa.harvard.edu';
#
#----------------------------------------------------------

#
#--- read paramter stage, which indicates what a user want to do
#
$stage=param("stage");

#-----------------------------------------------------------
#--- everything is fine and mail the letter to the observer
#-----------------------------------------------------------

if ($stage eq "mailit") {
#
#--- read parameters passed
#
    $which_letter = param("letter");
    $email_list   = param("emaillist");
    $cxc_email    = param("cxcemail");
    $obs_type     = param("obstype");
    $obs_date     = param("obsdate");
    $obj_name     = param("objname");
    $obsid        = param("obsid");
    $prop_title   = param("proptitle");
    $prop_name    = param("propname");
    $seq_num      = param("seqnum");
    $deadline     = param("deadline");
    $cxc_name     = param("cxcname");
    $cxc_phone    = param("cxcphone");
    $cxc_fax      = param("cxcfax");
    $email_who    = param("emailwho");
    $instrument   = param("instrument");
    $contact      = param("contact");
#
#--- create an appropriate letter
#
    if ($which_letter eq "hrc_27") {
	    make_hrc_letter(); 

    } elsif ($which_letter eq "acis_27") {
	    make_acis_letter();

    } elsif ($which_letter eq "acis_st_27") {
	    make_acis_st_letter();

    } elsif ($which_letter eq "acis_st_early_27") {
	    make_acis_st_early_letter();

    } elsif ($which_letter eq "letg") {
	    make_letg_letter();

    } elsif ($which_letter eq "hetg") {
	    make_hetg_letter();

    }
#
#--- print a header part of email notification
#
    html_email_header();

    $subject_line = "Your Chandra Observation (Sequence \#$seq_num)";
#
#--- sending out email to proposer(s) -----------------------------
#
    if ($email_who eq "prop") {

	    $cc="cus\@cfa.harvard.edu, $cxc_email";
	    $bcc="";
#
#--- if this is a test, just sent to "tester"
#
        if($test =~ /yes/i){
	        sendmail($tester, $tester, '', '', $subject_line, $the_letter);
        }else{
	        sendmail($email_list, $cxc_email, $cc, $bcc, $subject_line, $the_letter);
        }
	    print h2("Your email has been sent to $email_list!");
#
#--- select the correct backlink page
#
#        print "<a href='https://icxc.harvard.edu/cal/go_form/test_new.html'>";
#        print "<a href='https://icxc.harvard.edu/cal/go_form/'>";
#        print "<a href='https://cxc.cfa.harvard.edu/usg/'>";
        print "<table border=1><tr><th><a href='https://cxc.cfa.harvard.edu/cus/Usint/go_form/'>Back To Letter Generator Page</a></th></tr></table>";
#        print "<p><a href='https://icxc.harvard.edu/cal/go_form/'>Back To Letter Generator Page</a></p>";

#
#--- sending email to CXC user for review/rewrite ------------------
#
    } elsif ($email_who eq "cxc") {

        if($test =~ /yes/i){
	        sendmail($tester, $tester, '', '', $subject_line, $the_letter);
        }else{
	        sendmail($cxc_email, $cxc_email, "", "", $subject_line, $email_list.", 
                 cus\@cfa.harvard.edu\n\n".$the_letter);
        }

	    print h2("Your email has been sent to $cxc_email!");
	    print "<p style='padding-bottom:40px'>";
        print "If you see any problems, please email <a href=mailto:bwargelin\@cfa.harvard.edu>Brad Wargelin</a> and <a href=mailto:william.aaron\@cfa.harvard.edu>Will Aaron</a>.</p>";
#
#--- select the correct backlink page
#
#        print "<a href='https://icxc.harvard.edu/cal/go_form/test_new.html'>";
#        print "<a href='https://icxc.harvard.edu/cal/go_form/'>";
#        print "<a href='https://cxc.cfa.harvard.edu/usg/'>";
        print "<table border=1><tr><th><a href='https://cxc.cfa.harvard.edu/cus/Usint/go_form/'>Back To Letter Generator Page</a></th></tr></table>";
#        print "<p><a href='https://icxc.harvard.edu/cal/go_form/'>Back To Letter Generator Page</a></p>";


    } else {
#
#--- something not right, go back to the previous page ---------------
#
	    print "<p>You did not select a destination.  Please return to the previous page ";
        print "and choose where to send the email.</p>";
    }
    print end_html;

#--------------------------------------------------------------------------------------------
#--- previewing the letter; if there is an error, it gets caught to the first two "if" blocks.
#--------------------------------------------------------------------------------------------

} elsif ($stage eq "preview") {

    $which_letter=param("letter");

    if ($which_letter eq "") {
#
#--- selection-miss error.
#
        html_error_header();
	    print "<p>You did not chose which form letter to use.  Please return to ";
        print "the previous page and select the appropriate template.</p>";
	    print end_html;

    } else {

	    if ($got=get_values()) {
#
#--- Other errors.
#
#--- Yes, I (J.P.B.) did write get_values to return TRUE (non-zero) if it
#--- encounters a PROBLEM.  This is because I wanted to signal different
#--- kinds of problems with different integers, instead of being limited to
#--- just zero.
#
            html_error_header();
            print h2("Could not find entered information:");

            if ($got == 1) {
		        print "<p>I could not locate your Obsid ($obsid) in the OCAT. ";
                print "Please check the number and <a href=\"http://icxc.harvard.edu/cal/go_form/\">";
                print "try again</a>.</p>";
				
	        } elsif ($got == 2) {
		        print "<p>Your name ($cxc_last) is not in the list of USINT scientists. ";
                print "If you would like to be added, please <a href=mailto:$tester>";
                print "email $tester</a></p>";

	        } elsif ($got == 3) {
		        print "<p>I could not find the contact information for the observer. ";
                print "Please <a href=mailto:$tester>email $tester</a> ";
                print "and report this problem.</p>";
	        }
	        print end_html;
	        print "\n";

	    } else {
#
#--- everything seems OK, print the result
#
	        if ($which_letter eq "hrc_27") {
		        make_hrc_letter(); 		

	        } elsif ($which_letter eq "acis_27") {
		        make_acis_letter();

	        } elsif ($which_letter eq "acis_st_27") {
		        make_acis_st_letter();

	        } elsif ($which_letter eq "acis_st_early_27") {
		        make_acis_st_early_letter();

	        } elsif ($which_letter eq "letg") {
		        make_letg_letter();

	        } elsif ($which_letter eq "hetg") {
		        make_hetg_letter();

	        }
    
	        html_header();

            print "<p>";
	        print "To: $email_list<br />";
            print "Cc: cus\@cfa.harvard.edu, $cxc_email<br />";
            print "Subject: Your Chandra Observation (Sequence \#$seq_num)<br />";
            print "--------------<br /></p>";

            print "<pre>";
            $the_letter_temp = $the_letter;
            $the_letter_temp =~ s/\&/&amp;/g;
            $the_letter_temp =~ s/\>/&gt;/g;
            $the_letter_temp =~ s/\</&lt;/g;
            $the_letter_temp =~ s/\-/&ndash;/g;
	        print "$the_letter_temp";	
            print "</pre>";

	        html_footer();	
        }
    }
}

#----------------------------------------------------------------------------------
#--- html_header: writing a header of the page                                  ---
#----------------------------------------------------------------------------------

sub html_header {
#
#--- html 5 compliant
#
    print "<!DOCTYPE html>";
    print "<html><head><title>Preview Letter</title></head>\n";
    print "<body style='color:#000000;background-color:#FFFFFF'>\n";
    print "<h3>Preview of the Draft</h3>";
    print "<p style='margin-left:20px;pmargin-right:20px;padding-bottoom:20px'><em>";
    print "The letter is below.  Use your browser's Back button<br /> ";
    print "to change your inputs, or see the bottom of the page for<br /> ";
    print "information on how send it to: <br /><br /> $email_list.</em></p>\n";
    print "<hr />";
}

#----------------------------------------------------------------------------------
#--- html_error_header: header for the error notification page                  ---
#----------------------------------------------------------------------------------

sub html_error_header {
    print "<!DOCTYPE html>";
    print "<html><head><title>Error processing Request</title></head>\n";
    print "<body style='color:#000000;background-color:#FFFFFF'>\n";
}

#----------------------------------------------------------------------------------
#--- html_email_header: header for the email sending notification page          ---
#----------------------------------------------------------------------------------

sub html_email_header {
    print "<!DOCTYPE html>";
    print "<html><head><title>Result of Send</title></head>\n";
    print "<body style='color:#000000;background-color:#FFFFFF'>\n";
}

#----------------------------------------------------------------------------------
#--- html_footer: writing the end part of the page                              ---
#----------------------------------------------------------------------------------

sub html_footer { 

    print "<hr />\n\n";
    print "<form action=\"cycle27.cgi\">\n";
#
#-- passing parameters
#
    print "<input type=hidden name=\"stage\"      value=\"mailit\">\n";
    print "<input type=hidden name=\"letter\"     value=\"$which_letter\">\n";
    print "<input type=hidden name=\"cxcemail\"   value=\"$cxc_email\">\n";
    print "<input type=hidden name=\"cxcname\"    value=\"$cxc_name\">\n";
    print "<input type=hidden name=\"cxcphone\"   value=\"$cxc_phone\">\n";
    print "<input type=hidden name=\"cxcfax\"     value=\"$cxc_fax\">\n";
    print "<input type=hidden name=\"instrument\" value=\"$instrument\">\n";
    print "<input type=hidden name=\"obstype\"    value=\"$obs_type\">\n";
    print "<input type=hidden name=\"obsdate\"    value=\"$obs_date\">\n";
    print "<input type=hidden name=\"obsid\"      value=\"$obsid\">\n";
    print "<input type=hidden name=\"objname\"    value=\"$obj_name\">\n";
    print "<input type=hidden name=\"seqnum\"     value=\"$seq_num\">\n";
    print "<input type=hidden name=\"proptitle\"  value=\"$prop_title\">\n";
    print "<input type=hidden name=\"propname\"   value=\"$prop_name\">\n";
    print "<input type=hidden name=\"deadline\"   value=\"$deadline\">\n";
    print "<input type=hidden name=\"emaillist\"  value=\"$email_list\">\n";
    print "<input type=hidden name=\"contact\"    value=\"$contact\">\n";
#
#--- setting radio buttom selections
#
    print "<p>";
    print "<div style='padding-bottom:5px'>";
    print "<input type=radio  name=\"emailwho\"   value=\"prop\"> ";
    print "<b>This letter is fine</b> so email it directly to $email_list<br />";
    print "</div>";
    print "<input type=radio name=\"emailwho\" value=\"cxc\"> <b>I need to edit this letter</b>";
    print " so email it to me and I will forward it to the proposer(s).<br />";
    print "<span style='margin-left:25px'> </span>";
    print "The appropriate email address(es) will be on the first line of the message.<br />";
    print "<span style='margin-left:25px'> </span>";
    print "(Don't forget to edit the email header to remove the Forwarding.)";
    print "<p>";

    print "<input type=submit value=\"Proceed\">\n";

    print "</form>\n";
    print "</body></htmt>\n";
}

#----------------------------------------------------------------------------------
#--- sendmail: Calls the UNIX program "sendmail" to send the message            ---
#----------------------------------------------------------------------------------

sub sendmail{

    my($to, $from, $cc, $bcc, $subject, $msg) = @_; 

    open(SENDMAIL, "|/usr/lib/sendmail $to $cc $bcc") || return;
    print SENDMAIL <<"EOD";
From:     $from
To:       $to
Cc:       $cc
Bcc:      $bcc
Reply-To: $from
Subject:  $subject

$msg
EOD
    close(SENDMAIL);
    return;
}

#----------------------------------------------------------------------------------
#--- get_values: read database, cxc user list, etc                              ---
#----------------------------------------------------------------------------------

sub get_values {

    my %months = qw(
		    Jan    Dec
		    Feb    Jan
		    Mar    Feb
		    Apr    Mar
		    May    Apr
		    Jun    May
		    Jul    Jun
		    Aug    Jul
		    Sep    Aug
		    Oct    Sep
		    Nov    Oct
		    Dec    Nov
		    );
    
    my %months_for = qw(
			Jan    Feb
			Feb    Mar
			Mar    Apr
			Apr    May
			May    Jun
			Jun    Jul
			Jul    Aug
			Aug    Sep
			Sep    Oct
			Oct    Nov
			Nov    Dec
			Dec    Jan
			);
      
    my %days = qw(
		    Jan    31
		    Feb    28
		    Mar    31
		    Apr    30
		    May    31
		    Jun    30
		    Jul    31
		    Aug    31
		    Sep    30
		    Oct    31
		    Nov    30
		    Dec    31
		    );
    

    $seq_num2  = param("seqnum");
    $obsid     = trim($seq_num2);
    $cxc_last2 = param("cxcname");
    $cxc_last  = trim($cxc_last2);
    $cxc_last  =~ tr/A-Z/a-z/;
    $date_type = param("datetype");
#
#--- /usr/local/bin/sqsh -S ocatsqlsrv -D axafocat -U browser -P newuser
#--- see /proj/web-cxc/cgi-gen/target_param.cgi
#
    #$usr   = "browser";
    $usr   = "mtaops_internal_web";
    $srv   = "ocatsqlsrv";
    $dbase = "axafocat";
 
    $pwd   = `cat /data/mta4/CUS/authorization/.targpass_internal`;
    chomp $pwd;

    $db    = "server=$srv;database=$dbase";
    $dsn1  = "DBI:Sybase:$db";
    $dbh1  = DBI->connect($dsn1, $usr, $pwd, { PrintError => 0, RaiseError => 1});

    $sqlh1 = $dbh1->prepare(qq(select obsid,targname,instrument,lts_lt_plan,proposal_id,seq_nbr from target where obsid=${obsid}));
    $sqlh1->execute();
    @targetdata = $sqlh1->fetchrow_array;
    $sqlh1->finish;

#    $obsid=$targetdata[0];
    $obj_name   = $targetdata[1];
    $instrument = $targetdata[2];

    if (! defined($targetdata[3])) {
#
#---if field is empty, assume it's a pool target
#
	    $obs_date = "pool";

    } else {
#
#--- otherwise get date
#
	    @blah = split(/ /, $targetdata[3]);

	    if (trim($blah[1]) !~ /^$/) {               # day is single digit
	        $obs_date = join '-', $blah[1], $blah[0], $blah[2];
	    } else {
	        $obs_date = join '-', $blah[2], $blah[0], $blah[3];
	    }
    }
    

    $id      = $targetdata[4];
    $seq_num = $targetdata[5];
    
    $sqlh1   = $dbh1->prepare(qq(select title,piid,coi_contact,coin_id from prop_info where proposal_id=${id}));
    $sqlh1->execute();
    @targetdata = $sqlh1->fetchrow_array;
    $sqlh1->finish;
#
#--- disconnect from axafocat database
#
    $dbh1->disconnect(); 

    $prop_title = $targetdata[0];

    $piid       = $targetdata[1];
    $coiid      = $targetdata[3];
    $coiflag    = $targetdata[2];       #Y/N: if Y then co-i is observer, if N then pi is observer
#
#--- if co-i is observer, send to both emails but address to co-i's name
#--- get observer contact info
#
    $dbase="axafusers";

    $db   = "server=$srv;database=$dbase";
    $dsn1 = "DBI:Sybase:$db";
    $dbh1 = DBI->connect($dsn1, $usr, $pwd, { PrintError => 0, RaiseError => 1});
#
#--- get PI email and set email and name to PI by default
#
    $sqlh1 = $dbh1->prepare(qq(select last,email from person_short where pers_id=${piid}));
    $sqlh1->execute();
    @contactdata = $sqlh1->fetchrow_array;
    $sqlh1->finish;
    
    if (! defined ($contactdata[0])){
	    $prop_name  = "Chandra Observer";
	    $email_list = $contactdata[1];
	    $pi_email   = $contactdata[1];
    } else {
	    $prop_name  = join ' ',"Dr.",$contactdata[0];
	    $email_list = $contactdata[1];
	    $pi_email   = $contactdata[1];
    } 
    
    if ($coiflag eq 'Y') { 
#
#--- overwrite name w/ co-i name and email w/ both emails
#
	    $sqlh1 = $dbh1->prepare(qq(select last,email from person_short where pers_id=${coiid}));
	    $sqlh1->execute();
	    @contactdata = $sqlh1->fetchrow_array;
	    $sqlh1->finish;
	
	    if (! defined ($contactdata[0])){
	        $prop_name = "Chandra Observer";
	        $coi_email = $contactdata[1];
	    } else {
	        $prop_name = join ' ', "Dr.", $contactdata[0];
	        $coi_email = $contactdata[1];
	    } 

	    $email_list=join ', ', $coi_email, $pi_email;
    }
#
#--- disconnect from axafusers database
#
    $dbh1->disconnect();

    if ($date_type ne "unscheduled") { 
	    if ($obs_date eq "pool") {
	        $obs_type="P";
	    } else {
	        $obs_type="S";
	    }
    } else {
	    $obs_type="U";
    }

    if ($date_type eq "auto") {
##	    if ($obs_type eq "P") {
#
#--- pooled observations default to a deadline 1 week from the day the
#--- email is sent.
#
	        $delta=7;
	        $date=`/bin/date`;
	        chomp($date);
	        @temp=split(/ +/,$date);
	        $year=$temp[5];
	        $day=$temp[2] + $delta;
	        $month=$temp[1];
	        $count=$days{$month};

	        if (($month eq "Feb") && (($year % 4) == 0)) {
#
#--- This handles leap years, but not the absence of a leap year every
#--- year divisible by 100 but not 400.
#
		        $count++;
	        }
	        if ($day > $count) {
		        $day  -= $count;
		        $month = $months_for{$month};
		        if ($month eq "Jan") {
		            $year++;
		    
		        }
	        }
	        $deadline = $day ."-". $month ."-". $year;

##	    } elsif ($obs_type eq "S") {      # not pooled but auto date
#
#--- Explicitly scheduled observations default to a deadline 32 days
#--- before observation.
#
##	        $delta = 32;
##	        @temp  = split(/-/,$obs_date);
##	        $year  = $temp[2];
##	        $day   = $temp[0];
##	        $month = $temp[1];
##	        $count = $day;
##
##	        for ($count=$day; $count-$delta < 1; $count+=$days{$month}) {
##		        $month=$months{$month};
##
##		        if ($month eq "Dec") {
##		            $year--;
##		        } elsif (($month eq "Feb") && (($year % 4) == 0)) {
#
#--- This handles leap years, but not the absence of a leap year every
#--- year divisible by 100 but not 400.
#
##		            $count++;
##		        }
##	        }
##	        $day      = $count - $delta;
##	        $deadline = $day ."-". $month ."-". $year;
##	    }

    } elsif ($date_type eq "setdate") {    #custom assigned deadline

	    $deadline=param("deadline");

    } elsif ($date_type eq "unscheduled") {
#
#--- set deadline to 14 days from date of email
#
	    $delta = 14;
	    $date  =`/bin/date`;
	    chomp($date);
	    @temp  = split(/ +/,$date);
	    $year  = $temp[5];
	    $day   = $temp[2] + $delta;
	    $month = $temp[1];
	    $count = $days{$month};

	    if (($month eq "Feb") && (($year % 4) == 0)) {
#
#--- This handles leap years, but not the absence of a leap year every
#--- year divisible by 100 but not 400.
#
		    $count++;
	    }
	    if ($day > $count) {
		    $day  -= $count;
		    $month = $months_for{$month};
		    if ($month eq "Jan") {
		        $year++;
		    }
	    }
	    $deadline = $day ."-". $month ."-". $year;
	}

    open (CXCDATA,"cxc_data.txt") || die "couldn't open cxc_data.txt";
#
#--- This is a file that must be maintained when new scientists are going
#--- to use the script.  It is a shortcut for finding their info uniquely
#--- and in the right format.
#
    $gotit = 0;
    while (!$gotit && ($temp=<CXCDATA>)) {
	    chomp ($temp);
        if($temp =~ /::/){
	        @temp = split(/::/,$temp);
        }else{
	        @temp = split(/\t/,$temp);
        }
	    if ($temp[0] eq $cxc_last) {
	        $gotit     = 1;
	        $cxc_name  = $temp[1];
	        $cxc_email = $temp[2];
	        $cxc_phone = $temp[3];
	        $cxc_fax   = $temp[4];
#
#--- COVID closure temporally suspended --------------------------
##
            $cxc_phone = '000-000-0000 (temporarily suspended)';
            $cxc_fax   = '000-000-0000 (temporarily suspended)';
#------------------------------------------------------------------
	    }
    }
    close (CXCDATA) || die "couldn't close cxc_data.txt";

    if (!$gotit) {
#
#---Returns error signalling user last name not in database.
#
	    return 2;
    }
#
#--- No longer include followup contact name.  Only ACIS letter 
#--- mentions, and if none, it ignores it.
#
	$contact="NONE";
    
    return 0;  #It all worked!  (We hope.)
}


#----------------------------------------------------------------------------------
#--- make_hrc_letter: creating a letter for HRC observation                     ---
#----------------------------------------------------------------------------------

sub make_hrc_letter {
#
#--- Constructs the string $the_letter based on the HRC-I letter template
#--- and global variables filled with observation specific information.
#--- $the_letter is formatted to a good screen width (72 char?).
#
    my($count,$big_ole_string, $big_part);

    if ($obs_type eq "U") {

	    $big_ole_string = "using the HRC has yet to be scheduled and as such could be observed at any time. ";

    } elsif ($obs_type eq "P") {

	    $big_ole_string  = "using the HRC is in the queue for observation. Since it is not time constrained, ";
        $big_ole_string .= "the exact time of your observation has not yet been determined exactly ";
        $big_ole_string .= "and will be set to \"over-subscribe\" the schedule allowing for more ";
        $big_ole_string .= "efficient observatory operations. We will communicate the exact time ";
        $big_ole_string .= "of observation when it is known, which could be at any time. ";

    } elsif ($obs_type eq "S") {

	    $big_ole_string = "using the HRC is scheduled to be observed the week of $obs_date. ";

    }
    $big_part = '';
    while ($big_ole_string =~ /.+/) {
	    $count = rindex(substr($big_ole_string,0,72)," ");
	
        if ($count == 0) {
	        $big_part      .= $big_ole_string;
	        $big_ole_string = "";
	    } else {
	        $big_part      .= substr($big_ole_string,0,$count) . "\n";
	        $big_ole_string = substr($big_ole_string,$count+1);
	    }
    }
#
#--- read hrc template and substitute values
#
    local(*INPUT, $/);
    open(INPUT, "/data/mta4/CUS/www/Usint/go_form/Letters/hrc");
    $the_letter = <INPUT>;
    close(INPUT);

    $the_letter =~ s/#prop_name#/$prop_name/g;
    $the_letter =~ s/#obj_name#/$obj_name/g;
    $the_letter =~ s/#prop_title#/$prop_title/g;
    $the_letter =~ s/#seq_num#/$seq_num/g;
    $the_letter =~ s/#obsid#/$obsid/g;
    $the_letter =~ s/#big_ole_string#/$big_part/g;
    $the_letter =~ s/#deadline#/$detline/g;
    $the_letter =~ s/#cxc_name#/$cxc_name/g;
    $the_letter =~ s/#cxc_email#/$cxc_email/g;
    $the_letter =~ s/#cxc_phone#/$cxc_phone/g;

}

#----------------------------------------------------------------------------------
#--- make_acis_letter: creating a letter for ACIS observation                   ---
#----------------------------------------------------------------------------------

sub make_acis_letter {
#
#--- Constructs the string $the_letter based on the ACIS letter template
#--- and global variables filled with observation specific information.
#--- $the_letter is formatted to a good screen width (72 char?).
#

    my($count, $big_ole_string, $part1, $part2, $part3);

    $part1 = '';
    $part2 = '';

    $big_ole_string  = "$cxc_name ($cxc_email; Phone: $cxc_phone) ";
    $big_ole_string .= "will be your contact for your ACIS observation: ";
#
#--- FYI- this loop can hiccup if there isn't a space at the end of the
#--- last line of text in $big_ole_string - so just stick one in.
#
    while ($big_ole_string =~ /.+/) {
	    $count = rindex(substr($big_ole_string,0,72)," ");
	    if ($count == 0) {
	        $part1         .= $big_ole_string;
	        $big_ole_string = "";
	    } else {
	        $part1         .= substr($big_ole_string,0,$count) . "\n";
	        $big_ole_string = substr($big_ole_string,$count+1);
	    }
    }

    if ($contact eq "NONE"){
	    $part2 = "until the observational data have been received by the CXC. ";
    } else {
        $another_string = "until the observational data have been received by the CXC. ";
        while ($another_string =~ /.+/) {
            $count = rindex(substr($another_string,0,72)," ");
            if ($count == 0) {
	            $part2         .= $another_string;
	            $another_string = "";
            } else {
	            $part2         .= substr($another_string,0,$count) . "\n";
	            $another_string = substr($another_string,$count+1);
            }
        }
    }

    if ($obs_type eq "U") {
        $part3 ="Your observation has yet to be scheduled and as such could be observed at any time.";

    } elsif ($obs_type eq "P") {

        $part3  = "Your observation is currently in a pool for observation at any time. \n";
        $part3 .= "Since it is not time constrained, the exact time of your observation \n";
        $part3 .= "has not yet been determined and will be set to \"over-subscribe\" the \n";
        $part3 .= "schedule allowing for more efficient observatory operations. We will \n";
        $part3 .= "communicate the expected time of observation when it is known.  Note, \n";
        $part3 .= "because pool observations are subject to schedule changes, your pool \n";
        $part3 .= "observation may not appear in the posted schedule during the timeframe above.\n";

    } elsif ($obs_type eq "S") {

        $part3  ="Your observation is currently scheduled to be observed during the week ";
        $part3 .= "of $obs_date. ";

    }
#
#--- read acis template and substitues 
#
    local(*INPUT, $/);
    open(INPUT, "/data/mta4/CUS/www/Usint/go_form/Letters/acis_27");
    $the_letter = <INPUT>;
    close(INPUT);


    $the_letter =~ s/#part1#/$part1/g;
    $the_letter =~ s/#part2#/$part2/g;
    $the_letter =~ s/#part3#/$part3/g;
    $the_letter =~ s/#obj_name#/$obj_name/g;
    $the_letter =~ s/#seq_num#/$seq_num/g;
    $the_letter =~ s/#obsid#/$obsid/g;
    $the_letter =~ s/#prop_title#/$prop_title/g;
    $the_letter =~ s/#deadline#/$deadline/g;
    $the_letter =~ s/#obsid#/$obsid/g;
    $the_letter =~ s/#obs_date#/$obs_date/g;
    $the_letter =~ s/#contact#/$prop_name/g;
    $the_letter =~ s/#cxc_name#/$cxc_name/g;
    $the_letter =~ s/#cxc_email#/$cxc_email/g;
    $the_letter =~ s/#cxc_phone#/$cxc_phone/g;
    if ($cxc_fax ne ''){
        $the_letter =~ s/#cxc_fax#/$cxc_fax/g;
    }
}

#----------------------------------------------------------------------------------
#-- make_acis_st_letter: make acis short letter                                 ---
#----------------------------------------------------------------------------------

sub make_acis_st_letter {
#
#--- read acis template and substitues 
#
    local(*INPUT, $/);
    open(INPUT, "/data/mta4/CUS/www/Usint/go_form/Letters/acis_st_27");
    $the_letter = <INPUT>;
    close(INPUT);

    $the_letter =~ s/#obsid#/$obsid/g;
    $the_letter =~ s/#prop_title#/$prop_title/g;
    $the_letter =~ s/#deadline#/$deadline/g;
    $the_letter =~ s/#obj_name#/$obj_name/g;
    $the_letter =~ s/#seq_num#/$seq_num/g;
    $the_letter =~ s/#contact#/$prop_name/g;
    $the_letter =~ s/#cxc_name#/$cxc_name/g;
    $the_letter =~ s/#cxc_email#/$cxc_email/g;
    $the_letter =~ s/#cxc_phone#/$cxc_phone/g;
    if ($cxc_fax ne ''){
        $the_letter =~ s/#cxc_fax#/$cxc_fax/g;
    }
}

#----------------------------------------------------------------------------------
#-- make_acis_st_early_letter: make acis short early letter                     ---
#----------------------------------------------------------------------------------

sub make_acis_st_early_letter {
#
#--- read acis template and substitues 
#
    local(*INPUT, $/);
    open(INPUT, "/data/mta4/CUS/www/Usint/go_form/Letters/acis_st_early_27");
    $the_letter = <INPUT>;
    close(INPUT);

    $the_letter =~ s/#obsid#/$obsid/g;
    $the_letter =~ s/#prop_title#/$prop_title/g;
    $the_letter =~ s/#deadline#/$deadline/g;
    $the_letter =~ s/#obj_name#/$obj_name/g;
    $the_letter =~ s/#seq_num#/$seq_num/g;
    $the_letter =~ s/#contact#/$prop_name/g;
    $the_letter =~ s/#cxc_name#/$cxc_name/g;
    $the_letter =~ s/#cxc_email#/$cxc_email/g;
    $the_letter =~ s/#cxc_phone#/$cxc_phone/g;
    if ($cxc_fax ne ''){
        $the_letter =~ s/#cxc_fax#/$cxc_fax/g;
    }
}

#----------------------------------------------------------------------------------
#--- make_letg_letter: creating a letter for letg observation                   ---
#----------------------------------------------------------------------------------

sub make_letg_letter {
#
#--- Constructs the string $the_letter based on the LETG letter template
#--- and global variables filled with observation specific information.
#--- $the_letter is formatted to a good screen width (72 char?).
#

    my($count, $big_ole_strin, $part1, $part2);

    if ($cxc_name=~ /Drake/) {
	    $oth_name="Brad Wargelin";
    } else {
	    $oth_name="Jeremy Drake";
    }

    $big_ole_string  = "I will be the Uplink Support Interface (USINT) contact for ";
    $big_ole_string .= "your LETGS/$instrument observation of $obj_name (Sequence ";
    $big_ole_string .= "\#$seq_num) throughout the \"uplink cycle\", i.e., until your ";
    $big_ole_string .= "photons are collected by Chandra.  I am contacting you now to ";
    $big_ole_string .= "request that you confirm your observation set-up by $deadline. ";
    $part1           = '';

	while ($big_ole_string =~ /.+/) {
	    $count=rindex(substr($big_ole_string, 0, 72)," ");
	    if ($count == 0) {
		    $part1         .= $big_ole_string;
		    $big_ole_string = "";
	    } else {
		    $part1         .= substr($big_ole_string,0,$count) . "\n";
		    $big_ole_string = substr($big_ole_string,$count+1);
	    }
	}

    if ($obs_type eq "U") {
        $part2 = "Your observation has yet to be scheduled and as such could be observed at any time.";

    }  elsif ($obs_type eq "S") {
	    $part2 = "Your observation is currently scheduled for the week of $obs_date.";

    } elsif ($obs_type eq "P") {
        $part2 = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n";
        $part2 .= "\n";
        $part2 .= "Your observation is in a \"pool\" of targets that may be scheduled at\n";
        $part2 .= "any time in order to \"fill out\" Mission Planning's Short Term\n";
        $part2 .= "Schedules.  This pooling of relatively unconstrained targets permits\n";
        $part2 .= "more efficient and flexible observatory operations.  Note that\n";
        $part2 .= "Pool targets are marked with a red \"P\" in the Chandra Long Term\n";
        $part2 .= "Schedule (at http://cxc.harvard.edu/target_lists/longsched.html).\n";
        $part2 .= "\n";
        $part2 .= "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n";

#       $part2  = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n";
#       $part2 .= "\n";
#       $part2 .= "Your observation is a TOO, and does not appear in the Chandra long\n";
#       $part2 .= "term schedule (at http://cxc.harvard.edu/target_lists/longsched.html).  I am\n";
#       $part2 .= "contacting you now, even though some set-up parameters cannot be\n";
#       $part2 .= "specified in advance, in order to minimize the amount of work that\n";
#       $part2 .= "must be done during what may be a very short period of time.  Any\n";
#       $part2 .= "remaining parameters will be finalized when your TOO has been activated.\n";
#       $part2 .= "\n";
#       $part2 .= "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n";
    }

    if (($instrument eq "HRC-S") or ($instrument eq "HRC-I")) {

        local(*INPUT, $/);
        open(INPUT, "/data/mta4/CUS/www/Usint/go_form/Letters/letg_hrc_27");
        $the_letter = <INPUT>;
        close(INPUT);

    } elsif (($instrument eq "ACIS-S") or ($instrument eq "ACIS-I")) {

        local(*INPUT, $/);
        open(INPUT, "/data/mta4/CUS/www/Usint/go_form/Letters/letg_acis_27");
        $the_letter = <INPUT>;
        close(INPUT);

    }

    if ($oth_name=~ /Wargelin/) {

        $other       = 'Brad Wargelin';
        $other_email = 'bwargelin@cfa.harvard.edu';
        $other_phone = '(617)496-7702';
        $other_fax   = '(617)495-7356';

    } elsif ($oth_name=~ /Drake/) {

        $other       = 'Jeremy Drake';
        $other_email = 'jdrake@cfa.harvard.edu';
        $other_phone = '(617)496-7850';
        $other_fax   = '(617)495-7356';
    }

    $the_letter =~ s/#prop_name#/$prop_name/g;
    $the_letter =~ s/#obsid#/$obsid/g;

    $the_letter =~ s/#prop_title#/$prop_title/g;
    $the_letter =~ s/#seq_num#/$seq_num/g;
    $the_letter =~ s/#obj_name#/$obj_name/g;
    $the_letter =~ s/#deadline#/$deadline/g;

    $the_letter =~ s/#part1#/$part1/g;
    $the_letter =~ s/#part2#/$part2/g;
    #
    $the_letter =~ s/#cxc_name#/$cxc_name/g;
    $the_letter =~ s/#cxc_email#/$cxc_email/g;
    $the_letter =~ s/#cxc_phone#/$cxc_phone/g;
    $the_letter =~ s/#cxc_fax#/$cxc_fax/g;
    $the_letter =~ s/#other#/$other/g;
    $the_letter =~ s/#other_email#/$other_email/g;
    $the_letter =~ s/#other_phone#/$other_phone/g;
    $the_letter =~ s/#other_fax#/$other_fax/g;
}



#----------------------------------------------------------------------------------
#--- make_hetg_letter: creating a letter for hetig observation                  ---
#----------------------------------------------------------------------------------


sub make_hetg_letter {
#
#--- Constructs the string $the_letter based on the HETG letter template
#--- and global variables filled with observation specific information.
#--- $the_letter is formatted to a good screen width (72 char?).

    local(*INPUT, $/);
    open(INPUT, "/data/mta4/CUS/www/Usint/go_form/Letters/hetg");
    $the_letter = <INPUT>;
    close(INPUT);

}

#----------------------------------------------------------------------------------
#--- trim: triming leading and trailing blank spaces                            ---
#----------------------------------------------------------------------------------

sub trim {
    my @out = @_;
    for (@out){
        s/^\s+//;
        s/\s+$//;
    }
    return wantarray ? @out: $out[0];
}

#----------------------------------------------------------------------------------
#--- trimtr: triming tail blank spaces                                          ---
#----------------------------------------------------------------------------------

sub trimtr {
    my @out = @_;
    for (@out){
#        s/^\s+//;
        s/\s+$//;
    }
    return wantarray ? @out: $out[0];
}

exit();

