document.addEventListener('DOMContentLoaded', () =>{
    bindToggle("dither_flag", "ditherDiv");
    bindToggle("window_flag", "timeDiv");
    bindToggle("roll_flag", "rollDiv");
    bindToggle("spwindow_flag", "windowDiv");

    bindToggle("subarray", "subarrayTr", "CUSTOM");
    bindToggle("duty_cycle", "dutyTr");

    document.getElementById("instrument").addEventListener("change", function() {
        const acis = document.querySelectorAll(".ACISDiv");
        const hrc = document.querySelectorAll(".HRCDiv");

        if (["ACIS-I", "ACIS-S"].includes(this.value)) {
            acis.forEach(el => el.style.display = "block");
            hrc.forEach(el => el.style.display = "none");
        }
        else if (["HRC-I", "HRC-S"].includes(this.value)) {
            hrc.forEach(el => el.style.display = "block");
            acis.forEach(el => el.style.display = "none");
        }
    });

    document.getElementById("addTime").addEventListener("click", () => {
        addRank("template_time_ranks", "time_ranks");
    });

    document.getElementById("addRoll").addEventListener("click", () => {
        addRank("template_roll_ranks", "roll_ranks");
    });

    document.getElementById("addWindow").addEventListener("click", () => {
        addRank("template_window_ranks", "window_ranks");
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

function bindToggle(selectId, targetId, showValue = "Y") {
    document.getElementById(selectId).addEventListener("change", function() {
        document.getElementById(targetId).style.display =
            this.value === showValue ? "block" : "none";
    });
}