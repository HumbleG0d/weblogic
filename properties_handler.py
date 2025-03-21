import os
from os.path import exists

def get_script_path():
    return os.path.dirname(os.path.realpath(__file__))

def parse_properties_file():
    propfile = get_script_path() + "/domain.properties"
    properties = {}
    if exists(propfile):
        with open(propfile, 'r') as fo:
            lines = fo.readlines()
            for line in lines:
                if "=" in line:
                    key, value = line.strip().split('=', 1)
                    properties[key] = value
    return properties

def export_properties(properties):
    exported = {
        "mwhome": properties.get('mwhome'),
        "wlshome": properties.get('wlshome'),
        "domainroot": properties.get('domainroot'),
        "approot": properties.get('approot'),
        "domainName": properties.get('domain_name'),
        "domain_username": properties.get('domain_username'),
        "domain_password": properties.get('domain_password'),
        "domain_confirm_password": properties.get('domain_confirm_password'),
        "adminPort": properties.get("admin.port"),
        "adminAddress": properties.get("admin.address"),
        "machines": properties.get("machines", "").split(','),
        "servers": properties.get("managedservers", "").split(','),
        "clusters": properties.get("clusters", "").split(',')
    }
    return exported