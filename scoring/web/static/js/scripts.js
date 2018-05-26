jQuery(document).ready(function($) {
    $(".clickable").click(function() {
        window.document.location = $(this).data("href");
    });

    $(".btn-reset").click(function(d) {
        var sendbtn = $(d.target);
        $("input[receive='btn-reset']").attr("value", sendbtn.attr("transfer"));
    });
});
