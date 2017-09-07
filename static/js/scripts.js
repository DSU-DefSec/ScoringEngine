jQuery(document).ready(function($) {
    $(".clickable-row td:not(.no-clickable)").click(function() {
        window.document.location = $(this).parent().data("href");
    });

    $(".btn-reset").click(function(d) {
        var sendbtn = $(d.target);
        $("input[receive='btn-reset']").attr("value", sendbtn.attr("transfer"));
    });
});
