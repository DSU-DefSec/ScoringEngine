function sum(total, num) {
    return total + num;
}

function calc_score(team_ids, check_ids) {
    var sla_limit = document.getElementById('sla-limit').value;
    var sla_penalty = document.getElementById('sla-penalty').value;
    var max_score = document.getElementById('max-score').value;

    for (tid of team_ids) {
        var slas = 0;
        var good = 0;
        var total = 0;
        for (cid of check_ids) {
            results = document.getElementById('res-'+tid+'-'+cid).innerHTML;
            results = JSON.parse(results);
            var run = 0;
            for (result of results) {
                if (result) {
                    run = 0;
                } else {
                    run += 1;
                    if (run >= sla_limit) {
                        slas += 1;
                        run = 0;
                    }
                }
            }
            good += results.reduce(sum);
            total += results.length;
        }
        var sla_penalties = slas * sla_penalty * max_score;
        var uptime = good / total;
        var raw_score = uptime * max_score;
        var total_score = raw_score - sla_penalties;

        document.getElementById(tid+'-sla-v').innerHTML = slas;
        document.getElementById(tid+'-sla-p').innerHTML = sla_penalties;
        document.getElementById(tid+'-raw-s').innerHTML = raw_score;
        document.getElementById(tid+'-score-t').innerHTML = total_score;
    }
}
