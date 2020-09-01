var config = {
    type: 'line',
    data: {
        datasets: [
        ]
    },
    options: {
        responsive: true,
        layout: {
            padding: {
                top:0,
            }
        },
        title: {
            display: true,
            text: 'Score Trends',
            fontSize: 25,
        },
        legend: {
            display: true,
            position: 'right'
        },
        tooltips: {
            enabled: true,
        },
        hover: {
            mode: 'nearest',
            intersect: true
        },
        elements: {
            line: {
                tension: 0
            },
            point: {
                radius: 0
            },
        },
        scales: {
            xAxes: [{
                display: true,
                type: 'time',
                scaleLabel: {
                    display: false,
                    labelString: ''
                },
            }],
            yAxes: [{
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: 'Score'
                },
                ticks: {
                    maxTicksLimit:20,
                    suggestedMin: 0,
                }
            }]
        }
    }
};

function load_res(tids, cids) {
    var results = {};
    for (var i = 0; i < tids.length; i++) {
        var tid = tids[i];
        results[tid] = {};
        for (var j = 0; j < cids.length; j++) {
            var cid = cids[j];
            var id = "res-" + tid + "-" + cid;
            var td = document.getElementById(id);
            var resStr = td.textContent.replace(/'/gm, "\"");
            results[tid][cid] = JSON.parse(resStr);
        }
    }
    window.results = results;
}

function load_results(tid, cid, penalty) {
    var results = window.results[tid][cid];

    var downCount = 0;
    for (var i = 0; i < results.length; i++) {
        if (results[i][1] == 0) {
            downCount++;
            if (downCount >= 6) {
                downCount = 0;
                results[i][1] -= penalty;
            }
        } else {
            downCount = 0;
        }
    }
    return results;
}

function load_all_results(tids, cids) {
    var penalty = cids.length;
    var results = {};
    for (var i = 0; i < tids.length; i++) {
        var tid = tids[i];
        results[tid] = {};
        for (var j = 0; j < cids.length; j++) {
            var cid = cids[j];
            results[tid][cid] = load_results(tid, cid, penalty);
        }
    }
    return results;
}

function normalize_results(results) {
    for (var tid in results) {
        var num_results = 0;
        for (var cid in results[tid]) {
            num_results += results[tid][cid].length;
        }
        var point_value = 5000.0 / num_results;
        for (var cid in results[tid]) {
            var service_results = results[tid][cid];
            for (var i = 0; i < service_results.length; i++) {
                service_results[i][1] *= point_value;
            }
        }
    }
}

function randomColor () { 
    return '#' + (Math.random().toString(16) + '0000000').slice(2, 8); 
}

function create_dataset(name, series) {
    var color = randomColor();
    var dataset = {
        label: name,
        backgroundColor: color,
        borderColor: color,
        data: series,
        fill: false,
    }
    return dataset;
}

function create_series(results) {
    var series = []
    for (var i = 0; i < results.length; i++) {
        series.push({ x: results[i][0], y: results[i][1]});
        if (i > 0) {
            series[i].y += series[i-1].y;
        }
    }
    return series;
}

function create_datasets(results, tid, cids, checks) {
    var datasets = []

    var series = create_series(results[tid][0]);
    var dataset = create_dataset('Total', series);
    datasets.push(dataset);

    for (var i = 0; i < cids.length; i++) {
        var cid = cids[i];
        var service_results = results[tid][cid];
        series = create_series(service_results);
        dataset = create_dataset(checks[cid], series);
        datasets.push(dataset);
    }
    return datasets;
}

function calc_totals(results) {
    for (var tid in results) {
        var team_results = results[tid];
        team_results[0] = [];
        for (var cid in team_results) {
            if (cid != 0) {
                Array.prototype.push.apply(team_results[0], team_results[cid]);
            }
        }
        team_results[0].sort(function(a, b) {
            var x = a[0];
            var y = b[0];
            return ((x < y) ? -1 : ((x > y) ? 1 : 0));
        });
    }
}

function load_data(tids, cids, teams, checks) {
    load_res(tids, cids);
    var results = load_all_results(tids, cids);
    normalize_results(results);
    calc_totals(results);
    
    var data = {}
    for (var tid in results) {
        data[tid] = create_datasets(results, tid, cids, checks);
    }
    all_teams = []
    for (var tid in data) {
        var dataset = create_dataset(teams[tid], data[tid][0].data);
        all_teams.push(dataset);
    }
    data[0] = all_teams;
    return data;
}

function graph_dataset(tid) {
    var dataset = window.data[tid];
    config.data.datasets = dataset;
    window.scoreChart.update();
}

function calc_uptime(tids, cids) {
    var uptime = {};
    for (var i = 0; i < tids.length; i++) {
        var tid = tids[i];
        uptime[tid] = {};
        var total = 0;
        for (var j = 0; j < cids.length; j++) {
            var cid = cids[j];
            var res = window.results[tid][cid];
            var up = 0;
            var count = 0;
            for (var k = 0; k < res.length; k++) {
                if (res[k][1] > 0) {
                    up++;
                }
                count++;
            }
            uptime[tid][cid] = up / count;
            check_uptime = document.getElementById("uptime-" + tid + "-" + cid);
            check_uptime.innerHTML = (uptime[tid][cid] * 100).toFixed(2) + "%";
            total += uptime[tid][cid];
        }
        total_uptime = document.getElementById("uptime-" + tid);
        total_uptime.innerHTML = (total / cids.length * 100).toFixed(2) + "%";
    }
}

function calc_scores(tids) {
    for (var i = 0; i < tids.length; i++) {
        var tid = tids[i];
        var data = window.data[tid][0].data;
        if (data.length > 0) {
            var score = data[data.length - 1].y;
        } else {
            var score = 0;
        }
        var reset_penalty = document.getElementById("revert-" + tid).innerHTML;
        var score_td = document.getElementById("score-" + tid);
        score_td.innerHTML = Math.round(score);
    }
}
