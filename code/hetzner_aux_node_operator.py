#!/usr/bin/env python3

"""
MIT License

Copyright (c) 2024 Roberto Sebastiano

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from lightkube import Client as lightkubeClient
from lightkube import AsyncClient as lightkubeAsyncClient
from lightkube.resources.apps_v1 import Deployment
from lightkube.resources.core_v1 import Node

import hcloud, sys
from hcloud.networks import NetworksClient
from hcloud.firewalls import FirewallResource

from os import environ
from pprint import pprint

DEFAULT_FIREWALL_CHECK_INTERVAL = 10

assert (
    "HCLOUD_TOKEN" in environ
), "Please export your API token in the HCLOUD_TOKEN environment variable"
token = environ["HCLOUD_TOKEN"]

# split the configmap value into a list of ids
try: 
    firewall_check_interval = int(environ["firewall_check_interval"])
except:
    firewall_check_interval = DEFAULT_FIREWALL_CHECK_INTERVAL

# split the configmap value into a list of ids
try: 
    required_network_ids = environ["required_network_ids"].split(",")
except:
    required_network_ids = []
else:
    # handle case where 'required_network_ids='
    if required_network_ids[0] == "":
        required_network_ids = []

# split the configmap value into a list of names
try:
    required_network_names = environ["required_network_names"].split(",")
except:
    required_network_names = []
else:
    # handle case where 'required_network_names='
    if required_network_names[0] == "":
        required_network_names = []

# split the configmap value into a list of ids
try:
    enforce_firewall_ids = environ["enforce_firewall_ids"].split(",")
except:
    enforce_firewall_ids = []
else:
    # handle case where 'enforce_firewall_ids='
    if enforce_firewall_ids[0] == "":
        enforce_firewall_ids = []

# split the configmap value into a list of names
try:
    enforce_firewall_names = environ["enforce_firewall_names"].split(",")
except:
    enforce_firewall_names = []
else:
    # handle case where 'enforce_firewall_ids='
    if enforce_firewall_names[0] == "":
        enforce_firewall_names = []

try:
    enforce_firewall_extra_hosts = environ["enforce_firewall_extra_hosts"].split(",")
except:
    enforce_firewall_extra_hosts = []
else:
    # handle case where 'enforce_firewall_extra_hosts='
    if enforce_firewall_extra_hosts[0] == "":
        enforce_firewall_extra_hosts = []


#required_network_names = ["network-1"]

# Connect to Hetzner Cloud API
hcloud_client = hcloud.Client(token=token)
networks_client = NetworksClient(client=hcloud_client)

def print_config():
    print(f"INFO: STARTUP CONFIG: firewall_check_interval: {firewall_check_interval}")
    print(f"INFO: STARTUP CONFIG: required_network_ids: {required_network_ids}")
    print(f"INFO: STARTUP CONFIG: required_network_names: {required_network_names}")
    print(f"INFO: STARTUP CONFIG: enforce_firewall_ids: {enforce_firewall_ids}")
    print(f"INFO: STARTUP CONFIG: enforce_firewall_names: {enforce_firewall_names}")
    print(f"INFO: STARTUP CONFIG: enforce_firewall_extra_hosts: {enforce_firewall_extra_hosts}")

# Check if a firewall exists in Hetzner Cloud
def check_hcloud_firewall_exists_by_id(firewall_id):
    try:
        firewall = hcloud_client.firewalls.get_by_id(int(firewall_id))
        if firewall:
            return True
        else:
            return False
    except Exception as e:
        #print(e)
        return False

def check_hcloud_firewall_exists_by_name(firewall_name):
    try:
        firewall = hcloud_client.firewalls.get_by_name(firewall_name)
        if firewall:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

# Check if network exists in Hetzner Cloud
def check_hcloud_network_exists_by_id(network_id):
    try:
        network = networks_client.get_by_id(int(network_id))
        if network:
            return True
        else:
            return False
    except Exception as e:
        #print(e)
        return False
    
def check_hcloud_network_exists_by_name(network_name):
    try:
        network = networks_client.get_by_name(network_name)
        if network:
            return True
        else:
            return False
    except Exception as e:
        #print(e)
        return False

def check_all_required_firewalls_exist(required_firewall_ids, required_firewall_names):
    ret = True
    for firewall_id in required_firewall_ids:
        if not check_hcloud_firewall_exists_by_id(firewall_id):
            print(f"WARNING: Firewall ID {firewall_id} not found in Hetzner Cloud")
            ret = False
    for firewall_name in required_firewall_names:
        if not check_hcloud_firewall_exists_by_name(firewall_name):
            print(f"WARNING: Firewall Name {firewall_name} not found in Hetzner Cloud")
            ret = False
    return ret

# Startup check to see if all required networks declared in the configmap exist in Hetzner Cloud
def check_all_required_networks_exist(required_network_ids, required_network_names):
    ret = True
    for network_id in required_network_ids:
        if not check_hcloud_network_exists_by_id(network_id):
            print(f"WARNING: Network ID {network_id} not found in Hetzner Cloud")
            ret = False
    for network_name in required_network_names:
        if not check_hcloud_network_exists_by_name(network_name):
            print(f"WARNING: Network Name {network_name} not found in Hetzner Cloud")
            ret = False
    return ret

def check_enforce_firewall_extra_hosts_exist(enforce_firewall_extra_hosts):
    ret = True
    for hostname in enforce_firewall_extra_hosts:
        if not hcloud_client.servers.get_by_name(hostname):
            print(f"WARNING: Firewall Enforcing Extra Host {hostname} not found in Hetzner Cloud")
            ret = False
    return ret

# Attach a given server to an existing network
def attach_server_to_network_by_id(server, network_id):
    try:
        network = networks_client.get_by_id(int(network_id))
        if server and network:
            server.attach_to_network(network)
            return True
        else:
            return False
    except Exception as e:
        # This should not fail
        print(e)
        return False

def attach_server_to_network_by_name(server, network_name):
    try:
        network_id = networks_client.get_by_name(network_name).id
        return attach_server_to_network_by_id(server, network_id)
    except Exception as e:
        # This should not fail
        print(e)
        return False

# Remediation function to attach a server to a network
def remediation_server_to_network(server, hostname, network_id=False, network_name=False):
    if network_name:
        kind = "NAME"
        check_exist = check_hcloud_network_exists_by_name(network_name)
        network=network_name
    elif network_id:
        kind = "ID"
        check_exist = check_hcloud_network_exists_by_id(network_id)
        network=network_id

    if not check_exist:
        print(f"REMEDIATION: Node {hostname} SKIPPING Required network {kind} {network} as not found in Hetzner Cloud")
    else:
        print(f"REMEDIATION: Node {hostname} Required network {kind} {network} is not attached. Attaching ..")
        if network_name:
            attach = attach_server_to_network_by_name(server, network_name)
        elif network_id:
            attach = attach_server_to_network_by_id(server, network_id)
        if attach:
            print(f"REMEDIATION: Node {hostname} Required network {kind} {network} ATTACHED SUCCESSFULLY.")
        else:
            print(f"REMEDIATION: Node {hostname} Required network {kind} {network} ATTACHMENT FAILED.")

def remediation_server_to_firewall(server, hostname, firewall_id=False, firewall_name=False):
    if firewall_name:
        kind = "NAME"
        check_exist = check_hcloud_firewall_exists_by_name(firewall_name)
        firewall=firewall_name
    elif firewall_id:
        kind = "ID"
        check_exist = check_hcloud_firewall_exists_by_id(firewall_id)
        firewall=firewall_id

    if not check_exist:
        print(f"REMEDIATION: Node {hostname} ERROR SKIPPING Required firewall {kind} {firewall} as not found in Hetzner Cloud")
    else:
        print(f"REMEDIATION: Node {hostname} Required firewall {kind} {firewall} is not attached. Attaching ..")
        if firewall_name:
            attach = attach_server_to_firewall_by_name(server, firewall_name)
        elif firewall_id:
            attach = attach_server_to_firewall_by_id(server, firewall_id)
        if attach:
            print(f"REMEDIATION: Node {hostname} Required firewall {kind} {firewall} ATTACHED SUCCESSFULLY.")
        else:
            print(f"REMEDIATION: Node {hostname} ERROR Required firewall {kind} {firewall} ATTACHMENT FAILED.")

def attach_server_to_firewall_by_id(server, firewall_id):
    try:
        firewall = hcloud_client.firewalls.get_by_id(int(firewall_id))
        if server and firewall:
            firewall.apply_to_resources([FirewallResource(type=FirewallResource.TYPE_SERVER, server=server)])
            #server.attach_to_firewall(firewall)
            return True
        else:
            return False
    except Exception as e:
        # This should not fail
        print(e)
        return False
    
def attach_server_to_firewall_by_name(server, firewall_name):
    try:
        firewall_id = hcloud_client.firewalls.get_by_name(firewall_name).id
        return attach_server_to_firewall_by_id(server, firewall_id)
    except Exception as e:
        # This should not fail
        print(e)
        return False

async def operator_networks():
    client = lightkubeAsyncClient()
    while True:
        async for op, dep in client.watch(Node):
            # We watch for added nodes only
            if op == "ADDED":
                hostname = dep.metadata.name
                ip = dep.metadata.annotations.get("alpha.kubernetes.io/provided-node-ip")
                #print(f"Node Name: {hostname}, Node IP: {ip}")
                #patch = { 'metadata': {'labels': {'test': None}} }
                server = hcloud_client.servers.get_by_name(hostname)
                if server is None:
                    print(f"ERROR: Hetzner Server {hostname} not found via API")
                    continue
                networks_dict = {}
                for private_net in server.private_net:
                    networks_dict[private_net.network.id] =  private_net.network.name
                print(f"Network Enforcer Found Server ID: {server.id} Server Name: {server.name} Private Networks: {networks_dict}" )
                for net_id in required_network_ids:
                    if net_id not in networks_dict.keys():
                        remediation_server_to_network(server, hostname=hostname, network_id=net_id)
                for net_name in required_network_names:
                    if net_name not in networks_dict.values():
                        remediation_server_to_network(server, hostname=hostname, network_name=net_name)
        await asyncio.sleep(1)

async def operator_firewall():
    client = lightkubeAsyncClient()
    first_run = True
    while True:
        servers_dict_dict = {}
        check_all_required_firewalls_exist(enforce_firewall_ids, enforce_firewall_names)
        async for node in client.list(Node):
            hostname = node.metadata.name
            ip = node.metadata.annotations.get("alpha.kubernetes.io/provided-node-ip")
            server = hcloud_client.servers.get_by_name(hostname)
            if server is None:
                print(f"ERROR: Hetzner Server {hostname} not found via API. Maybe Deleted ?")
                continue
            servers_dict_dict[hostname] = {"server": server, "firewalls": {}}
            for pubnet_firewall in server.public_net.firewalls:
                servers_dict_dict[hostname]["firewalls"].update({pubnet_firewall.firewall.id: pubnet_firewall.firewall.name})
            if first_run:
                fws = servers_dict_dict[hostname]["firewalls"]
                print(f"Firewall Enforcer Found Server ID: {server.id} Server Name: {server.name} Firewalls: {fws}")
        for hostname in enforce_firewall_extra_hosts:
            #print(f"Checking Firewall Enforcing Extra Host {hostname}")
            server = hcloud_client.servers.get_by_name(hostname)
            if not server:
                print(f"WARNING: Firewall Enforcing Extra Host {hostname} not found in Hetzner Cloud")
                continue
            servers_dict_dict[hostname] = {"server": server, "firewalls": {}}
            for pubnet_firewall in server.public_net.firewalls:
                servers_dict_dict[hostname]["firewalls"].update({pubnet_firewall.firewall.id: pubnet_firewall.firewall.name})
            if first_run:
                fws = servers_dict_dict[hostname]["firewalls"]
                print(f"Firewall Enforcer Found Server ID: {server.id} Server Name: {server.name} Firewalls: {fws}")
        #pprint(servers_dict_dict)
        for hostname, fields in servers_dict_dict.items():
            firewalls_dict = fields["firewalls"]
            server = fields["server"]
            for enforce_firewall_id in enforce_firewall_ids:
                if int(enforce_firewall_id) not in firewalls_dict.keys():
                   remediation_server_to_firewall(server, hostname=hostname, firewall_id=enforce_firewall_id)
            for enforce_firewall_name in enforce_firewall_names:
                if enforce_firewall_name not in firewalls_dict.values():
                    remediation_server_to_firewall(server, hostname=hostname, firewall_name=enforce_firewall_name)
        first_run = False
        # There is a limit of 3600 requests per hour on the Hetzner Cloud API, we make node_count * 3600 / sleep_time requests per hour
        await asyncio.sleep(firewall_check_interval)


async def async_main():
    print("Starting Hetzner Cloud Aux Network Operator..")
    print_config()
    check_all_required_networks_exist(required_network_ids, required_network_names)
    check_all_required_firewalls_exist(enforce_firewall_ids, enforce_firewall_names)
    check_enforce_firewall_extra_hosts_exist(enforce_firewall_extra_hosts)
    await asyncio.gather(operator_networks(), operator_firewall())
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(async_main())
