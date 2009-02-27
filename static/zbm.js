
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

function setup_browsedir_sort() {
    $("table.browsedir").tablesorter({
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


$(document).ready(
    function() {
        setup_browsedir_sort();

        $("input.zbm_select").click(file_change);
    }
);

