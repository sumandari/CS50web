$(function(){
    // username should be alphabetic, numeric or _ character
    $("#username").keyup(function(){
        username = $(this).val();
        (username.match(/^(\w+)$/)) ? $(this).val(username) : $(this).val(username.replace(/[^A-Za-z0-9_]/g,""))
    });
    // password confirmation should be match
    $("#confirmation").on({
        focusout : function(){
            let password = $("#password").val();
            let confirmation = $(this).val();
            if (password != confirmation) {
                $(this).focus();
                $("#helpConfirmation").text("password should be match")
            } else {
                $("#helpConfirmation").text("")
            }
        }
    })
    // register
    $("form#registration").submit(function(event){
        let password = $("#password").val();
        let confirmation = $("#confirmation").val();
        if (password != confirmation) {
            event.preventDefault();
            return false;
        }
    })

    $("#year").keyup(function(){
        let year = $(this).val();
        (year.match(/^[0-9]+$/g)) ? $(this).val(year) : $(this).val(year.replace(/[^0-9]/g,""));
    })
})
           