document.getElementById("id_task_money").onchange = function () {
    let money = parseFloat(document.getElementById("user_money").value)
    let value = parseFloat(document.getElementById("id_task_money").value)
    if (money < value) {
        document.getElementById("id_upload").disabled = true
        document.getElementById("money_not_enough").style.display = "block"
    } else {
        document.getElementById("id_upload").disabled = false
        document.getElementById("money_not_enough").style.display = "none"
    }
}