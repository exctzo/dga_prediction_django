import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from .tasks import *
from . import forms
from . import models
from . import plots
from celery.result import AsyncResult
from celery.task.control import revoke, inspect
from django.db.models import Count

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def revoke_task(request):
	i = inspect()
	active_tasks = i.active()
	task_id = list(active_tasks.values())[0][0]["id"]
	revoke(task_id, terminate=True)

@login_required(login_url='/login/')
def sniff(iv_request) :
	if iv_request.method == 'POST' :
		lv_form = forms.SniffForm(iv_request.POST)
		if lv_form.is_valid() :
			lv_interface = lv_form.cleaned_data.get("interface")
			lv_as_proxy = lv_form.cleaned_data.get("as_proxy")

			if lv_as_proxy == True:
				lv_dns_up_ip = lv_form.cleaned_data.get("dns_up_ip")
				lv_port = lv_form.cleaned_data.get("port")
				lv_task = task_capture.delay(lv_interface, lv_as_proxy, lv_dns_up_ip, lv_port)
			else: 
				lv_task = task_capture.delay(lv_interface, lv_as_proxy, None, None)

			return HttpResponse(json.dumps({'task_id': lv_task.id}), content_type='application/json')
	else :
		lv_form = forms.SniffForm()
	return render(iv_request, 'sniff.html', {'sniff_form': forms.SniffForm, 'head':'Setting parameters for sniffing:'})

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def statsbyhost(request, pk):
	requested_host = pk
	#requested_host_details = models.Hosts.objects.get(ip=requested_host)
	count_requests = models.Requests.objects.filter(ip_src=requested_host).annotate(count=Count('ip_src'))
	count_dga_requests = models.Requests.objects.filter(ip_src=requested_host,dga=1).annotate(count=Count('ip_src'))
	requests_by_host = models.Requests.objects.filter(ip_src=requested_host)
	
	return render(request, 'host.html', {'host':requested_host,'count_requests':count_requests,'count_dga_requests':count_dga_requests, 'requests':requests_by_host})

@login_required(login_url='/login/')
class Dashboard(TemplateView):
	template_name = 'dash.html'
	def get_context_data(self, **kwargs):
		context = super(Dashboard, self).get_context_data(**kwargs)
		context['dga_lineplot'] = plots.dga_lineplot()
		context['hosts_piechart'] = plots.hosts_piechart()
		context['families_piechart'] = plots.families_piechart()
		return context