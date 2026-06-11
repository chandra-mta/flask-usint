#!/home/ascds/DS.release/bin/perl

use strict;
use CGI qw{ :standard fatalsToBrowser};
use CGI::Carp;
#use Carp;
use Data::Dumper;
BEGIN {
    $ENV{SYBASE} = '/soft/SYBASE16.0';
}

use DBI;
use DBD::Sybase;
#use SQL::Abstract;
use POSIX;

# Paths
# expects to find the simcoord clicoord scripts in
my $program_dir = '/proj/web-cxc-secure/cgi-bin/target_search/';
# expects to find ".targpass" in the $pass_dir
#my $pass_dir = $program_dir;
#my $pass_dir = "/proj/web-icxc/cgi-bin/obs_ss/.Pass_dir/";
my $pass_dir = "/proj/web-cxc-secure/htdocs/mta/CUS/Usint/Pass_dir";
# to redirect back in case of failure
my $location = './search.html';

# paths of other CGIs used in output
my $target_cgi = 'http://cda.cfa.harvard.edu/chaser/startViewer.do?menuItem=sequenceSummary&obsid=';
my $target_param_cgi = 'http://cda.cfa.harvard.edu/chaser/startViewer.do?menuItem=details&obsid=';
my $ocatdatapage = 'https://cxc.cfa.harvard.edu/wsgi/cus/usint/ocatdatapage';
my $status_table = '/cgi-bin/op/op_status_table.cgi';
my $ads_search = 'http://cxc.harvard.edu/cgi-gen/cda/bib.pl?ADS=search&';
my $prop_search = ' https://icxc.harvard.edu/cgi-bin/cdo/review_report/disp_report.cgi';
my $sorttable_js = '/incl/sorttable.js';

my $default_search_radius = 4/60.;


my $app = new CGI;
if ($app->param()){
    my ($search_stmt, $bind, $order, $order_col);
    eval{
        my $param = get_param( $app );
        ($search_stmt, $bind, $order, $order_col) = define_search($param);
        my $dbh = get_dbh();
        my $list = run_search($dbh, $search_stmt, $bind, $order);
        show_list($list, $order_col);
    };
   if ($@){
       my $err = $@;
       print $app->header();
       print $app->start_html('Error');
       print "<pre>\n";
       print "$err\n";
       my $param_href = get_param( $app );
       print Dumper $param_href;
       print "</pre>\n";
       print $app->end_html();
       exit(0);
   }

}
else{
    # if the form has not been submitted, display the form
  print redirect($location);
} 

sub get_dbh{

    my $db_user = 'mtaops_internal_web';
    my $server = 'sqlsao';
    #if ( not -r "$pass_dir/.targpass"){
    #    croak("database password file not found at $pass_dir/.targpass");
    #}
    my $db_passwd = (-r ".targpass") ? `cat .targpass` : `cat $pass_dir/.targpass`;
    chomp $db_passwd;
    my $dbh = DBI->connect("DBI:Sybase:server=$server;database=axafocat",
                           $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});
    return $dbh;
}


sub run_search{
    my ($dbh, $stmt, $bind, $order_field) = @_;

    # Use ugly SQL to create a join on target, prop_info, view_coi, view_pi, and acisparam
    # We have "left join"s on the not-required components.
    #
    # the 'convert(char(26), t.soe_st_sched_date, 112) as sortday,' bit was just an easy way
    # to get the scheduled date as an integer for later lightweight sorting
    my $select = "select t.obsid, t.targid, t.seq_nbr, t.targname, t.obs_ao_str, t.obj_flag, t.object, "
        . " t.ra, t.dec, t.approved_exposure_time, t.ocat_propid, t.grating, t.instrument, "
        . " t.soe_st_sched_date, "
        . " convert(char(26), t.soe_st_sched_date, 121) as sortday, "
        . " t.type, t.lts_lt_plan, t.status, "
        . " p.prop_num, p.title, p.ao_str, p.joint, "
        . " pi.last as pi_last, coi.last as coi_last, acis.exp_mode as exp_mode"
        ."  from target as t "
        . " left join view_coi coi on t.ocat_propid = coi.ocat_propid "
        . " right join prop_info p on t.ocat_propid = p.ocat_propid "
        . " right join view_pi pi on t.ocat_propid = pi.ocat_propid "
        . " left join acisparam acis on t.acisid = acis.acisid ";


    my $order = " order by $order_field ";
    my @list = sql_fetchall_array_of_hashref( $dbh, $select . $stmt . $order, @{$bind} );
    return \@list;


}



##****************************************************************************
sub sql_fetchall_array_of_hashref {
#  Fetch complete results of an SQL statement into an array of hashrefs
##****************************************************************************
    my $dbh = shift;
    my $statement = shift;
    my @arg = @_;
    my @out;

    my $sth = $dbh->prepare($statement)
      or croak("Bad SQL statement '$statement': " . $dbh->errstr);
    
    $sth->execute(@arg);
    while (my $row = $sth->fetchrow_hashref) {
	push @out, $row;
    }
    $sth->finish();
    return @out;
 }



sub define_search{

    my $param_href = shift;

    # I've used SQL::Abstract to design the queries for this tool.
    # It isn't particularly easy to understand, but the idea of creating
    # "where" hash where by default each key corresponds to a SQL "AND"
    # condition makes sense.  See the docs for SQL::Abstract as needed.
    # It isn't in the DS OTS perl and is just appended to this CGI.
    my $sql = SQL::Abstract->new();
    my %where;

    # range fields, no wildcards or commas in this release
    my %exact_map = ( 'seqnbr' => 't.seq_nbr',
                      'pronbr' => 'p.prop_num',
                      'obsid' => 't.obsid' );

    # split on commas to try to parse lists
    # then try to parse ranges in those lists
    # manually construct a list of integers and pass that as the search
    # if given something other than integers, don't do anything with them.
    for my $def_param (keys %{$param_href}){
        if (defined $exact_map{$def_param}){
            my $form = $param_href->{$def_param};
            if ($form =~ /^\s*(\d+)\s*-+\s*(\d+)\s*$/) {
              my ($start, $stop) = ($1, $2);
              $where{$exact_map{$def_param}} = {'-between' => [ $start, $stop ]};
            }
            else{
              my @chunks = split(/,/, $form);
              my @ints;
              for my $piece (@chunks){
                if ($piece =~ /^\s*(\d+)\s*$/){
                  push @ints, $1;
                }
                else{
                  croak("Not an integer, range, or recognized list in '$form'");
                }
              }
              if (scalar(@ints)){
                $where{$exact_map{$def_param}} = { '-in' => \@ints };
              }
            }
            if (not defined $where{$exact_map{$def_param}}){
              croak("Could not build $def_param search.  Copy the parameters below and send to maintainer for assistance if required.");
            }
        }
    }

    # search either name field
    my %name = ( 'piname' => 1,
                 'observ' => 1 );
    for my $def_param (keys %{$param_href}){
        if (defined $name{$def_param}){
            my $par = lc($param_href->{$def_param});
            $where{'-or'} = ['lower(pi.last)' => { 'like' => "%${par}%"},
                               'lower(coi.last)' => { 'like' => "%${par}%"}];
        }
    }
    # for the name fields, the %where construction is more complicated, because
    # it has been relaxed to a SQL OR condition on either field.


    # category
    if (defined $param_href->{category}){
        my $cat = $param_href->{category};
        $where{'p.prop_num'} = { 'like' =>  "__${cat}%" };
    }


    if ((defined $param_href->{ra}) and (not defined $param_href->{dec})){
        croak("Dec. is missing" . $param_href->{ra});
    }
    if (defined $param_href->{dec} and not defined $param_href->{ra}){
        croak("RA is missing");
    }


    ##---- Convert hegidecimal coordinates to decimal for RA and Dec
    if (defined $param_href->{ra} and defined $param_href->{dec}){
        $_ = join ' ', ($param_href->{ra}, $param_href->{dec});
        s/[,:dhms]/ /g;
        my @arg = split;
        if (scalar(@arg) == 6){
            ($param_href->{ra}, $param_href->{dec}) = hms2dec( $param_href->{ra},
                                                               $param_href->{dec});
        }
        elsif (scalar(@arg) != 2){
            croak("RA, Dec must be Decimal or HH:MM:SS.SSS");
        }

    }

    # position search
    # if a simbad search, get coords and remove target from search (just doing the coordinate search)
    if (defined $param_href->{simbad}) {
        my ($sim_ra, $sim_dec) = sim2coord($param_href->{target}, $program_dir);
        $param_href->{ra} = $sim_ra;
        $param_href->{dec} = $sim_dec;
        delete $param_href->{target};
        delete $param_href->{simbad};
    }


    if (defined $param_href->{ra} and defined $param_href->{dec}){
        if (not defined $param_href->{radius}){
            $param_href->{radius} = $default_search_radius;
        }

        if (defined $param_href->{radcho}){
            if ($param_href->{radcho} eq 'arcmin'){
                $param_href->{radius} /= 60.0
            }
        }

        my $pi = 3.14159265;
        my $d2r = $pi/180.;
        my $r2d = 1./$d2r;

        my %pos = ($param_href->{ra}, $param_href->{dec});
        my $par = { 'ra' => $param_href->{ra},
                    'dec' => $param_href->{dec} };
        my $dist_string = "$r2d * "
            . " acos( cos( dec * $d2r) * cos( $par->{dec} * $d2r) * cos(( ra-$par->{ra} ) * $d2r) "
                . " + sin( dec * $d2r ) * sin( $par->{dec} * $d2r )) ";
        
        my $inn = 'is Not Null';

        # match where the ra and dec are both not null and the distance from the 
        # target pointing to the requested pointing is less than the radias.
        $where{ra} = \$inn;
        $where{dec} = \$inn;
        $where{$dist_string} = { '<=' => $param_href->{radius} };
    }
    

    # For the SQL searches with the 'like' => \@ constructors
    # we're getting an OR over all of the elements in the array (which is 
    # perfect if we've selected more than one box from a block like HETG and LETG)
    # and we're getting an AND between different types of elements as
    # they have different 'where' keys
    

    # loose match (wrapped with %'s)
    my %loose_match = ('joint' => 'p.joint',
                       'target' => 't.targname' );

    # for the joint and target name matches, ignore case
    # and wrap the search string in wildcards (%$_%")
    for my $like_type (keys %loose_match){
        my @instance;
        for my $def_param (keys %{$param_href}){
            if ($def_param =~ /$like_type.?/){
                push @instance, lc($param_href->{$def_param});
            }
        }
        if (scalar(@instance)){
            my @like = map {"%$_%"} @instance;
            my $ltype = $loose_match{$like_type};
            $where{"lower(${ltype})"} = { 'like' => \@like };
        }
    }

    # just plain "like" matches with no %'s but still case insensitive
    my %like_match = ('status' => 't.status',
                      'type' => 't.type',
                      'grating' => 't.grating',
                      'sciins' => 't.instrument',
                      'mode' => 'acis.exp_mode',
                      'prop_cycle' => 'p.ao_str',
                      'obs_cycle' => 't.obs_ao_str',
                  );
                      

    for my $like_type (keys %like_match){
        my @instance;
        for my $def_param (keys %{$param_href}){
            if ($def_param =~ /$like_type.?/){
                push @instance, lc($param_href->{$def_param});
            }
        }
        if (scalar(@instance)){
            my $ltype = $like_match{$like_type};
            $where{"lower(${ltype})"} = { 'like' => \@instance };
        }
    }

    # if we asked for a search and got absolutely nothing
    # param_href always has a sorted field, so check for scalar > 1
    if ((scalar(keys %{$param_href}) > 1) and not scalar(keys %where)){
        croak("Search could not be built.  Copy the parameters below and send to maintainer for assistance if required.");
    }

    #use Data::Dumper;
    #print Dumper \%where;
    my ($stmt, @bind) = $sql->where(\%where);
    my %order_map = ( 'Sequence Number' => 't.seq_nbr',
                      'RA' => 't.ra',
                      'Sched. Start Time' => 'sortday',
                 );
    # manually set default sort order, ignoring parameters...
    my $order = 't.seq_nbr';
    my $order_label = 'Sequence Number';
    # and then set by parameter
    if (defined $param_href->{sorted}){
        if (defined $order_map{$param_href->{sorted}}){
            $order = $order_map{$param_href->{sorted}};
            $order_label = $param_href->{sorted};
        }
    }
    return ($stmt, \@bind, $order, $order_label);

}



# from Ska::Convert
##***************************************************************************
sub hms2dec {
##***************************************************************************
    # Converts between sexigesimal (HMS) and decimal RA and Dec.  The
    # direction of conversion is given by the number and form of inputs
    # Returns two-element array of (RA, Dec) in either case.

    $_ = join ' ', @_;
   s/[,:dhms]/ /g;
    my @arg = split;
    my ($ra, $dec);

    if (@arg == 2) {
        ($ra, $dec) = @arg;
        my ($rah, $ram, $ras);
        my ($dec_sign, $decd, $decm, $decs);
        my ($ra_hms, $dec_hms);

        $ra += 360.0 if ($ra < 0);
        $ra /= 15.;
        $rah = floor($ra);
        $ram = floor(($ra - $rah) * 60.);
        $ras = ($ra - $rah - $ram / 60.) * 60. * 60.;

        $dec_sign = ($dec < 0);
        $dec = abs($dec);
        $decd = floor($dec);
        $decm = floor(($dec - $decd ) * 60.);
        $decs = ($dec - $decd - $decm / 60) * 60. * 60.;

        $ra_hms = sprintf "%d:%02d:%06.3f", $rah, $ram, $ras;
        $dec_hms = sprintf "%s%d:%02d:%05.2f", $dec_sign ? '-' : '+', $decd, $decm, $decs;

        return ($ra_hms,$dec_hms);
    } elsif (@arg == 6) {
        my ($rah, $ram, $ras, $decd, $decm, $decs) = @arg;
        $ra = 15.0*($rah + $ram/60. + $ras/3600.);
        $dec = abs($decd) + $decm/60. + $decs/3600.;
        $dec = -$dec if ($decd < 0.0);
        return (sprintf("%12.7f",$ra), sprintf("%12.6f", $dec));
    } else {
        carp "hms2dec: ERROR -- enter either 6 or 2 arguments\n";
    }
}


sub get_param {
    my $app = shift;
    my $param_href = $app->Vars();

    # create a list of allowed parameters manually
    my @fields = qw( sorted seqnbr pronbr piname observ target obsid ra dec radius radcho category prop_cycle obs_cycle simbad);
    push @fields, map {"sciins$_"} (1 .. 4);
    push @fields, map {"mode$_"} (1 .. 2);
    push @fields, map {"grating$_"} (1 .. 3);
    push @fields, map {"type$_"} (1 .. 5);
    push @fields, map {"status$_"} (1 .. 8);
    push @fields, map {"joint$_"} (1 .. 9);
    
    my %allowed_param = map { $_ => 1 } @fields;

    # delete any empty string elements or any from fields that aren't in %allowed_param
    for my $key (keys %{$param_href}){
        my $value = $param_href->{$key};
        $value =~ s/^\s+//;
        $value =~ s/\s+$//;
        if (($value eq '') or (not defined $allowed_param{$key})){
            delete $param_href->{$key};
        }
        else{
            $param_href->{$key} = $value;
        }

    }
    return $param_href;
}


sub show_list{
    my $list = shift;
    my $order_label = shift;

#---- open up html document and print beginning of table
#

print $app->header();

print '<html>';
print qq{<head><script language="javascript" type="text/javascript" src="${sorttable_js}"></script></head>};
print '<body BGCOLOR="#FFFFFF">';
print '<ul>';
print '<li>Click on any header to sort by that content.';
print '<li>The Sequence Number link will take you to the MP Sequence Number Page.';
print '<li>The Proposal Number link will take you to the Peer Review Report / RPS / Science Justification.';
print '<li>The ObsID link will take you to the Obscat Data Page.';
print '<li>The Edit link (if available) will take you to the USINT Obscat edit interface.';
print '<li>The ADS link (if available) will search for papers relevant to that ObsID.';
print '<li>The Status link (if available) will take you to the relevant Processing Status page. ';
print '</ul>';
print '<table class="sortable" border cellpadding=5>';
print '<tr>';
for my $col_label ('Sequence Number', 'Proposal Number', 'Target', 'ObsID',
                   'USINT edit', 'ADS search', 'Exp. Time', 'Status',
                      'Inst/Grat', 'PI', 'Observer', 'Type',
                      'Sched. Start Time', 'RA', 'Dec'){
    printf('<th align="left">%s%s</th>', 
           $col_label, 
           $col_label eq $order_label ? '<span id="sorttable_sortfwdind">&nbsp;&#9662;</span>' : "");

}
print '</tr>';



#
##
##---- Make sure a field is entered, if not return error message
##
#
#if ($field_counter == 0) {		#---- $field_counter keeps track of # of entered fields
#
#	print "<h2>Please enter a field.  If you wish to display all observations, ";
#	print " you may do so by selecting all Science Instruments.</h2>";
#    	print "<a href=\"https://icxc.harvard.edu/mta/CUS/Usint/search.html\">New Search</a>";
#	exit(0);
#}
#
##

    for my $obs (@{$list}){


#        my @code = map { my $var = $_;
#                         (my $lvar = $var ) =~ s/\W/_/g;
#                         "my \$$lvar = \$obs->{'$var'};";
#                     } keys %{$obs};
#        my $code = join("\n", @code);
#        print Dumper $code;
#        my $s = eval $code ;

        my ($seq_nbr, $prop_num, $targname, $status, $obsid, $approved_exposure_time, $instrument,
            $grating, $pi_last, $coi_last, $type, $sortday, $soe_st_sched_date, $ra, $dec ) 
            = map { $obs->{$_} }  qw( seq_nbr prop_num targname status obsid approved_exposure_time instrument
            grating pi_last coi_last type sortday soe_st_sched_date ra dec ); 
        
        print "<tr><td><a href=\"${target_cgi}$obsid\">$seq_nbr</a></td>";
        print "<td><a href=\"${prop_search}?$prop_num\">$prop_num<a></td>";
        print "<td>$targname</td>";

        print "<td><a href=\"${target_param_cgi}$obsid\">$obsid</a></td>";

        # conditional EDIT field for observations
        if (($status eq 'observed') || ($status eq 'archived') 
            || ($status eq 'discarded') || ($status eq 'canceled')) {
            print "<td>&nbsp;</td>";
        }else{
            print "<td align='center'><a href=\"${ocatdatapage}/$obsid\">Edit</a></td>";
        }

        if (($status eq 'observed') || ($status eq 'archived')){
            print "<td align='center'><a href=\"${ads_search}obsid=${obsid}\">ADS</a></td>";
        }else{
            print "<td>&nbsp;</td>";
        }

        printf "<td align='right'>%.1f</td>", $approved_exposure_time;
        
        if (($status eq 'unobserved') || ($status eq 'untriggered') || ($status eq 'discarded') || ($status eq 'canceled')) {
            print "<td>$status</td>";
        } else {
            print "<td><a href=\"${status_table}?field=ObsId&id=$obsid&out=long&tab_del=HTML\">$status</a></td>";
        }


  

        print "<td>${instrument}/${grating}</td>";
        print "<td>$pi_last&nbsp;</td>";
        print "<td>$coi_last&nbsp;</td>";
        print "<td>$type</td>";

        print "<td sorttable_customkey=\"${sortday}\">$soe_st_sched_date&nbsp;</td>";

        #---- Continue printing out entry

        printf "<td align='right'>%.2f</td>", $ra;
        printf "<td align='right'>%.2f</td></tr>\n", $dec;

    }

    if (scalar(@{$list})){
        print scalar(@{$list}) . " observations(s) match your search criteria.<br>";
    }
    print "</table>";
    ##---- if no entries, print out error message
    if (not scalar(@{$list})){
	print "<h2>There are no entries which match the selected parameters.</h2>";
    	print "<a href=\"${location}\">New Search</a>";
    }
    print "</body></html>";
}

#################################################################################
#### sim2coord: Gets the coordinates from Simbad                              ###
#################################################################################
sub sim2coord {
        my ($target_str, $tool_dir) = @_;
        my $coords = qx(${tool_dir}resolve_name.py "${target_str}");
        if (defined $coords){
            return split(" ",$coords);
        } 
        else{
          croak("Could not resolve coordinates with SIMBAD, NED, Vizier.");
        }
}



package SQL::Abstract;

=head1 NAME

SQL::Abstract - Generate SQL from Perl data structures

=head1 SYNOPSIS

    use SQL::Abstract;

    my $sql = SQL::Abstract->new;

    my($stmt, @bind) = $sql->select($table, \@fields, \%where, \@order);

    my($stmt, @bind) = $sql->insert($table, \%fieldvals || \@values);

    my($stmt, @bind) = $sql->update($table, \%fieldvals, \%where);

    my($stmt, @bind) = $sql->delete($table, \%where);

    # Then, use these in your DBI statements
    my $sth = $dbh->prepare($stmt);
    $sth->execute(@bind);

    # Just generate the WHERE clause
    my($stmt, @bind) = $sql->where(\%where, \@order);

    # Return values in the same order, for hashed queries
    # See PERFORMANCE section for more details
    my @bind = $sql->values(\%fieldvals);

=head1 DESCRIPTION

This module was inspired by the excellent L<DBIx::Abstract>.
However, in using that module I found that what I really wanted
to do was generate SQL, but still retain complete control over my
statement handles and use the DBI interface. So, I set out to
create an abstract SQL generation module.

While based on the concepts used by L<DBIx::Abstract>, there are
several important differences, especially when it comes to WHERE
clauses. I have modified the concepts used to make the SQL easier
to generate from Perl data structures and, IMO, more intuitive.
The underlying idea is for this module to do what you mean, based
on the data structures you provide it. The big advantage is that
you don't have to modify your code every time your data changes,
as this module figures it out.

To begin with, an SQL INSERT is as easy as just specifying a hash
of C<key=value> pairs:

    my %data = (
        name => 'Jimbo Bobson',
        phone => '123-456-7890',
        address => '42 Sister Lane',
        city => 'St. Louis',
        state => 'Louisiana',
    );

The SQL can then be generated with this:

    my($stmt, @bind) = $sql->insert('people', \%data);

Which would give you something like this:

    $stmt = "INSERT INTO people
                    (address, city, name, phone, state)
                    VALUES (?, ?, ?, ?, ?)";
    @bind = ('42 Sister Lane', 'St. Louis', 'Jimbo Bobson',
             '123-456-7890', 'Louisiana');

These are then used directly in your DBI code:

    my $sth = $dbh->prepare($stmt);
    $sth->execute(@bind);

In addition, you can apply SQL functions to elements of your C<%data>
by specifying an arrayref for the given hash value. For example, if
you need to execute the Oracle C<to_date> function on a value, you
can say something like this:

    my %data = (
        name => 'Bill',
        date_entered => ["to_date(?,'MM/DD/YYYY')", "03/02/2003"],
    ); 

The first value in the array is the actual SQL. Any other values are
optional and would be included in the bind values array. This gives
you:

    my($stmt, @bind) = $sql->insert('people', \%data);

    $stmt = "INSERT INTO people (name, date_entered) 
                VALUES (?, to_date(?,'MM/DD/YYYY'))";
    @bind = ('Bill', '03/02/2003');

An UPDATE is just as easy, all you change is the name of the function:

    my($stmt, @bind) = $sql->update('people', \%data);

Notice that your C<%data> isn't touched; the module will generate
the appropriately quirky SQL for you automatically. Usually you'll
want to specify a WHERE clause for your UPDATE, though, which is
where handling C<%where> hashes comes in handy...

This module can generate pretty complicated WHERE statements
easily. For example, simple C<key=value> pairs are taken to mean
equality, and if you want to see if a field is within a set
of values, you can use an arrayref. Let's say we wanted to
SELECT some data based on this criteria:

    my %where = (
       requestor => 'inna',
       worker => ['nwiger', 'rcwe', 'sfz'],
       status => { '!=', 'completed' }
    );

    my($stmt, @bind) = $sql->select('tickets', '*', \%where);

The above would give you something like this:

    $stmt = "SELECT * FROM tickets WHERE
                ( requestor = ? ) AND ( status != ? )
                AND ( worker = ? OR worker = ? OR worker = ? )";
    @bind = ('inna', 'completed', 'nwiger', 'rcwe', 'sfz');

Which you could then use in DBI code like so:

    my $sth = $dbh->prepare($stmt);
    $sth->execute(@bind);

Easy, eh?

=head1 FUNCTIONS

The functions are simple. There's one for each major SQL operation,
and a constructor you use first. The arguments are specified in a
similar order to each function (table, then fields, then a where 
clause) to try and simplify things.

=cut

use Carp;
use strict;

our $VERSION  = '1.24';
our $REVISION = '$Id: Abstract.pm 12 2006-11-30 17:05:24Z nwiger $';
our $AUTOLOAD;

# Fix SQL case, if so requested
sub _sqlcase {
    my $self = shift;
    return $self->{case} ? $_[0] : uc($_[0]);
}

# Anon copies of arrays/hashes
# Based on deep_copy example by merlyn
# http://www.stonehenge.com/merlyn/UnixReview/col30.html
sub _anoncopy {
    my $orig = shift;
    return (ref $orig eq 'HASH')  ? +{map { $_ => _anoncopy($orig->{$_}) } keys %$orig}
         : (ref $orig eq 'ARRAY') ? [map _anoncopy($_), @$orig]
         : $orig;
}

# Debug
sub _debug {
    return unless $_[0]->{debug}; shift;  # a little faster
    my $func = (caller(1))[3];
    warn "[$func] ", @_, "\n";
}

sub belch (@) {
    my($func) = (caller(1))[3];
    carp "[$func] Warning: ", @_;
}

sub puke (@) {
    my($func) = (caller(1))[3];
    croak "[$func] Fatal: ", @_;
}

# Utility functions
sub _table  {
    my $self = shift;
    my $tab  = shift;
    if (ref $tab eq 'ARRAY') {
        return join ', ', map { $self->_quote($_) } @$tab;
    } else {
        return $self->_quote($tab);
    }
}

sub _quote {
    my $self  = shift;
    my $label = shift;

    return $label
      if $label eq '*';

    return $self->{quote_char} . $label . $self->{quote_char}
      if !defined $self->{name_sep};

    return join $self->{name_sep},
        map { $self->{quote_char} . $_ . $self->{quote_char}  }
        split /\Q$self->{name_sep}\E/, $label;
}

# Conversion, if applicable
sub _convert ($) {
    my $self = shift;
    return @_ unless $self->{convert};
    my $conv = $self->_sqlcase($self->{convert});
    my @ret = map { $conv.'('.$_.')' } @_;
    return wantarray ? @ret : $ret[0];
}

# And bindtype
sub _bindtype (@) {
    my $self = shift;
    my($col,@val) = @_;
    return $self->{bindtype} eq 'columns' ? [ @_ ] : @val;
}

# Modified -logic or -nest
sub _modlogic ($) {
    my $self = shift;
    my $sym = @_ ? lc(shift) : $self->{logic};
    $sym =~ tr/_/ /;
    $sym = $self->{logic} if $sym eq 'nest';
    return $self->_sqlcase($sym);  # override join
}

=head2 new(option => 'value')

The C<new()> function takes a list of options and values, and returns
a new B<SQL::Abstract> object which can then be used to generate SQL
through the methods below. The options accepted are:

=over

=item case

If set to 'lower', then SQL will be generated in all lowercase. By
default SQL is generated in "textbook" case meaning something like:

    SELECT a_field FROM a_table WHERE some_field LIKE '%someval%'

=item cmp

This determines what the default comparison operator is. By default
it is C<=>, meaning that a hash like this:

    %where = (name => 'nwiger', email => 'nate@wiger.org');

Will generate SQL like this:

    WHERE name = 'nwiger' AND email = 'nate@wiger.org'

However, you may want loose comparisons by default, so if you set
C<cmp> to C<like> you would get SQL such as:

    WHERE name like 'nwiger' AND email like 'nate@wiger.org'

You can also override the comparsion on an individual basis - see
the huge section on L</"WHERE CLAUSES"> at the bottom.

=item logic

This determines the default logical operator for multiple WHERE
statements in arrays. By default it is "or", meaning that a WHERE
array of the form:

    @where = (
        event_date => {'>=', '2/13/99'}, 
        event_date => {'<=', '4/24/03'}, 
    );

Will generate SQL like this:

    WHERE event_date >= '2/13/99' OR event_date <= '4/24/03'

This is probably not what you want given this query, though (look
at the dates). To change the "OR" to an "AND", simply specify:

    my $sql = SQL::Abstract->new(logic => 'and');

Which will change the above C<WHERE> to:

    WHERE event_date >= '2/13/99' AND event_date <= '4/24/03'

=item convert

This will automatically convert comparisons using the specified SQL
function for both column and value. This is mostly used with an argument
of C<upper> or C<lower>, so that the SQL will have the effect of
case-insensitive "searches". For example, this:

    $sql = SQL::Abstract->new(convert => 'upper');
    %where = (keywords => 'MaKe iT CAse inSeNSItive');

Will turn out the following SQL:

    WHERE upper(keywords) like upper('MaKe iT CAse inSeNSItive')

The conversion can be C<upper()>, C<lower()>, or any other SQL function
that can be applied symmetrically to fields (actually B<SQL::Abstract> does
not validate this option; it will just pass through what you specify verbatim).

=item bindtype

This is a kludge because many databases suck. For example, you can't
just bind values using DBI's C<execute()> for Oracle C<CLOB> or C<BLOB> fields.
Instead, you have to use C<bind_param()>:

    $sth->bind_param(1, 'reg data');
    $sth->bind_param(2, $lots, {ora_type => ORA_CLOB});

The problem is, B<SQL::Abstract> will normally just return a C<@bind> array,
which loses track of which field each slot refers to. Fear not.

If you specify C<bindtype> in new, you can determine how C<@bind> is returned.
Currently, you can specify either C<normal> (default) or C<columns>. If you
specify C<columns>, you will get an array that looks like this:

    my $sql = SQL::Abstract->new(bindtype => 'columns');
    my($stmt, @bind) = $sql->insert(...);

    @bind = (
        [ 'column1', 'value1' ],
        [ 'column2', 'value2' ],
        [ 'column3', 'value3' ],
    );

You can then iterate through this manually, using DBI's C<bind_param()>.
    
    $sth->prepare($stmt);
    my $i = 1;
    for (@bind) {
        my($col, $data) = @$_;
        if ($col eq 'details' || $col eq 'comments') {
            $sth->bind_param($i, $data, {ora_type => ORA_CLOB});
        } elsif ($col eq 'image') {
            $sth->bind_param($i, $data, {ora_type => ORA_BLOB});
        } else {
            $sth->bind_param($i, $data);
        }
        $i++;
    }
    $sth->execute;      # execute without @bind now

Now, why would you still use B<SQL::Abstract> if you have to do this crap?
Basically, the advantage is still that you don't have to care which fields
are or are not included. You could wrap that above C<for> loop in a simple
sub called C<bind_fields()> or something and reuse it repeatedly. You still
get a layer of abstraction over manual SQL specification.

=item quote_char

This is the character that a table or column name will be quoted
with.  By default this is an empty string, but you could set it to 
the character C<`>, to generate SQL like this:

  SELECT `a_field` FROM `a_table` WHERE `some_field` LIKE '%someval%'

This is useful if you have tables or columns that are reserved words
in your database's SQL dialect.

=item name_sep

This is the character that separates a table and column name.  It is
necessary to specify this when the C<quote_char> option is selected,
so that tables and column names can be individually quoted like this:

  SELECT `table`.`one_field` FROM `table` WHERE `table`.`other_field` = 1

=back

=cut

sub new {
    my $self = shift;
    my $class = ref($self) || $self;
    my %opt = (ref $_[0] eq 'HASH') ? %{$_[0]} : @_;

    # choose our case by keeping an option around
    delete $opt{case} if $opt{case} && $opt{case} ne 'lower';

    # override logical operator
    $opt{logic} = uc $opt{logic} if $opt{logic};

    # how to return bind vars
    $opt{bindtype} ||= delete($opt{bind_type}) || 'normal';

    # default comparison is "=", but can be overridden
    $opt{cmp} ||= '=';

    # default quotation character around tables/columns
    $opt{quote_char} ||= '';

    return bless \%opt, $class;
}

=head2 insert($table, \@values || \%fieldvals)

This is the simplest function. You simply give it a table name
and either an arrayref of values or hashref of field/value pairs.
It returns an SQL INSERT statement and a list of bind values.

=cut

sub insert {
    my $self  = shift;
    my $table = $self->_table(shift);
    my $data  = shift || return;

    my $sql   = $self->_sqlcase('insert into') . " $table ";
    my(@sqlf, @sqlv, @sqlq) = ();

    my $ref = ref $data;
    if ($ref eq 'HASH') {
        for my $k (sort keys %$data) {
            my $v = $data->{$k};
            my $r = ref $v;
            # named fields, so must save names in order
            push @sqlf, $self->_quote($k);
            if ($r eq 'ARRAY') {
                # SQL included for values
                my @val = @$v;
                push @sqlq, shift @val;
                push @sqlv, $self->_bindtype($k, @val);
            } elsif ($r eq 'SCALAR') {
                # embedded literal SQL
                push @sqlq, $$v;
            } else { 
                push @sqlq, '?';
                push @sqlv, $self->_bindtype($k, $v);
            }
        }
        $sql .= '(' . join(', ', @sqlf) .') '. $self->_sqlcase('values') . ' ('. join(', ', @sqlq) .')';
    } elsif ($ref eq 'ARRAY') {
        # just generate values(?,?) part
        # no names (arrayref) so can't generate bindtype
        carp "Warning: ",__PACKAGE__,"->insert called with arrayref when bindtype set"
            if $self->{bindtype} ne 'normal';
        for my $v (@$data) {
            my $r = ref $v;
            if ($r eq 'ARRAY') {
                my @val = @$v;
                push @sqlq, shift @val;
                push @sqlv, @val;
            } elsif ($r eq 'SCALAR') {
                # embedded literal SQL
                push @sqlq, $$v;
            } else { 
                push @sqlq, '?';
                push @sqlv, $v;
            }
        }
        $sql .= $self->_sqlcase('values') . ' ('. join(', ', @sqlq) .')';
    } elsif ($ref eq 'SCALAR') {
        # literal SQL
        $sql .= $$data;
    } else {
        puke "Unsupported data type specified to \$sql->insert";
    }

    return wantarray ? ($sql, @sqlv) : $sql;
}

=head2 update($table, \%fieldvals, \%where)

This takes a table, hashref of field/value pairs, and an optional
hashref WHERE clause. It returns an SQL UPDATE function and a list
of bind values.

=cut

sub update {
    my $self  = shift;
    my $table = $self->_table(shift);
    my $data  = shift || return;
    my $where = shift;

    my $sql   = $self->_sqlcase('update') . " $table " . $self->_sqlcase('set ');
    my(@sqlf, @sqlv) = ();

    puke "Unsupported data type specified to \$sql->update"
        unless ref $data eq 'HASH';

    for my $k (sort keys %$data) {
        my $v = $data->{$k};
        my $r = ref $v;
        my $label = $self->_quote($k);
        if ($r eq 'ARRAY') {
            # SQL included for values
            my @bind = @$v;
            my $sql = shift @bind;
            push @sqlf, "$label = $sql";
            push @sqlv, $self->_bindtype($k, @bind);
        } elsif ($r eq 'SCALAR') {
            # embedded literal SQL
            push @sqlf, "$label = $$v";
        } else { 
            push @sqlf, "$label = ?";
            push @sqlv, $self->_bindtype($k, $v);
        }
    }

    $sql .= join ', ', @sqlf;

    if ($where) {
        my($wsql, @wval) = $self->where($where);
        $sql .= $wsql;
        push @sqlv, @wval;
    }

    return wantarray ? ($sql, @sqlv) : $sql;
}

=head2 select($table, \@fields, \%where, \@order)

This takes a table, arrayref of fields (or '*'), optional hashref
WHERE clause, and optional arrayref order by, and returns the
corresponding SQL SELECT statement and list of bind values.

=cut

sub select {
    my $self   = shift;
    my $table  = $self->_table(shift);
    my $fields = shift || '*';
    my $where  = shift;
    my $order  = shift;

    my $f = (ref $fields eq 'ARRAY') ? join ', ', map { $self->_quote($_) } @$fields : $fields;
    my $sql = join ' ', $self->_sqlcase('select'), $f, $self->_sqlcase('from'), $table;

    my(@sqlf, @sqlv) = ();
    my($wsql, @wval) = $self->where($where, $order);
    $sql .= $wsql;
    push @sqlv, @wval;

    return wantarray ? ($sql, @sqlv) : $sql; 
}

=head2 delete($table, \%where)

This takes a table name and optional hashref WHERE clause.
It returns an SQL DELETE statement and list of bind values.

=cut

sub delete {
    my $self  = shift;
    my $table = $self->_table(shift);
    my $where = shift;

    my $sql = $self->_sqlcase('delete from') . " $table";
    my(@sqlf, @sqlv) = ();

    if ($where) {
        my($wsql, @wval) = $self->where($where);
        $sql .= $wsql;
        push @sqlv, @wval;
    }

    return wantarray ? ($sql, @sqlv) : $sql; 
}

=head2 where(\%where, \@order)

This is used to generate just the WHERE clause. For example,
if you have an arbitrary data structure and know what the
rest of your SQL is going to look like, but want an easy way
to produce a WHERE clause, use this. It returns an SQL WHERE
clause and list of bind values.

=cut

# Finally, a separate routine just to handle WHERE clauses
sub where {
    my $self  = shift;
    my $where = shift;
    my $order = shift;

    # Need a separate routine to properly wrap w/ "where"
    my $sql = '';
    my @ret = $self->_recurse_where($where);
    if (@ret) {
        my $wh = shift @ret;
        $sql .= $self->_sqlcase(' where ') . $wh if $wh;
    }

    # order by?
    if ($order) {
        $sql .= $self->_order_by($order);
    }

    return wantarray ? ($sql, @ret) : $sql; 
}


sub _recurse_where {
    local $^W = 0;  # really, you've gotta be fucking kidding me
    my $self  = shift;
    my $where = _anoncopy(shift);   # prevent destroying original
    my $ref   = ref $where || '';
    my $join  = shift || $self->{logic} ||
                    ($ref eq 'ARRAY' ? $self->_sqlcase('or') : $self->_sqlcase('and'));

    # For assembling SQL fields and values
    my(@sqlf, @sqlv) = ();

    # If an arrayref, then we join each element
    if ($ref eq 'ARRAY') {
        # need to use while() so can shift() for arrays
        my $subjoin;
        while (my $el = shift @$where) {

            # skip empty elements, otherwise get invalid trailing AND stuff
            if (my $ref2 = ref $el) {
                if ($ref2 eq 'ARRAY') {
                    next unless @$el;
                } elsif ($ref2 eq 'HASH') {
                    next unless %$el;
                    $subjoin ||= $self->_sqlcase('and');
                } elsif ($ref2 eq 'SCALAR') {
                    # literal SQL
                    push @sqlf, $$el;
                    next;
                }
                $self->_debug("$ref2(*top) means join with $subjoin");
            } else {
                # top-level arrayref with scalars, recurse in pairs
                $self->_debug("NOREF(*top) means join with $subjoin");
                $el = {$el => shift(@$where)};
            }
            my @ret = $self->_recurse_where($el, $subjoin);
            push @sqlf, shift @ret;
            push @sqlv, @ret;
        }
    }
    elsif ($ref eq 'HASH') {
        # Note: during recursion, the last element will always be a hashref,
        # since it needs to point a column => value. So this be the end.
        for my $k (sort keys %$where) {
            my $v = $where->{$k};
            my $label = $self->_quote($k);
            if ($k =~ /^-(\D+)/) {
                # special nesting, like -and, -or, -nest, so shift over
                my $subjoin = $self->_modlogic($1);
                $self->_debug("OP(-$1) means special logic ($subjoin), recursing...");
                my @ret = $self->_recurse_where($v, $subjoin);
                push @sqlf, shift @ret;
                push @sqlv, @ret;
            } elsif (! defined($v)) {
                # undef = null
                $self->_debug("UNDEF($k) means IS NULL");
                push @sqlf, $label . $self->_sqlcase(' is null');
            } elsif (ref $v eq 'ARRAY') {
                my @v = @$v;
                
                # multiple elements: multiple options
                $self->_debug("ARRAY($k) means multiple elements: [ @v ]");

                # special nesting, like -and, -or, -nest, so shift over
                my $subjoin = $self->_sqlcase('or');
                if ($v[0] =~ /^-(\D+)/) {
                    $subjoin = $self->_modlogic($1);    # override subjoin
                    $self->_debug("OP(-$1) means special logic ($subjoin), shifting...");
                    shift @v;
                }

                # map into an array of hashrefs and recurse
                my @ret = $self->_recurse_where([map { {$k => $_} } @v], $subjoin);

                # push results into our structure
                push @sqlf, shift @ret;
                push @sqlv, @ret;
            } elsif (ref $v eq 'HASH') {
                # modified operator { '!=', 'completed' }
                for my $f (sort keys %$v) {
                    my $x = $v->{$f};
                    $self->_debug("HASH($k) means modified operator: { $f }");

                    # check for the operator being "IN" or "BETWEEN" or whatever
                    if (ref $x eq 'ARRAY') {
                          if ($f =~ /^-?\s*(not[\s_]+)?(in|between)\s*$/i) {
                              my $u = $self->_modlogic($1 . $2);
                              $self->_debug("HASH($f => $x) uses special operator: [ $u ]");
                              if ($u =~ /between/i) {
                                  # SQL sucks
                                  push @sqlf, join ' ', $self->_convert($label), $u, $self->_convert('?'),
                                                        $self->_sqlcase('and'), $self->_convert('?');
                              } else {
                                  push @sqlf, join ' ', $self->_convert($label), $u, '(',
                                                  join(', ', map { $self->_convert('?') } @$x),
                                              ')';
                              }
                              push @sqlv, $self->_bindtype($k, @$x);
                          } else {
                              # multiple elements: multiple options
                              $self->_debug("ARRAY($x) means multiple elements: [ @$x ]");
                              
                              # map into an array of hashrefs and recurse
                              my @ret = $self->_recurse_where([map { {$k => {$f, $_}} } @$x]);
                              
                              # push results into our structure
                              push @sqlf, shift @ret;
                              push @sqlv, @ret;
                          }
                    } elsif (! defined($x)) {
                        # undef = NOT null
                        my $not = ($f eq '!=' || $f eq 'not like') ? ' not' : '';
                        push @sqlf, $label . $self->_sqlcase(" is$not null");
                    } else {
                        # regular ol' value
                        $f =~ s/^-//;   # strip leading -like =>
                        $f =~ s/_/ /;   # _ => " "
                        push @sqlf, join ' ', $self->_convert($label), $self->_sqlcase($f), $self->_convert('?');
                        push @sqlv, $self->_bindtype($k, $x);
                    }
                }
            } elsif (ref $v eq 'SCALAR') {
                # literal SQL
                $self->_debug("SCALAR($k) means literal SQL: $$v");
                push @sqlf, "$label $$v";
            } else {
                # standard key => val
                $self->_debug("NOREF($k) means simple key=val: $k $self->{cmp} $v");
                push @sqlf, join ' ', $self->_convert($label), $self->_sqlcase($self->{cmp}), $self->_convert('?');
                push @sqlv, $self->_bindtype($k, $v);
            }
        }
    }
    elsif ($ref eq 'SCALAR') {
        # literal sql
        $self->_debug("SCALAR(*top) means literal SQL: $$where");
        push @sqlf, $$where;
    }
    elsif (defined $where) {
        # literal sql
        $self->_debug("NOREF(*top) means literal SQL: $where");
        push @sqlf, $where;
    }

    # assemble and return sql
    my $wsql = @sqlf ? '( ' . join(" $join ", @sqlf) . ' )' : '';
    return wantarray ? ($wsql, @sqlv) : $wsql; 
}

sub _order_by {
    my $self = shift;
    my $ref = ref $_[0];

    my @vals = $ref eq 'ARRAY'  ? @{$_[0]} :
               $ref eq 'SCALAR' ? ${$_[0]} :
               $ref eq ''       ? $_[0]    :
               puke "Unsupported data struct $ref for ORDER BY";

    my $val = join ', ', map { $self->_quote($_) } @vals;
    return $val ? $self->_sqlcase(' order by')." $val" : '';
}

=head2 values(\%data)

This just returns the values from the hash C<%data>, in the same
order that would be returned from any of the other above queries.
Using this allows you to markedly speed up your queries if you
are affecting lots of rows. See below under the L</"PERFORMANCE"> section.

=cut

sub values {
    my $self = shift;
    my $data = shift || return;
    puke "Argument to ", __PACKAGE__, "->values must be a \\%hash"
        unless ref $data eq 'HASH';
    return map { $self->_bindtype($_, $data->{$_}) } sort keys %$data;
}

=head2 generate($any, 'number', $of, \@data, $struct, \%types)

Warning: This is an experimental method and subject to change.

This returns arbitrarily generated SQL. It's a really basic shortcut.
It will return two different things, depending on return context:

    my($stmt, @bind) = $sql->generate('create table', \$table, \@fields);
    my $stmt_and_val = $sql->generate('create table', \$table, \@fields);

These would return the following:

    # First calling form
    $stmt = "CREATE TABLE test (?, ?)";
    @bind = (field1, field2);

    # Second calling form
    $stmt_and_val = "CREATE TABLE test (field1, field2)";

Depending on what you're trying to do, it's up to you to choose the correct
format. In this example, the second form is what you would want.

By the same token:

    $sql->generate('alter session', { nls_date_format => 'MM/YY' });

Might give you:

    ALTER SESSION SET nls_date_format = 'MM/YY'

You get the idea. Strings get their case twiddled, but everything
else remains verbatim.

=cut

sub generate {
    my $self  = shift;

    my(@sql, @sqlq, @sqlv);

    for (@_) {
        my $ref = ref $_;
        if ($ref eq 'HASH') {
            for my $k (sort keys %$_) {
                my $v = $_->{$k};
                my $r = ref $v;
                my $label = $self->_quote($k);
                if ($r eq 'ARRAY') {
                    # SQL included for values
                    my @bind = @$v;
                    my $sql = shift @bind;
                    push @sqlq, "$label = $sql";
                    push @sqlv, $self->_bindtype($k, @bind);
                } elsif ($r eq 'SCALAR') {
                    # embedded literal SQL
                    push @sqlq, "$label = $$v";
                } else { 
                    push @sqlq, "$label = ?";
                    push @sqlv, $self->_bindtype($k, $v);
                }
            }
            push @sql, $self->_sqlcase('set'), join ', ', @sqlq;
        } elsif ($ref eq 'ARRAY') {
            # unlike insert(), assume these are ONLY the column names, i.e. for SQL
            for my $v (@$_) {
                my $r = ref $v;
                if ($r eq 'ARRAY') {
                    my @val = @$v;
                    push @sqlq, shift @val;
                    push @sqlv, @val;
                } elsif ($r eq 'SCALAR') {
                    # embedded literal SQL
                    push @sqlq, $$v;
                } else { 
                    push @sqlq, '?';
                    push @sqlv, $v;
                }
            }
            push @sql, '(' . join(', ', @sqlq) . ')';
        } elsif ($ref eq 'SCALAR') {
            # literal SQL
            push @sql, $$_;
        } else {
            # strings get case twiddled
            push @sql, $self->_sqlcase($_);
        }
    }

    my $sql = join ' ', @sql;

    # this is pretty tricky
    # if ask for an array, return ($stmt, @bind)
    # otherwise, s/?/shift @sqlv/ to put it inline
    if (wantarray) {
        return ($sql, @sqlv);
    } else {
        1 while $sql =~ s/\?/my $d = shift(@sqlv);
                             ref $d ? $d->[1] : $d/e;
        return $sql;
    }
}

sub DESTROY { 1 }
sub AUTOLOAD {
    # This allows us to check for a local, then _form, attr
    my $self = shift;
    my($name) = $AUTOLOAD =~ /.*::(.+)/;
    return $self->generate($name, @_);
}

1;

__END__

=head1 WHERE CLAUSES

This module uses a variation on the idea from L<DBIx::Abstract>. It
is B<NOT>, repeat I<not> 100% compatible. B<The main logic of this
module is that things in arrays are OR'ed, and things in hashes
are AND'ed.>

The easiest way to explain is to show lots of examples. After
each C<%where> hash shown, it is assumed you used:

    my($stmt, @bind) = $sql->where(\%where);

However, note that the C<%where> hash can be used directly in any
of the other functions as well, as described above.

So, let's get started. To begin, a simple hash:

    my %where  = (
        user   => 'nwiger',
        status => 'completed'
    );

Is converted to SQL C<key = val> statements:

    $stmt = "WHERE user = ? AND status = ?";
    @bind = ('nwiger', 'completed');

One common thing I end up doing is having a list of values that
a field can be in. To do this, simply specify a list inside of
an arrayref:

    my %where  = (
        user   => 'nwiger',
        status => ['assigned', 'in-progress', 'pending'];
    );

This simple code will create the following:
    
    $stmt = "WHERE user = ? AND ( status = ? OR status = ? OR status = ? )";
    @bind = ('nwiger', 'assigned', 'in-progress', 'pending');

If you want to specify a different type of operator for your comparison,
you can use a hashref for a given column:

    my %where  = (
        user   => 'nwiger',
        status => { '!=', 'completed' }
    );

Which would generate:

    $stmt = "WHERE user = ? AND status != ?";
    @bind = ('nwiger', 'completed');

To test against multiple values, just enclose the values in an arrayref:

    status => { '!=', ['assigned', 'in-progress', 'pending'] };

Which would give you:

    "WHERE status != ? OR status != ? OR status != ?"

But, this is probably not what you want in this case (look at it). So
the hashref can also contain multiple pairs, in which case it is expanded
into an C<AND> of its elements:

    my %where  = (
        user   => 'nwiger',
        status => { '!=', 'completed', -not_like => 'pending%' }
    );

    # Or more dynamically, like from a form
    $where{user} = 'nwiger';
    $where{status}{'!='} = 'completed';
    $where{status}{'-not_like'} = 'pending%';

    # Both generate this
    $stmt = "WHERE user = ? AND status != ? AND status NOT LIKE ?";
    @bind = ('nwiger', 'completed', 'pending%');

To get an OR instead, you can combine it with the arrayref idea:

    my %where => (
         user => 'nwiger',
         priority => [ {'=', 2}, {'!=', 1} ]
    );

Which would generate:

    $stmt = "WHERE user = ? AND priority = ? OR priority != ?";
    @bind = ('nwiger', '2', '1');

However, there is a subtle trap if you want to say something like
this (notice the C<AND>):

    WHERE priority != ? AND priority != ?

Because, in Perl you I<can't> do this:

    priority => { '!=', 2, '!=', 1 }

As the second C<!=> key will obliterate the first. The solution
is to use the special C<-modifier> form inside an arrayref:

    priority => [ -and => {'!=', 2}, {'!=', 1} ]

Normally, these would be joined by C<OR>, but the modifier tells it
to use C<AND> instead. (Hint: You can use this in conjunction with the
C<logic> option to C<new()> in order to change the way your queries
work by default.) B<Important:> Note that the C<-modifier> goes
B<INSIDE> the arrayref, as an extra first element. This will
B<NOT> do what you think it might:

    priority => -and => [{'!=', 2}, {'!=', 1}]   # WRONG!

Here is a quick list of equivalencies, since there is some overlap:

    # Same
    status => {'!=', 'completed', 'not like', 'pending%' }
    status => [ -and => {'!=', 'completed'}, {'not like', 'pending%'}]

    # Same
    status => {'=', ['assigned', 'in-progress']}
    status => [ -or => {'=', 'assigned'}, {'=', 'in-progress'}]
    status => [ {'=', 'assigned'}, {'=', 'in-progress'} ]

In addition to C<-and> and C<-or>, there is also a special C<-nest>
operator which adds an additional set of parens, to create a subquery.
For example, to get something like this:

    $stmt = WHERE user = ? AND ( workhrs > ? OR geo = ? )
    @bind = ('nwiger', '20', 'ASIA');

You would do:

    my %where = (
         user => 'nwiger',
        -nest => [ workhrs => {'>', 20}, geo => 'ASIA' ],
    );

You can also use the hashref format to compare a list of fields using the
C<IN> comparison operator, by specifying the list as an arrayref:

    my %where  = (
        status   => 'completed',
        reportid => { -in => [567, 2335, 2] }
    );

Which would generate:

    $stmt = "WHERE status = ? AND reportid IN (?,?,?)";
    @bind = ('completed', '567', '2335', '2');

You can use this same format to use other grouping functions, such
as C<BETWEEN>, C<SOME>, and so forth. For example:

    my %where  = (
        user   => 'nwiger',
        completion_date => {
           -not_between => ['2002-10-01', '2003-02-06']
        }
    );

Would give you:

    WHERE user = ? AND completion_date NOT BETWEEN ( ? AND ? )

So far, we've seen how multiple conditions are joined with a top-level
C<AND>.  We can change this by putting the different conditions we want in
hashes and then putting those hashes in an array. For example:

    my @where = (
        {
            user   => 'nwiger',
            status => { -like => ['pending%', 'dispatched'] },
        },
        {
            user   => 'robot',
            status => 'unassigned',
        }
    );

This data structure would create the following:

    $stmt = "WHERE ( user = ? AND ( status LIKE ? OR status LIKE ? ) )
                OR ( user = ? AND status = ? ) )";
    @bind = ('nwiger', 'pending', 'dispatched', 'robot', 'unassigned');

This can be combined with the C<-nest> operator to properly group
SQL statements:

    my @where = (
         -and => [
            user => 'nwiger',
            -nest => [
                -and => [workhrs => {'>', 20}, geo => 'ASIA' ],
                -and => [workhrs => {'<', 50}, geo => 'EURO' ]
            ],
        ],
    );

That would yield:

    WHERE ( user = ? AND 
          ( ( workhrs > ? AND geo = ? )
         OR ( workhrs < ? AND geo = ? ) ) )

Finally, sometimes only literal SQL will do. If you want to include
literal SQL verbatim, you can specify it as a scalar reference, namely:

    my $inn = 'is Not Null';
    my %where = (
        priority => { '<', 2 },
        requestor => \$inn
    );

This would create:

    $stmt = "WHERE priority < ? AND requestor is Not Null";
    @bind = ('2');

Note that in this example, you only get one bind parameter back, since
the verbatim SQL is passed as part of the statement.

Of course, just to prove a point, the above can also be accomplished
with this:

    my %where = (
        priority  => { '<', 2 },
        requestor => { '!=', undef },
    );

TMTOWTDI.

These pages could go on for a while, since the nesting of the data
structures this module can handle are pretty much unlimited (the
module implements the C<WHERE> expansion as a recursive function
internally). Your best bet is to "play around" with the module a
little to see how the data structures behave, and choose the best
format for your data based on that.

And of course, all the values above will probably be replaced with
variables gotten from forms or the command line. After all, if you
knew everything ahead of time, you wouldn't have to worry about
dynamically-generating SQL and could just hardwire it into your
script.

=head1 PERFORMANCE

Thanks to some benchmarking by Mark Stosberg, it turns out that
this module is many orders of magnitude faster than using C<DBIx::Abstract>.
I must admit this wasn't an intentional design issue, but it's a
byproduct of the fact that you get to control your C<DBI> handles
yourself.

To maximize performance, use a code snippet like the following:

    # prepare a statement handle using the first row
    # and then reuse it for the rest of the rows
    my($sth, $stmt);
    for my $href (@array_of_hashrefs) {
        $stmt ||= $sql->insert('table', $href);
        $sth  ||= $dbh->prepare($stmt);
        $sth->execute($sql->values($href));
    }

The reason this works is because the keys in your C<$href> are sorted
internally by B<SQL::Abstract>. Thus, as long as your data retains
the same structure, you only have to generate the SQL the first time
around. On subsequent queries, simply use the C<values> function provided
by this module to return your values in the correct order.

=head1 FORMBUILDER

If you use my C<CGI::FormBuilder> module at all, you'll hopefully
really like this part (I do, at least). Building up a complex query
can be as simple as the following:

    #!/usr/bin/perl

    use CGI::FormBuilder;
    use SQL::Abstract;

    my $form = CGI::FormBuilder->new(...);
    my $sql  = SQL::Abstract->new;

    if ($form->submitted) {
        my $field = $form->field;
        my $id = delete $field->{id};
        my($stmt, @bind) = $sql->update('table', $field, {id => $id});
    }

Of course, you would still have to connect using C<DBI> to run the
query, but the point is that if you make your form look like your
table, the actual query script can be extremely simplistic.

If you're B<REALLY> lazy (I am), check out C<HTML::QuickTable> for
a fast interface to returning and formatting data. I frequently 
use these three modules together to write complex database query
apps in under 50 lines.

=head1 NOTES

There is not (yet) any explicit support for SQL compound logic
statements like "AND NOT". Instead, just do the de Morgan's
law transformations yourself. For example, this:

  "lname LIKE '%son%' AND NOT ( age < 10 OR age > 20 )"

Becomes:

  "lname LIKE '%son%' AND ( age >= 10 AND age <= 20 )"

With the corresponding C<%where> hash:

    %where = (
        lname => {like => '%son%'},
        age   => [-and => {'>=', 10}, {'<=', 20}],
    );

Again, remember that the C<-and> goes I<inside> the arrayref.

=head1 ACKNOWLEDGEMENTS

There are a number of individuals that have really helped out with
this module. Unfortunately, most of them submitted bugs via CPAN
so I have no idea who they are! But the people I do know are:

    Mark Stosberg (benchmarking)
    Chas Owens (initial "IN" operator support)
    Philip Collins (per-field SQL functions)
    Eric Kolve (hashref "AND" support)
    Mike Fragassi (enhancements to "BETWEEN" and "LIKE")
    Dan Kubb (support for "quote_char" and "name_sep")
    Matt Trout (DBIx::Class support)

Thanks!

=head1 BUGS

Bugs can be filed through the RT site:
https://rt.cpan.org/Dist/Display.html?Queue=SQL-Abstract

Or email: bugs-SQL-Abstract@rt.cpan.org

=head1 SEE ALSO

L<DBIx::Abstract>, L<DBI|DBI>, L<CGI::FormBuilder>, L<HTML::QuickTable>

=head1 AUTHOR

Copyright (c) 2001-2006 Nathan Wiger <nwiger@cpan.org>. All Rights Reserved.

=head1 MAINTAINERS

The DBIx-Class team, contactable via the DBIC list at <dbix-class@lists.scsys.co.uk>

Release manager Matt S Trout, mst <at> shadowcat.co.uk

=head1 LICENSE 

This module is free software; you may copy this under the terms of
the GNU General Public License, or the Artistic License, copies of
which should have accompanied your Perl kit.

=cut
