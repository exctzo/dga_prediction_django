import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from .tasks import *
from . import forms
from . import models
from . import plots
from celery.result import AsyncResult
from celery.task.control import revoke, inspect
from django.db.models import Count
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

@staff_member_required(login_url='/login/')
def get_task_info(iv_request):
	lv_task_id = iv_request.GET.get('task_id', None)
	if lv_task_id is not None:
		try:
			lv_task = AsyncResult(lv_task_id)
			lv_data = {
				'state': lv_task.state,
				'result': lv_task.result,
			}
			return HttpResponse(json.dumps(lv_data), content_type='application/json')
		except Exception:
			lv_data = {'state': 'REVOKED',}
			return HttpResponse(json.dumps(lv_data), content_type='application/json')
	else:
		return HttpResponse('No job id given.')

@staff_member_required(login_url='/login/')
def revoke_task(iv_request):
	lv_i = inspect()
	lv_active_tasks = lv_i.active()
	lv_task_id = list(lv_active_tasks.values())[0][0]["id"]
	revoke(lv_task_id, terminate=True)

@staff_member_required(login_url='/login/')
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
		# After restart page - lose status by active processes
		# lv_i = inspect()
		# lv_active_tasks = lv_i.active()
		# try:
		# 	lv_task_id = list(lv_active_tasks.values())[0][0]["id"]
		# 	# return HttpResponse(json.dumps({'task_id': lv_task_id}), content_type='application/json')
		# 	return render(iv_request, 'sniff2.html', {'sniff2_form': lv_form, 'task_id':lv_task_id})
		# except Exception:
		lv_form = forms.SniffForm()
		return render(iv_request, 'sniff.html', {'sniff_form': lv_form, 'head':'Setting parameters for sniffing:'})

@login_required(login_url='/login/')
def statistic(iv_request) :
	if iv_request.user.is_superuser:
		lv_hosts_list = models.Requests.objects.values('ip_src').annotate(count=Count('ip_src')).order_by("-count")
	else:
		lv_local_dns_ip = iv_request.user.first_name
		lv_hosts_list = models.Requests.objects.filter(ip_src=lv_local_dns_ip).values('ip_src').annotate(count=Count('ip_src')).order_by("-count")
	lv_requests_list = models.Requests.objects.order_by("report_date")

	return render(iv_request, 'statistic.html', {'hosts_list':lv_hosts_list, 'requests_list':lv_requests_list})

@login_required(login_url='/login/')
def statsbyhost(iv_request, pk):
	lv_requested_host = pk
	lv_count_requests = models.Requests.objects.filter(ip_src=lv_requested_host).annotate(count=Count('ip_src'))
	lv_count_dga_requests = models.Requests.objects.filter(ip_src=lv_requested_host,dga=1).annotate(count=Count('ip_src'))
	lv_requests_by_host = models.Requests.objects.filter(ip_src=lv_requested_host)
	
	return render(iv_request, 'host.html', {'host':lv_requested_host,'count_requests':lv_count_requests,'count_dga_requests':lv_count_dga_requests, 'requests':lv_requests_by_host})

@login_required(login_url='/login/')
@cache_page(CACHE_TTL)
def dashboard(iv_request):
	if iv_request.user.is_superuser:
		return render(iv_request, 'dash.html', {'dga_lineplot':plots.dga_lineplot(),'hosts_piechart':plots.hosts_piechart(),'families_piechart':plots.families_piechart()})
	else:
		return render(iv_request, 'dash.html', {'dga_lineplot':plots.dga_lineplot(iv_request.user.first_name),'families_piechart':plots.families_piechart(iv_request.user.first_name)})