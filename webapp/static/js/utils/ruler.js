/* Show a reference ruler at the bottom of the scan image
*/

$(function() {
    // Build "dynamic" rulers by adding items
    $(".ruler[data-items]").each(function() {
        var ruler = $(this).empty(),
            len = Number(ruler.attr("data-items")) || 0,
            item = $(document.createElement("li")),
            i;
        for (i = 0; i < len; i++) {
            if (i == 0) {
                ruler.append(item.clone().text(i));
            }
            else if (i+1 == len) {
                ruler.append(item.clone().text(i+1 + " μm"));
            }
            else {
                ruler.append(item.clone().text(" "));
            }
        }
    });
    // Change the spacing programatically
    function changeRulerSpacing(spacing) {
        $(".ruler").
          css("padding-right", spacing).
          find("li").
            css("padding-left", spacing);
    }
    $("#spacing").change(function() {
        changeRulerSpacing($(this).val());
    });
});
