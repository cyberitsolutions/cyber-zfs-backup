
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
    console.debug("name: " + node.name);
}


$(document).ready(
    function() {
        setup_browsedir_sort();

        $("input.zbm_select").click(file_change);
    }
);

