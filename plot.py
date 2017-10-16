#!/bin/python3
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime

def plot_results(results):
    dates = []
    ys = []
    for result in results:
#        d = datetime.strptime(result.time, "%Y-%m-%d %H:%M:%S")
        d = result.time
        dates.append(d)
        ys.append(int(result.result))

    xs = matplotlib.dates.date2num(dates)

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot_date(xs, ys, fmt='k-', drawstyle='steps-post', zorder=0)
#    plt.scatter(xs, ys, c='red', zorder=1, marker='X')
    fmt = matplotlib.dates.DateFormatter('%H:%M')
    ax.xaxis.set_label_text('Time')
    ax.xaxis.set_major_formatter(fmt)
    ax.yaxis.set_label_text('Pass/Fail')
    ax.yaxis.set_ticks([0,1])
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    fname = '%s_%s.png' % (result.team.id, result.check.id)
    fig.savefig('static/imgs/%s' % fname)
    plt.close(fig)
    return fname
