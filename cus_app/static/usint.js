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

    //Event listener for any .removeRow button click.
    document.addEventListener("click", function(event) {
        // On any click, check if the clicked element is the remove row button
        const button = event.target.closest(".removeRow");
        //Not not a remove row button. exit the listener immediately.
        if (!button) {
            return;
        }
        // Read the.removeRow button id to find the id of the whole row and remove it.
        const removeIDarr = button.id.split("-");
        const removeID = `${removeIDarr[0]}-${removeIDarr[1]}`;

        document.getElementById(removeID)?.remove();
        // Edit the row index for all remaining rows.
        document
            .querySelectorAll(`#${removeIDarr[0]} tbody tr`)
            .forEach((row, index) => {
                renameTableRow(row, removeIDarr[0], index);
            });
    });
    
  });

function addRank(template_name, rank_list) {
    // Select set of rows in rank list table
    const rows = document.querySelectorAll(`#${rank_list} tbody tr`);
    const rowCount = rows.length;
    // Clone a new row from the rank list template hidden in the div
    const rowClone = document
        .querySelector(`#${template_name} table tr`)
        .cloneNode(true);

    renameTableRow(rowClone, rank_list, rowCount);

    document
        .querySelector(`#${rank_list} tbody`)
        .appendChild(rowClone);
}

function renameTableRow(row, rank_list, index) {
    const rowID = `${rank_list}-${index}`;
    //rename the row ID
    row.id = rowID;

    const header = row.querySelector("th");
    // Change the displayed index
    if (header) {
        header.textContent = index;
    }
    // Rename and reassign the id of the templated form input cells
    row.querySelectorAll("select, input").forEach(input => {
        const parts = input.id.split("-");
        const inputType = parts[parts.length - 1];

        input.id = `${rowID}-${inputType}`;
        input.name = `${rowID}-${inputType}`;
    });
}

function bindToggle(selectId, targetId, showValue = "Y") {
    document.getElementById(selectId).addEventListener("change", function() {
        document.getElementById(targetId).style.display =
            this.value === showValue ? "block" : "none";
    });
}