document.addEventListener('DOMContentLoaded', () =>{
    // jQuery goes here;
    jQuery("#dither_flag").change(function(){
        if (jQuery(this).val() == 'Y'){
            jQuery("#ditherDiv").slideDown('fast');
        } else {
            jQuery("#ditherDiv").slideUp('fast');
        };
    });
    jQuery("#window_flag").change(function(){
        if (jQuery(this).val() == 'Y'){
            jQuery("#timeDiv").slideDown('fast');
        } else {
            jQuery("#timeDiv").slideUp('fast');
        };
    });
    jQuery("#roll_flag").change(function(){
        if (jQuery(this).val() == 'Y'){
            jQuery("#rollDiv").slideDown('fast');
        } else {
            jQuery("#rollDiv").slideUp('fast');
        };
    });
    jQuery("#subarray").change(function(){
        if (jQuery(this).val() == 'CUSTOM'){
            jQuery("#subarrayTr").show('fast');
        } else {
            jQuery("#subarrayTr").hide('fast');
        };
    });
    jQuery("#duty_cycle").change(function(){
        if (jQuery(this).val() == 'Y'){
            jQuery("#dutyTr").show('fast');
        } else {
            jQuery("#dutyTr").hide('fast');
        };
    });
    jQuery("#spwindow_flag").change(function(){
        if (jQuery(this).val() == 'Y'){
            jQuery("#windowDiv").slideDown('fast');
        } else {
            jQuery("#windowDiv").slideUp('fast');
        };
    });

    jQuery("#instrument").change(function(){
        if (['ACIS-I', 'ACIS-S'].includes(jQuery(this).val())) {
            jQuery(".ACISDiv").slideDown('fast');
            jQuery(".HRCDiv").slideUp('fast'); 
        } else if (['HRC-I', 'HRC-S'].includes(jQuery(this).val())) {
            jQuery(".HRCDiv").slideDown('fast');
            jQuery(".ACISDiv").slideUp('fast');
        };
    });

    jQuery("#addTime").click(function(){
        addRank("template_time_ranks","time_ranks");
    });

    jQuery("#addRoll").click(function(){
        addRank("template_roll_ranks","roll_ranks");
    });

    jQuery("#addWindow").click(function(){
        addRank("template_window_ranks","window_ranks");
    });

    jQuery(".removeRow").click(function(){
        //ID for row removal is substring of clicked remove button id.
        var removeIDarr = jQuery(this).attr('id').split('-');
        //Selection of table and row number
        var removeID = removeIDarr[0] + "-" + removeIDarr[1];
        jQuery(`#${removeID}`).remove();
        //Rename all ranks in the table
        jQuery(`#${removeIDarr[0]} tbody`).find("tr").each(function(index){
            renameTableRow(jQuery(this),removeIDarr[0], index);
        });
    });
    
  });

function addRank(template_name, rank_list) {
    //Select set of rows in rank list table
    var rows = jQuery(`#${rank_list} tbody`).children("tr");
    var rowCount = rows.length;
    //Clone a new row from rank list template hidden in div
    var timeRowClone = jQuery(`#${template_name} table tr`).clone(true, true);
    renameTableRow(timeRowClone, rank_list, rowCount);
    jQuery(`#${rank_list} tbody`).append(timeRowClone);
};

function renameTableRow(row, rank_list, index){
    var rowID = `${rank_list}-${index}`;
    // Rename the row id
    row.attr({'id': rowID});
    // Change the displayed index
    row.children("th").text(`${index}`);
    // Rename and ReID the templated form input cells
    row.find("select, input").each(function(){
        //Find input type and use to construct new ID and Name
        var inputTypeArr = jQuery(this).attr('id').split('-');
        var inputType = inputTypeArr[inputTypeArr.length - 1];
        jQuery(this).attr({
            'id': `${rowID}-${inputType}`,
            'name': `${rowID}-${inputType}`
        });
    });
};