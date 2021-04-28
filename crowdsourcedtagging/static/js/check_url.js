document.getElementById("id_task_content").onchange = function () {
    const expression = /https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)?/gi;
    const regex = new RegExp(expression);
    let urls = $("#id_task_content").val().split(/\r?\n/);
    console.log(urls);
    for(let i = 0; i < urls.length; i++) {
        if(urls[i].length > 0 && !urls[i].match(regex)) {
            document.getElementById("id_upload").disabled = true
            document.getElementById("url_not_correct").style.display = "block"
            break;
        }
        document.getElementById("id_upload").disabled = false
        document.getElementById("url_not_correct").style.display = "none"
    }
}