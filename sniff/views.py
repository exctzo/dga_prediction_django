import json
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from .tasks import *
from . import forms
from . import models
from . import plots
from celery.result import AsyncResult
from celery.task.control import revoke, inspect
from django.db.models import Count

def get_task_info(request):
	task_id = request.GET.get('task_id', None)
	if task_id is not None:
		try:
			task = AsyncResult(task_id)
			data = {
				'state': task.state,
				'result': task.result,
			}
			return HttpResponse(json.dumps(data), content_type='application/json')
		except Exception:
			data = {'state': 'REVOKED',}
			return HttpResponse(json.dumps(data), content_type='application/json')
	else:
		return HttpResponse('No job id given.')

def revoke_task(request):
	i = inspect()
	active_tasks = i.active()
	task_id = list(active_tasks.values())[0][0]["id"]
	revoke(task_id, terminate=True)

def sniff(request) :
	if request.method == 'POST' :
		form = forms.SniffForm(request.POST)
		if form.is_valid() :
			interface = form.cleaned_data.get("interface")
			as_proxy = form.cleaned_data.get("as_proxy")

			if as_proxy == True:
				dns_up_ip = form.cleaned_data.get("dns_up_ip")
				port = form.cleaned_data.get("port")
				task = task_capture.delay(interface, as_proxy, dns_up_ip, port)
			else: 
				task = task_capture.delay(interface, as_proxy, dns_up_ip=None, port=None)

			return HttpResponse(json.dumps({'task_id': task.id}), content_type='application/json')
	else :
		form = forms.SniffForm()
	return render(request, 'sniff.html', {'sniff_form': forms.SniffForm, 'head':'Setting parameters for sniffing:'})

def statistic(request) :
	if request.user.is_superuser:
		#hosts_list = models.Hosts.objects.order_by("-requests_count")
		hosts_list = models.Requests.objects.values('ip_src').annotate(count=Count('ip_src')).order_by("-count")
	else:
		local_dns_ip = request.user.first_name
		#hosts_list = models.Hosts.objects.filter(ip=local_dns_ip).order_by("-requests_count")
		hosts_list = models.Requests.objects.filter(ip_src=local_dns_ip).values('ip_src').annotate(count=Count('ip_src')).order_by("-count")
	requests_list = models.Requests.objects.order_by("report_date")

	return render(request, 'statistic.html', {'hosts_list':hosts_list, 'requests_list':requests_list})

def statsbyhost(request, pk):
	requested_host = pk
	#requested_host_details = models.Hosts.objects.get(ip=requested_host)
	count_requests = models.Requests.objects.filter(ip_src=requested_host).annotate(count=Count('ip_src'))
	count_dga_requests = models.Requests.objects.filter(ip_src=requested_host,dga=1).annotate(count=Count('ip_src'))
	requests_by_host = models.Requests.objects.filter(ip_src=requested_host)
	
	return render(request, 'host.html', {'host':requested_host,'count_requests':count_requests,'count_dga_requests':count_dga_requests, 'requests':requests_by_host})

class Dashboard(TemplateView):
	template_name = 'dash.html'
	def get_context_data(self, **kwargs):
		context = super(Dashboard, self).get_context_data(**kwargs)
		context['lineplot'] = plots.line_plot()
		context['piechart'] = plots.pie_chart()
		return context