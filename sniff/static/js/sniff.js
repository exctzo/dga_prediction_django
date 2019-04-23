var sniffform = $('#sniffForm');
var revokeform = $('#revokeTaskForm');

sniffform.submit(function () {
    $.ajax({
        type: sniffform.attr('method'),
        url: sniffform.attr('action'),
        data: sniffform.serialize(),
        success: function (data) {
            if (data.task_id != null) {
                get_task_info(data.task_id, sniffform);
            }
        },
        error: function (data) {
            console.log("Something went wrong!");
        }
    });
    return false;
});
    
revokeform.submit(function () {
    $.ajax({
        type: revokeform.attr('method'),
        url: revokeform.attr('action'),
        data: revokeform.serialize(),
        success: function (data) {
            if (data.task_id != null) {
                get_task_info(data.task_id, revokeform);
            }
        },
        error: function (data) {
            console.log("Something went wrong!");
        }
    });
    return false;
});

function get_task_info(task_id, form) {
    $.ajax({
        type: 'get',
        url: '/get_model/get_task_info/',
        data: {'task_id': task_id},
        success: function (data) {
            form.html('');
            if (data.state == 'PENDING') {
                form.html('<div class="alert"><div class="loader"></div><strong>&emsp;' + data.state + '</strong></div>');
            }
            else if (data.state == 'PROGRESS') {
                document.getElementById("revokeTaskForm").style.display = "block";
                form.html('<div class="alert info"><div class="loader"></div><strong>&emsp;' + data.state + ':  </strong>' +  data.result.step + '</div>');
            }
            else if (data.state == 'SUCCESS') {
                document.getElementById("revokeTaskForm").style.display = "none";
                form.html('<div class="alert success"><strong>' + data.state + ':  </strong>' +  data.result.step + '</div>');
            }
            else if (data.state == 'REVOKED') {
                document.getElementById("revokeTaskForm").style.display = "none";
                form.html('<div class="alert revoke"><strong>Status: ' + data.state + '</strong></div>');
            }
            if (data.state != 'SUCCESS' && data.state != 'REVOKED') {
                setTimeout(function () {
                    get_task_info(task_id, form)
                }, 1000);
            }
        },
        error: function (data) {
            form.html('<div class="alert warning"><strong>WARNING:  </strong>Something went wrong!</div>');
        }
    });
}

function check_proxy() {

    if (document.getElementById("as_proxy").checked == true){
    document.getElementById("dns_up_ip").style.display = "block";
    document.getElementById("port").style.display = "block";
    } else {
        document.getElementById("dns_up_ip").style.display = "none";
        document.getElementById("port").style.display = "none";
    }
}
