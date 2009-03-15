
function extract_value(node) {
    var child = node.childNodes[0];
    if (!child) { return ''; }
    if (child.nodeName == "#text") {
        return node.innerHTML;
    } else {
        var value = child.getAttribute("value");
        if (value) {
            return value;
        } else {
            return child.innerHTML;
        }
    }
}

// Takes a table node, alternately applies CSS classes
// row_odd and row_even to its rows.
function table_odd_even(table) {
    var kids = $(table).children("tbody").children("tr").get();
    var num_kids = kids.length;
    for (var i=0; i<num_kids; ++i) {
        if (i % 2 == 0) {
            $(kids[i]).removeClass("row_odd").addClass("row_even");
        } else {
            $(kids[i]).removeClass("row_even").addClass("row_odd");
        }
    }
}

function setup_browsedir_sort() {
    var table_browsedir = $("table.browsedir");
    table_browsedir.tablesorter({
        //debug: true,
        textExtraction: extract_value,
        headers: {
            0: { sorter: false },
            1: { sorter: "text" },
            2: { sorter: "digit" },
            3: { sorter: "text" },
            4: { sorter: "text" },
            5: { sorter: "isoDate" },
            6: { sorter: false }
        },
    });
    table_browsedir.bind("sortEnd", function () { table_odd_even(table_browsedir); });
}

function setup_restore_display_sort() {
    var restore_display_tables = $("table.restore_display");
    var ts_cfg = {
        textExtraction: extract_value,
        headers: {
            0: { sorter: false },
            1: { sorter: "digit" },
            2: { sorter: "text" },
        },
    };
    restore_display_tables.tablesorter(ts_cfg);
    restore_display_tables.bind("sortEnd", function () { table_odd_even(restore_display_tables); });
}

function file_change() {
    node = this;
    share = $("#share_name").get(0).name;
    path = node.name;
    //console.debug("name: " + node.name + ", share_name: " + share_name);
    if (node.checked) {
        action = "include";
    } else {
        action = "remove";
    }
    $.getJSON("/json", {"action":action, "share":share, "path":path},
        function (data) {
            if (data[0]) {
                $.growl(data[2]);
            }
        });
    //$.growl(action + " a file", action + " " + node.name + " for share " + share_name);
}

function share_file_remove() {
    var node = this;
    var regex = /^spath:([^+]+)\+(.*)$/;
    var m = regex.exec(node.name);

    if (!m) { return; }
    var share = m[1];
    var path = m[2];

    action = "remove";

    $.getJSON("/json", {"action":action, "share":share, "path":path},
        function (data) {
            if (data[0]) {
                $.growl(data[2]);
                // Now remove the tr row.
                tr = node.parentNode.parentNode;
                $(tr).remove();

                tbl = $("table.restore_display");
                tbl.trigger("update");
                table_odd_even(tbl);
            }
        });
}


$(document).ready(
    function() {
        setup_browsedir_sort();
        setup_restore_display_sort();
        $("input.zbm_select").click(file_change);
    }
);

