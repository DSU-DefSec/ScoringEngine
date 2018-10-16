from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vm import VM
import requests

host = 'vcloud.ialab.dsu.edu'
org_name = 'Projects'
vdc_name = 'Projects_Default'

def login(user, org, password):
   requests.packages.urllib3.disable_warnings()
   client = Client(host,
               api_version='29.0',
               verify_ssl_certs=False,
               log_file='pyvcloud.log',
               log_requests=True,
               log_headers=True,
               log_bodies=True)
   client.set_credentials(BasicLoginCredentials(user, org, password))
   return client

def load_creds():
    with open('ialab.creds', 'r') as f:
        user,passwd = f.read().split('\n')[:-1]
    return user, passwd

def get_vm(vapp_name, vm_name):
    user, passwd = load_creds()
    client = login(user, org_name, passwd)
    org = Org(client, resource=client.get_org())
    vdc = VDC(client, resource=org.get_vdc(vdc_name))
    vapp = VApp(client, resource=vdc.get_vapp(vapp_name))
    vm = VM(client, resource=vapp.get_vm(vm_name))
    return vm

def power_on(vapp_name, vm_name):
    vm = get_vm(vapp_name, vm_name)
    vm.power_on()

def power_off(vapp_name, vm_name):
    vm = get_vm(vapp_name, vm_name)
    vm.power_off()

def restart(vapp_name, vm_name):
    vm = get_vm(vapp_name, vm_name)
    vm.power_reset()

def revert(vapp_name, vm_name):
    vm = get_vm(vapp_name, vm_name)
    vm.snapshot_revert_to_current()

if __name__ == '__main__':
    revert('MySQL-mine', 'Client')
