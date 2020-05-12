from plotly.offline import plot
import plotly.graph_objs as go 
import pandas as pd 
from datetime import datetime
from django.db.models.functions import Trunc
import requests
from . import models
from django.db.models import Count

def dga_lineplot(iv_common_user_ip=None):
    if iv_common_user_ip is not None:
        lv_dga = models.Requests.objects.filter(ip_src=iv_common_user_ip,dga=1).annotate(trunced_date=Trunc('report_date', 'minute')).values('trunced_date').annotate(count=Count('trunced_date')).order_by("trunced_date")
        lv_non_dga = models.Requests.objects.filter(ip_src=iv_common_user_ip,dga=0).annotate(trunced_date=Trunc('report_date', 'minute')).values('trunced_date').annotate(count=Count('trunced_date')).order_by("trunced_date")
    else:
        lv_dga = models.Requests.objects.filter(dga=1).annotate(trunced_date=Trunc('report_date', 'minute')).values('trunced_date').annotate(count=Count('trunced_date')).order_by("trunced_date")
        lv_non_dga = models.Requests.objects.filter(dga=0).annotate(trunced_date=Trunc('report_date', 'minute')).values('trunced_date').annotate(count=Count('trunced_date')).order_by("trunced_date")
        
    lv_dga_dates = [i['trunced_date'] for i in lv_dga]
    lv_non_dga_dates = [i['trunced_date'] for i in lv_non_dga]
    lv_dga_requests_counts = [i['count'] for i in lv_dga]
    lv_non_dga_requests_counts = [i['count'] for i in lv_non_dga]

    lv_fig = go.Figure()

    # Create and style traces
    lv_fig.add_trace(go.Scatter(x=lv_dga_dates, y=lv_dga_requests_counts, line=dict(color='firebrick', width=4), name='DGA'))
    lv_fig.add_trace(go.Scatter(x=lv_non_dga_dates, y=lv_non_dga_requests_counts, line=dict(color='forestgreen', width=4), name='Legit'))

    # Edit the layout
    lv_fig.update_layout(xaxis_title='Dates',yaxis_title='Requests Count')

    lv_plot_div = plot(fig, output_type='div',filename='line')
    return lv_plot_div


def hosts_piechart(iv_common_user_ip=None):
    if iv_common_user_ip is not None:
        lv_data = models.Requests.objects.filter(ip_src=iv_common_user_ip,dga=1).values('ip_src').annotate(count=Count('ip_src'))
    else:
        lv_data = models.Requests.objects.filter(dga=1).values('ip_src').annotate(count=Count('ip_src'))

    lv_labels = [i['ip_src'] for i in lv_data]
    lv_values = [i['count']  for i in lv_data]

    # Edit the layout
    lv_fig = go.Figure(data=[go.Pie(labels=lv_labels, values=lv_values, hole=.3)])

    lv_plot_div = plot(lv_fig, output_type='div',filename='donut')
    return lv_plot_div


def families_piechart(iv_common_user_ip=None):
    if iv_common_user_ip is not None:
        lv_data = models.Requests.objects.filter(ip_src=iv_common_user_ip,dga=1).values('dga_subtype').annotate(count=Count('dga_subtype'))
    else:
        lv_data = models.Requests.objects.filter(dga=1).values('dga_subtype').annotate(count=Count('dga_subtype'))
    
    lv_labels = [i['dga_subtype'] for i in lv_data]
    lv_values = [i['count']  for i in lv_data]

    # Edit the layout
    lv_fig = go.Figure(data=[go.Pie(labels=lv_labels, values=lv_values, hole=.3)])
    
    lv_plot_div = plot(lv_fig, output_type='div',filename='donut')
    return lv_plot_div