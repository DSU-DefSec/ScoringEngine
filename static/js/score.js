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
                    if (run > sla_limit) {
                        slas += 1;
                    }
                }
            }
            good += results.reduce(sum);
            total += results.length;
        }
        var sla_penalties = slas*sla_penalty;
        var modified_uptime = (good - sla_penalties) / total;
        var total_score = modified_uptime * max_score;

        document.getElementById(tid+'-sla-v').innerHTML = slas;
        document.getElementById(tid+'-sla-p').innerHTML = sla_penalties;
        document.getElementById(tid+'-mod-u').innerHTML = Math.round(modified_uptime*100*100)/100 + '%';
        document.getElementById(tid+'-score-t').innerHTML = total_score;
    }
}
