from django import forms

import os
import netifaces as ni

class RevokeTaskForm(forms.Form) :
    action = forms.CharField(max_length=60, widget=forms.HiddenInput())


class SniffForm(forms.Form) :

    # Interface
    interfaces = os.listdir('/sys/class/net/')
    list_interfaces = []
    for int in interfaces:
        list_interfaces.append((int,int))
    INTERFACE_CHOICES = tuple(list_interfaces)
    interface = forms.ChoiceField(label="Interface", choices=INTERFACE_CHOICES, widget=forms.Select(), required=True)

    # AS PROXY
    as_proxy = forms.BooleanField(label="As proxy?", widget=forms.CheckboxInput(attrs={'id': 'as_proxy', 'onclick': 'check_proxy()'}), required=False)

    # DNS-UP IP
    gws = ni.gateways()
    gateway_ip = gws['default'][ni.AF_INET][0]
    dns_up_ip = forms.GenericIPAddressField(label="DNS-UP IP address", widget=forms.TextInput(attrs={'id': 'dns_up_ip', 'style': 'display:none'}), required=False, initial=gateway_ip)

    # Port
    port = forms.IntegerField(label="Port", widget=forms.NumberInput(attrs={'id': 'port', 'style': 'display:none'}), required=False)