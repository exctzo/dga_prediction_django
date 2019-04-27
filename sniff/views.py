import json

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from .tasks import *
from . import forms
from . import models
from celery.result import AsyncResult
from celery.task.control import revoke, inspect

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

	hosts_list = models.Hosts.objects.order_by("-requests_count")
	requests_list = models.Requests.objects.order_by("date")

	return render(request, 'statistic.html', {'hosts_list':hosts_list, 'requests_list':requests_list})


