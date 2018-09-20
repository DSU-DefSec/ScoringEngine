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
            text: 'Default Credentials',
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
                    labelString: 'Percent of Default Credentials in Use'
                },
                ticks: {
                    maxTicksLimit:20,
                    suggestedMin: 0,
                    suggestedMax: 100,
                }
            }]
        }
    }
};


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
    var penalty = cids.length * 2;
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

function create_series(data) {
    var series = []
    for (var i = 0; i < data.length; i++) {
        series.push({ x: data[i][0], y: data[i][1]});
    }
    return series;
}

function create_datasets(defaults, tids, teams) {
    var datasets = []
    for (var tid in defaults) {
        var team_defaults = defaults[tid];
        var series = create_series(team_defaults);
        if (tid == 0) {
            var name = 'All Teams';
        } else {
            var name = teams[tid];
        }
        var dataset = create_dataset(name, series);
        datasets.push(dataset);
    }
    return datasets;
}

function load_data(tids) {
    var defaults = {};
    for (var i = 0; i < tids.length; i++) {
        var tid = tids[i];
        var id = "def-" + tid;
        var td = document.getElementById(id);
        var resStr = td.textContent.replace(/'/gm, "\"");
        defaults[tid] = JSON.parse(resStr);
    }

    defaults[0] = []
    for (var i = 0; i < defaults[tids[0]].length; i++) {
        var total = 0;
        for (var j = 0; j < tids.length; j++) {
            var tid = tids[j];
            total += defaults[tid][i][1];
        }
        var avg = total / tids.length;
        var time = defaults[tids[0]][i][0];
        defaults[0].push([time, avg]);
    }
    window.defaults = defaults;
}

function load_datasets(tids, teams) {
    load_data(tids);
    var datasets = create_datasets(window.defaults, tids, teams);
    config.data.datasets = datasets;
}

function graph_dataset(tid) {
    var dataset = window.data[tid];
    window.scoreChart.update();
}
