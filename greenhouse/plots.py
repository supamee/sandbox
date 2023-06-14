from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as md
import matplotlib.pyplot as plt
import io
import random
import base64
from datetime import datetime,timedelta
import numpy as np
def time_to_datetime(timestamps):
    new_time=[]
    for t in timestamps:
        new_time.append(datetime.fromtimestamp(t))
    return new_time

def plot_my_data(xs,ys,labs):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    if isinstance(ys[0],list):
        for i in range(len(ys)):
            axis.plot(xs, ys[i],label = labs[i])
    else:
        axis.plot(xs, ys,label = labs)
    axis.legend()
    return fig
def plot_temp_hum(xs,temp,humidity):
    xs = time_to_datetime(xs)
    plt.margins(0.1)
    fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel('time')
    ax1.set_ylabel('°C', color=color)
    ax1.plot(xs, temp, color=color,label ="temperature")
    ax1.tick_params(axis='y', labelcolor=color)


    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('%humidity', color=color)  # we already handled the x-label with ax1
    ax2.plot(xs, humidity, color=color,label ="humidity")
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.autofmt_xdate(rotation=10)
    ax=plt.gca()
    xfmt = md.DateFormatter('%m/%d %H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    # ax.xticks(roatation=45)
    plt.xticks(np.arange(min(xs), max(xs)+timedelta(seconds=1), abs(max(xs)-min(xs))/5),rotation = 45)
    fig.set_size_inches(15, 8)
    fig.tight_layout()
    return fig


def create_figure():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
    axis.plot(xs, ys)
    return fig

def prep_for_html(fig):
    tmpfile = io.BytesIO()
    # FigureCanvas(fig).print_png(tmpfile)
    # return Response(tmpfile.getvalue(), mimetype='image/png')
    fig.savefig(tmpfile, format='png')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    return encoded