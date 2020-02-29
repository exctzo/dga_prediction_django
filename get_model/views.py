import json
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from .tasks import *
from . import forms
from celery.result import AsyncResult
from celery.task.control import revoke, inspect
from celery import current_task

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
	# task_id = current_task.request.id
	i = inspect()
	active_tasks = i.active()
	task_id = list(active_tasks.values())[0][0]["id"]
	revoke(task_id, terminate=True)

@login_required(login_url='/login/')
def get_model(request) :
	return render(request, 'get_model.html', {
		'get_data_form': forms.GetDataForm(),
		'train_form': forms.TrainForm(),})

@login_required(login_url='/login/')
def get_data(request) :
	if request.method == 'POST' :
		form = forms.GetDataForm(request.POST)
		task = task_get_data.delay()
		return HttpResponse(json.dumps({'task_id': task.id}), content_type='application/json')
	else:
		return HttpResponse('Request metod isnt POST')

@login_required(login_url='/login/')
def train_model(request) :
	if request.method == 'POST' :
		form = forms.TrainForm(request.POST)
		if form.is_valid() :
			output_dim = form.cleaned_data.get("output_dim")
			lstm_units = form.cleaned_data.get("lstm_units")
			drop_rate = form.cleaned_data.get("drop_rate")
			act_func = form.cleaned_data.get("act_func")
			epochs = form.cleaned_data.get("epochs")
			batch_size = form.cleaned_data.get("batch_size")
			task = task_train_model.delay(output_dim, lstm_units, drop_rate, act_func, epochs, batch_size)
			return HttpResponse(json.dumps({'task_id': task.id}), content_type='application/json')
	else :
		return HttpResponse('Request metod isnt POST')
