import requests
import urllib3

urllib3.disable_warnings()

url = 'https://142.93.9.12/'
with open('ialab.token', 'r') as f:
    token = f.read().strip()

def power_on(vapp, vm):
    resp = requests.post(url, data={'token': token, 'vapp':vapp, 'vm':vm, 'action': 'power on'}, verify=False)
    return resp.text

def power_off(vapp, vm):
    resp = requests.post(url, data={'token': token, 'vapp':vapp, 'vm':vm, 'action': 'power off'}, verify=False)
    return resp.text

def restart(vapp, vm):
    resp = requests.post(url, data={'token': token, 'vapp':vapp, 'vm':vm, 'action': 'restart'}, verify=False)
    return resp.text

def revert(vapp, vm):
    resp = requests.post(url, data={'token': token, 'vapp':vapp, 'vm':vm, 'action': 'revert'}, verify=False)
    return resp.text
