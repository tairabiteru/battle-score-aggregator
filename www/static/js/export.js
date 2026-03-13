function downloadCSV(csv, filename) {
  var csvFile = new Blob([csv], {type: "text/csv"});
}

function export_as_csv(judge) {
  return export_as_csv_raw(judge + "_table");
}

function export_as_csv_raw(row_id) {
  var csv = [];
  var rows = document.getElementById(row_id).rows;

  for (i=0; i<rows.length; i++) {
    var row = [];
    var cols = rows[i].querySelectorAll("td, th");

    for (j=0; j<cols.length; j++) {
      row.push(cols[j].innerText);
    }
    csv.push(row.join(","));
  }
  return csv.join("\n");
}

var totals_button = document.getElementById("download");
totals_button.download = "BSA-totals-table.html";
totals_button.href = "data:text/html," + document.getElementById("content").innerHTML;

document.addEventListener("DOMContentLoaded", function() {
  var judges = document.getElementsByClassName("judgeLink");
  for (judge of judges) {
    var csvFile = new Blob([export_as_csv(judge.id)], {type: "text/csv"});
    judge.download = judge.id + " Score Table.csv";
    judge.href = window.URL.createObjectURL(csvFile);
  }

  var teams = document.getElementById("download-teams");
  var csvFile = new Blob([export_as_csv_raw("teamstable")], {type: "text/csv"});
  teams.download = "BSA All Team Score Table.csv";
  teams.href = window.URL.createObjectURL(csvFile);
});
