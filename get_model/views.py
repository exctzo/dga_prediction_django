import json
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .tasks import *
from . import forms
from celery.result import AsyncResult
from celery.task.control import revoke, inspect
from celery import current_task

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
def get_model(iv_request) :
	return render(iv_request, 'get_model.html', {
		'get_data_form': forms.GetDataForm(),
		'train_form': forms.TrainForm(),})

@staff_member_required(login_url='/login/')
def get_data(iv_request) :
	if iv_request.method == 'POST' :
		lv_form = forms.GetDataForm(iv_request.POST)
		lv_task = task_get_data.delay()
		return HttpResponse(json.dumps({'task_id': lv_task.id}), content_type='application/json')
	else:
		return HttpResponse('Request metod isnt POST')

@staff_member_required(login_url='/login/')
def train_model(iv_request) :
	if iv_request.method == 'POST' :
		lv_form = forms.TrainForm(iv_request.POST)
		if lv_form.is_valid() :
			lv_output_dim = lv_form.cleaned_data.get("output_dim")
			lv_gru_units = lv_form.cleaned_data.get("gru_units")
			lv_drop_rate = lv_form.cleaned_data.get("drop_rate")
			lv_act_func = lv_form.cleaned_data.get("act_func")
			lv_epochs = lv_form.cleaned_data.get("epochs")
			lv_batch_size = lv_form.cleaned_data.get("batch_size")
			lv_task = task_train_model.delay(lv_output_dim, lv_gru_units, lv_drop_rate, lv_act_func, lv_epochs, lv_batch_size)
			return HttpResponse(json.dumps({'task_id': lv_task.id}), content_type='application/json')
	else :
		return HttpResponse('Request metod isnt POST')
