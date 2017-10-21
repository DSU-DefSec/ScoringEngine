import db

def calc_score(team_id, sla_limit, sla_penalty, max_score):
    """
    Calculate the score of the given team.

    Arguments:
        team_id (int): The ID of the team in the database
        sla_limit (int): The number of failed checks allowed before the SLA is
            violated
        sla_penalty (int): The penalty for an SLA violation
        max_score (int): The maximum possible score

    Returns:
        Dict(str->num): A dictionary containing the raw score, number of SLA
            violations, and total score for the given team
    """
    cmd = ('SELECT check_id, time, result FROM result '
           'WHERE team_id=%s ORDER BY time ASC')
    result_rows = db.get(cmd, (team_id))
    results = {}
    for check_id, time, result in result_rows:
        if check_id not in results:
            results[check_id] = []
        results[check_id].append({'time':time, 'result':int(result)})

    good_checks = 0
    total_checks = 0
    for key, result_list in results.items():
        total_checks += len(result_list)
        good_checks += sum([1 for r in result_list if r['result'] == 1])
    raw_score = max_score * (good_checks/total_checks)

    slas = 0
    for key, result_list in results.items():
        slas += sla_violations(result_list, sla_limit)
    score = raw_score - slas * sla_penalty
    return {'raw_score':raw_score, 'slas':slas, 'score':score}

def sla_violations(self, results, sla_limit):
    """
    Calculate the number of SLA violations in the given list of results.

    Arguments:
        results (List(Dict(str->obj))): A list of result dictionaries. Each 
            result dictionary contains the time of the check and the result of
            the check
        sla_limit (int): The number of failed checks allowed before the SLA is
            violated

    Returns:
        int: The number of SLA violations
    """
    slas = 0
    run = 0
    for result in results:
        if result['result'] == 1:
            run = 0
        else:
            run += 1
            if run > sla_limit:
                slas += 1
    return slas

