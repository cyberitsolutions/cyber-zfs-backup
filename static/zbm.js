
$(document).ready(
    function() {
        var extractValue = function(node) {
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
        };
        $("table.browsedir").tablesorter({
            //debug: true,
            textExtraction: extractValue,
            headers: {
                0: { sorter: "text" },
                1: { sorter: "digit" },
                2: { sorter: "text" },
                3: { sorter: "text" },
                4: { sorter: "isoDate" },
                5: { sorter: false }
            },
        });
    }
);

