from django.shortcuts import render

def sniff(request) :
	return render(request, 'sniff.html')

def statistic(request) :
	return render(request, 'statistic.html')

