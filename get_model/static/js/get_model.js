var getdataform = $('#getDataForm');
var trainform = $('#trainForm');
var revokeform = $('#revokeTaskForm');

getdataform.submit(function () {
    $.ajax({
        type: getdataform.attr('method'),
        url: getdataform.attr('action'),
        data: getdataform.serialize(),
        success: function (data) {
            if (data.task_id != null) {
                get_task_info(data.task_id, getdataform);
            }
        },
        error: function (data) {
            console.log("Something went wrong!");
        }
    });
    return false;
});
    
trainform.submit(function () {
    $.ajax({
        type: trainform.attr('method'),
        url: trainform.attr('action'),
        data: trainform.serialize(),
        success: function (data) {
            if (data.task_id != null) {
                get_task_info(data.task_id, trainform);
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
            form.html('<div class="alert success"><strong>WARNING:  </strong>Something went wrong!</div>');
        }
    });
}

function to_train_form() {
    document.getElementById("trainForm").style.display = "block";
    document.getElementById("getDataForm").style.display = "none";
    document.getElementById("toggle1").style.color = "#333232";
    document.getElementById("toggle2").style.color = "#4CAF50";
}

function to_get_data_form() {
    document.getElementById("trainForm").style.display = "none";
    document.getElementById("getDataForm").style.display = "block";
    document.getElementById("toggle1").style.color = "#4CAF50";
    document.getElementById("toggle2").style.color = "#333232";
}