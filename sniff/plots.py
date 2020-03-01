from plotly.offline import plot
import plotly.graph_objs as go 
import pandas as pd 
from datetime import datetime
import requests
from . import models
from django.db.models import Count

def dga_lineplot():

    dga = models.Requests.objects.filter(dga=1).annotate(trunced_date=Trunc('report_date', 'minute')).values('trunced_date').annotate(count=Count('trunced_date')).order_by("trunced_date")
    non_dga = models.Requests.objects.filter(dga=0).annotate(trunced_date=Trunc('report_date', 'minute')).values('trunced_date').annotate(count=Count('trunced_date')).order_by("trunced_date")

    dga_dates = [i['trunced_date'] for i in dga]
    non_dga_dates = [i['trunced_date'] for i in non_dga]
    dga_requests_counts = [i['count'] for i in dga]
    non_dga_requests_counts = [i['count'] for i in non_dga]

    fig = go.Figure()

    # Create and style traces
    fig.add_trace(go.Scatter(x=dga_dates, y=dga_requests_counts, line=dict(color='firebrick', width=4), name='DGA'))
    fig.add_trace(go.Scatter(x=non_dga_dates, y=non_dga_requests_counts, line=dict(color='forestgreen', width=4), name='Legit'))

    # Edit the layout
    fig.update_layout(xaxis_title='Dates',yaxis_title='Requests Count')


    plot_div = plot(fig, output_type='div',filename='line')

    return plot_div


def hosts_piechart():

    #labels = [i[0] for i in models.Hosts.objects.values_list('ip')]
    #values = [i[0] for i in models.Hosts.objects.values_list('requests_count')]

    data = models.Requests.objects.filter(dga=1).values('ip_src').annotate(count=Count('ip_src'))
    
    labels = [i['ip_src'] for i in data]
    values = [i['count']  for i in data]


    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    

    plot_div = plot(fig, output_type='div',filename='donut')
    return plot_div


def families_piechart():

    #labels = [i[0] for i in models.Hosts.objects.values_list('ip')]
    #values = [i[0] for i in models.Hosts.objects.values_list('requests_count')]

    data = models.Requests.objects.filter(dga=1).values('dga_subtype').annotate(count=Count('dga_subtype'))
    
    labels = [i['dga_subtype'] for i in data]
    values = [i['count']  for i in data]


    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    

    plot_div = plot(fig, output_type='div',filename='donut')
    return plot_div