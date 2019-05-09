import db

def get_results_list(team_ids, check_ids):
    """
    Collect the results for all teams on each check

    Arguments:
        team_ids (List(int)): The IDs of each team
        check_ids (List(int)): The IDs of each check

    Returns:
        Dict(int->Dict(int->List(bool))): A mapping of team IDs and check IDs to a list of boolean results in chronological order
    """
    # Build results dict
    results = {}
    for team_id in team_ids:
        results[team_id] = {}
        for check_id in check_ids:
            results[team_id][check_id] = []

    # Fill results dict
    result_rows = db.get('result', ['team_id', 'check_id', 'time', 'result'], orderby='time ASC')
    for team_id, check_id, time, result in result_rows:
        results[team_id][check_id].append(int(result))
    return results


def uptime(results):
    """
    Determine the uptime for each check on each team, as well as total uptime.

    Arguments:
        results (Dict(int->Dict(int->List(bool)))): A mapping of team IDs and check IDs to a list of boolean results in chronological order

    Returns:
        Dict(int->Dict(int->float)): A mapping of team and check IDs to an uptime percentage. Total uptime is stored at check ID zero which is unused.
    """
    uptime = {}

    for team_id, team_results in results.items():
        uptime[team_id] = {}
        total_checks = 0
        total_good_checks = 0

        for check_id, check_results in team_results.items():
            checks = len(check_results)
            total_checks += checks

            good_checks = sum(check_results)
            total_good_checks += good_checks

            if checks == 0:
                uptime[team_id][check_id] = 0
            else:
                uptime[team_id][check_id] = round(good_checks/float(checks)*100, 2)

        if total_checks == 0:
            uptime[team_id][0] = 0
        else:
            uptime[team_id][0] = round(total_good_checks/float(total_checks)*100, 2)
    return uptime

