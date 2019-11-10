from plotly.offline import plot
import plotly.graph_objs as go 
import pandas as pd 
from datetime import datetime
import requests
from . import models
from django.db.models import Count


def line_plot():

    data = models.Requests.objects.values('report_date').annotate(count=Count('report_date')).order_by("report_date")

    dates = [i['report_date'] for i in data]
    requests_counts = [i['count'] for i in data]

    fig = go.Figure()

    # Create and style traces
    fig.add_trace(go.Scatter(x=dates, y=requests_counts, line=dict(color='firebrick', width=4)))

    # Edit the layout
    fig.update_layout(xaxis_title='Dates',yaxis_title='Requests Count')


    plot_div = plot(fig, output_type='div',filename='line')

    return plot_div


def pie_chart():

    #labels = [i[0] for i in models.Hosts.objects.values_list('ip')]
    #values = [i[0] for i in models.Hosts.objects.values_list('requests_count')]

    data = models.Requests.objects.values('ip_src').annotate(count=Count('ip_src'))
    
    labels = [i['ip_src'] for i in data]
    values = [i['count']  for i in data]


    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    

    plot_div = plot(fig, output_type='div',filename='donut')
    return plot_div