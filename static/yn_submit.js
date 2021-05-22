
function submit_error(msg) {
    // update the page to indicate an error (with error message msg)
    $('#errormsg').text(msg);
    $('#error').css('display','initial');
}

function submit_success() {
    // update the page to indicate a success
    $('#error').css('display','none');
    $('#choices').css('display','none');
    $('#done').css('display','initial');
}

function submit(guess) {
    // submit a guess
    const pw = Cookies.get('pass');
    fetch(`/ynsubmit?a1=${house1_addr}&a2=${house2_addr}&guess=${guess}&pass=${pw}`).then(res => {
        if (res.status==200) submit_success();
        else res.text().then(submit_error);
    }).catch(err => {
        submit_error(err);
    });
}