var date = []
var time = []
var money = []
var dataset = []
const user_id = JSON.parse(document.getElementById('profileuser_id').textContent);

window.onload = function parselinechart() {
    var moneytsv = document.getElementById('moneytsv').innerHTML;

    moneytsv = moneytsv.trim();
    var split = moneytsv.split('\n');
    for (i = 0; i < split.length; i++) {
        // ele = split[i].split(/[\s,]+/)
        ele = split[i].split(",");
        // date.push(ele[0])
        // time.push(ele[1])
        // money.push(ele[2])
        time.push(Date.parse(ele[0]));
        money.push(parseFloat(ele[1]));
        dataset.push([Date.parse(ele[0]), parseFloat(ele[1])]);
    }
    // console.log("date",date)
    console.log("time", time)
    console.log("money", money)
    console.log("dataset", dataset)
    var chart = Highcharts.chart('container_line', {
        chart: {
            type: 'line'
        },
        title: {
            text: "Your money Report",
        },
        subtitle: {
            text: 'recharge and spend'
        },
        yAxis: {
            title: {
                text: 'Balance'
            }
        },
        xAxis: {
            type: 'time',
            type: 'datetime',
            labels: {
                format: '{value:%Y-%m-%e}'
            },
            accessibility: {
                rangeDescription: 'Time'
            }
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle'
        },
        plotOptions: {
            series: {
                label: {
                    connectorAllowed: false
                },
                pointStart: 0
            }
        },
        series: [{
            name: 'Balance Change',
            data: dataset,
        }],
        responsive: {
            rules: [{
                condition: {
                    maxWidth: 500
                },
                chartOptions: {
                    legend: {
                        layout: 'horizontal',
                        align: 'center',
                        verticalAlign: 'bottom'
                    }
                }
            }]
        }
    });
}


Highcharts.data({
    csv: document.getElementById('tsv').innerHTML,
    itemDelimiter: '\t',
    parsed: function (columns) {
        var maintask = {},
            alltasknum = 0,
            allposingnum = [],
            subtask = [],
            singletask = {},
            drilldownSeries = [],
            subcount = {};

        $.each(columns[0], function (i, name) {
            console.log("i--", i, " + name", name)
            var tasks,
                subtasks;

            var tabs = name.split(',');
            subtasks = tabs[1];
            // tasks = name.replace(subtasks, '');
            tasks = tabs[0];
            console.log("subtasks:tabs[1]", subtasks)
            console.log("tasks:", tasks)
            // mainboard
            if (!maintask[tasks]) {
                // maintask[tasks] = columns[1][i];
                maintask[tasks] = 1;
                subcount[tasks] = {};
                alltasknum += 1;
            } else {
                maintask[tasks] += 1;
                alltasknum += 1;
            }
            console.log("maintask", maintask)

            // subboard
            if (subtasks !== null) {
                if (!subcount[tasks][subtasks]) {
                    subcount[tasks][subtasks] = 1;
                } else {
                    subcount[tasks][subtasks] += 1;
                }
            }
            console.log("tasks amd subcount---", subcount)
        });

        for (var i in maintask) {
            allposingnum[i] = maintask[i];
            maintask[i] = maintask[i] * 100 / alltasknum;
        }

        for (var key1 in subcount) {
            if (!singletask[key1]) {
                singletask[key1] = [];
            }
            console.log("singletask-middld-", singletask)
            for (var key2 in subcount[key1]) {
                singletask[key1].push([key2, 100 * subcount[key1][key2] / allposingnum[key1]])
            }
        }

        $.each(maintask, function (name, y) {
            subtask.push({
                name: name,
                y: y,
                drilldown: singletask[name] ? name : null
            });
        });

        $.each(singletask, function (key, value) {
            var baselink;
            if (key.includes("Image")) {
                baselink = "finished_img_task";
            } else {
                baselink = "finished_pos_task";
            }
            drilldownSeries.push({
                name: key,
                id: key,
                data: value,
                point: {
                    events: {
                        click: function (e) {
                            console.log("name:", key, "id:", key, "data:", value);
                            // console.log(value)
                            // if key.includes("Image")
                            location.href = baselink + "_" + user_id;
                        }
                    }
                },

            });
        });
        // create pie chart

        var chart = Highcharts.chart('container', {
            chart: {
                type: 'pie'
            },
            title: {
                text: "Finished task report"
            },
            subtitle: {
                text: "you can drill down to see more details"
            },
            plotOptions: {
                series: {
                    dataLabels: {
                        enabled: true,
                        format: '{point.name} : {point.y:.1f}%',
                    }
                }
            },
            tooltip: {
                useHTML: true,
                style: {
                    pointerEvents: 'auto',
                    headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
                    pointFormat: '<a href ="{point.url}" >' +
                        '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.2f}%</b> subtasks<br/>' +
                        '<a>'
                }
            },
            series: [{
                name: "Task",
                colorByPoint: true,
                data: subtask,
            }],
            drilldown: {
                useHTML: true,
                series: drilldownSeries
            }
        });
    },
});


Highcharts.data({
    csv: document.getElementById('upload_tsv').innerHTML,
    itemDelimiter: ',',
    parsed: function (columns) {
        var up_maintask = {},
            up_alltasknum = 0,
            up_allposingnum = [],
            up_subtask = [],
            up_singletask = {},
            up_drilldownSeries = [],
            up_subcount = {};

        console.log("icolumns + columns", columns)

        $.each(columns[0], function (i, name) {
            console.log("i--", i, " + name", name)
            var tasks,
                subtasks, count;

            var tabs = name.split(',');
            subtasks = columns[1][i];
            // tasks = name.replace(subtasks, '');
            tasks = columns[0][i];
            count = parseInt(columns[2][i]);

            console.log("tasks:", tasks)
            console.log("subtasks:tabs[1]", subtasks)
            console.log("count:", count)
            // mainboard
            if (!up_maintask[tasks]) {
                up_maintask[tasks] = 1;
                up_subcount[tasks] = {};
                up_alltasknum += 1;
            } else {
                up_maintask[tasks] += 1;
                up_alltasknum += 1;
            }
            console.log("maintask", up_maintask)

            // subboard
            if (subtasks !== null) {
                if (!up_subcount[tasks][subtasks]) {
                    up_subcount[tasks][subtasks] = count;
                } else {
                    up_subcount[tasks][subtasks] += count;
                }
            }
            console.log("tasks amd subcount---", up_subcount)
        });

        for (var i in up_maintask) {
            up_allposingnum[i] = up_maintask[i];
            up_maintask[i] = up_maintask[i] * 100 / up_alltasknum;
        }

        for (var key1 in up_subcount) {
            if (!up_singletask[key1]) {
                up_singletask[key1] = [];
            }
            console.log("singletask-middld-", up_singletask)
            for (var key2 in up_subcount[key1]) {
                up_singletask[key1].push([key2, 100 * up_subcount[key1][key2] / up_allposingnum[key1]])
            }
        }

        $.each(up_maintask, function (name, y) {
            up_subtask.push({
                name: name,
                y: y,
                drilldown: up_singletask[name] ? name : null
            });
        });

        $.each(up_singletask, function (key, value) {
            var baselink;
            if (key.includes("Image")) {
                baselink = "uploaded_img_task";
            } else {
                baselink = "uploaded_pos_task";
            }
            up_drilldownSeries.push({
                name: key,
                id: key,
                data: value,
                point: {
                    events: {
                        click: function (e) {
                            console.log("name:", key, "id:", key, "data:", value);
                            // console.log(value)
                            location.href = baselink + "_" + user_id;
                        }
                    }
                },

            });
        });
        // create pie chart

        var chart = Highcharts.chart('container_upload', {
            chart: {
                type: 'pie'
            },
            title: {
                text: "Uploaded task report"
            },
            subtitle: {
                text: "you can drill down to see more details"
            },
            plotOptions: {
                series: {
                    dataLabels: {
                        enabled: true,
                        format: '{point.name} : {point.y:.1f}%',
                    }
                }
            },
            tooltip: {
                useHTML: true,
                style: {
                    pointerEvents: 'auto',
                    headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
                    pointFormat: '<a href ="{point.url}" >' +
                        '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.2f}%</b> subtasks<br/>' +
                        '<a>'
                }
            },
            series: [{
                name: "Task",
                colorByPoint: true,
                data: up_subtask,
            }],
            drilldown: {
                useHTML: true,
                series: up_drilldownSeries
            }
        });
    },
});


function reveal() {
    if (document.getElementById('tomodify').checked) {
        document.getElementById("id_username").readOnly = false;
        document.getElementById("id_first_name").readOnly = false;
        document.getElementById("id_last_name").readOnly = false;
    } else {
        document.getElementById("id_username").readOnly = true;
        document.getElementById("id_first_name").readOnly = true;
        document.getElementById("id_last_name").readOnly = true;
    }
}

function recharge() {
    if (document.getElementById('rechargebox').checked) {
        document.getElementById("amount").readOnly = false;
    } else {
        document.getElementById("amount").readOnly = true;
    }
}


