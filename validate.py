#!/bin/python
import dm
import json

def ip(ip_addr):
    try:
        octets = ip_addr.split('.')
        for i in range(4):
            octet = int(octets[i])
            if not (0 <= octet <= 255):
                raise Exception()
    except:
        raise Exception("%s is not an IP address" % ip_addr)

def integer(num):
    try:
        int(num)
    except:
        raise Exception("%s is not an integer" % num)

def check_function(func_str):
    try:
        parts = func_str.split('.')
        if parts[0] != 'checker':
            raise Exception()
        dm.load_module(func_str)
    except:
        raise Exception("Invalid check function: %s" % func_str)

def poller(poller_str):
    try:
        parts = poller_str.split('.')
        if parts[0] != 'polling':
            raise Exception()
        if 'Poller' not in parts[-1]:
            raise Exception()
        dm.load_module(poller_str)
    except Exception as e:
        raise e
        raise Exception("Invalid poller: %s" % poller_str)

def input_class(class_str):
    try:
        parts = class_str.split('.')
        if parts[0] != 'polling':
            raise Exception()
        if 'PollInput' not in parts[-1]:
            raise Exception()
        dm.load_module(class_str)
    except Exception as e:
        raise e
        raise Exception("Invalid PollInput: %s" % class_str)

def id_exists(id, dic):
    if str(id) not in dic:
        raise Exception("Referenced ID: %s does not exist" % id)

def jsondata(json_data):
    try:
        json.loads(json_data)
    except Exception as e:
        print(json_data)
        raise e
        raise Exception("Invalid JSON data: %s" % json_data)
