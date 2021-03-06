import json
import os
import re
from sqlite3.dbapi2 import Binary
import pandas as pd
import sqlite3
import numpy as np
import toml 
import getpass

from cryptography.fernet import Fernet

class FileExistsError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def check_overwrite(self):
        pass

def encode(obj):
    """
    Takes string, float, integer. Returns bytes value.
    """
    if isinstance(obj,(int,float,str)):
        obj = bytes(str(obj),'utf-8')
    else:
        raise ValueError("Value must be string, float, or int.") 
    return obj
def decode(byte:bytes):
    """
    Takes bytes value. Returns original value.
    """
    v = byte.decode('utf-8')
    if v.replace(".","",1).isdigit():
        if v.count(".")==1:
            v=float(v)
        else:
            v=int(v)
    return v
def encrypt(key:bytes,value:object):
    f = Fernet(key)
    value = encode(value)
    return f.encrypt(value)   
def decrypt(key:bytes,value):
    f = Fernet(key)
    if not isinstance(value,bytes):
        value=encode(value)
    return f.decrypt(value)

# def _dump_key_file(d,desc,path):
#     if not os.path.exists(path):
#         with open(path,'w') as f:
#             json.dump([d],f,indent=2)
#     else:
#         with open(path) as f:
#             j = json.load(f)
#             rm_idx=None
#             for idx,i in enumerate(j):
#                 for k,v in i.items():
#                     if k=='desc' and v==desc:
#                         rm_idx = idx
#                         break
#                 if rm_idx !=None:
#                     break
#         with open(path,'w') as f:
#             if rm_idx !=None:
#                 j.pop(rm_idx)
#                 j.append(d)
#             else:
#                 j.append(d)
#             json.dump(j,f,indent=2)
# def encrypt(obj):
#     """
#     Returns dictionary of public and private key using cryptography.fernet.
#     Encrypt a string/integer OR a dict. If dict, each value will be encrypted 
#     and stored in the returned dictionary.
#     """
#     keys={}
#     key = Fernet.generate_key()
#     f = Fernet(key)
#     keys["key_prv"] = key.decode('utf-8')
#     if isinstance(obj,(str,int)):
#         keys["key_pub"] = f.encrypt(encode(obj)).decode('utf-8')
#     elif isinstance(obj,dict):
#         for k,v in obj.items():
#             keys[k]=f.encrypt(bytes(v)).decode('utf-8')
#     return keys
# def make_key_file(
#     desc:str
#     ,username:str
#     ,pw:str
#     ,prv_path:str
#     ,pub_path:str
#     ,prv_fname:str=None
#     ,pub_fname:str=None
#     ):
#     if os.path.isfile(prv_path):
#         raise ValueError(f"{prv_path} must be a directory.")
#     if os.path.isfile(pub_path):
#         raise ValueError(f"{pub_path} must be a directory.")
#     if not os.path.isdir(prv_path):
#         raise ValueError(f"Directory {prv_path} does not exist.")
#     if not os.path.isdir(pub_path):
#         raise ValueError(f"Directory {pub_path} does not exist.")
#     if prv_fname == None:
#         prv_fname = 'keys.json'
#     if pub_fname == None:
#         pub_fname = 'keys_pub.json'
#     prv_path=os.path.join(prv_path,prv_fname)
#     pub_path=os.path.join(pub_path,pub_fname)

#     key = Fernet.generate_key()
#     f = Fernet(key)
#     username = f.encrypt(username.encode('ascii'))
#     pw = f.encrypt(pw.encode('ascii'))
#     username = encrypt(username)
#     pw = encrypt(pw)
#     pub={
#         'desc':desc,
#         'username':username.decode('utf-8'),
#         'password':pw.decode('utf-8')
#     }
#     prv={
#         'desc':desc,
#         'key':key.decode('utf-8')
#     }
#     _dump_key_file(prv,desc,prv_path)
#     _dump_key_file(pub,desc,pub_path)

def _check_overwrite(path,overwrite):
    "Overwrite protection. Throws an error if the file exists and overwrite is set to False."
    if os.path.exists(path) and overwrite==False:
        raise IOError(
            f"""{path} already exists. Raising exception as a precaution. 
            Set overwrite to True to overwrite the file. Ensure the old file are backed up.""")
def _check_env(env:str):
    """
    Validate incoming environment. Throw error for mismatches.
    """
    if (['prod','stage','dev']).count(env.lower()) == 0:
        raise ValueError('env parameter must be prod, stage, or dev')
def _write_config(conf_path:str,d:dict):
    """
    Write to TOML file. Returns TOML formatted string.
    """
    with open(conf_path,'w') as f:
        return toml.dump(d,f)
def read_config(conf_path:str):
    """
    Reads and existing TOML file. Returns dictionary
    """
    with open(conf_path,'r') as f:
        return toml.load(f) 
def read_key_file(
    env:str,
    conf_path:str='config.toml'
    ):
    """
    Returns secured keyfile.
    """
    _check_env(env)
    conf = read_config(conf_path)
    key_path = conf['paths']['private_keys'][env]['path']
    with open(key_path,'r') as f:
        return encode(json.load(f)['key'])
def make_key_file(
    env:str
    ,key_path:str
    ,conf_path:str='config.toml'
    ,overwrite:bool=False
    ):
    """
    Creates .json file containing key. 
    """
    _check_overwrite(key_path,overwrite)
    _check_env(env)
    key_path = os.path.abspath(key_path)
    key = {'key':decode(Fernet.generate_key())}
    with open(key_path,'w') as f:
        json.dump(key,f) 
    conf = read_config(conf_path)
    if not env in conf['paths']['private_keys'].keys():
         conf['paths']['private_keys'][env]={}
    conf['paths']['private_keys'][env]['path'] = key_path    
    _write_config(conf_path,conf)
def make_config_shell(conf_path:str='config.toml',overwrite:bool=False):
    """
    Creates a new TOML configuration file using a predefined template.
    
    Parameters
    ---
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    overwrite : bool (default False)
        Will throw an error if TOML file exists and is not set to False.
    """
    _check_overwrite(conf_path,overwrite)
    template={
        'owner':getpass.getuser(),
        'paths':{
        "private_keys":{},"output":{},"input":{}
    },'servers':{}}
    _write_config(conf_path,template)
    return _write_config(conf_path,template)

def config_server(
    env:str
    ,server_name:str
    ,server_address:str
    ,dbname:str
    ,username:str=None
    ,pw:str=None
    ,conf_path:str='config.toml'
    ,port:int=None
    ):
    """
    Adds a server to the TOML configuration file.
    """
    _check_env(env)
    with open(conf_path) as f:
        conf = toml.load(f)
    if not 'servers' in conf.keys():
        conf['servers'] = {}
    if username == None:
        username = getpass.getpass('Enter username.')
    if pw == None:
        pw = getpass.getpass('Enter password.')
    key = read_key_file(env,conf_path)
    if not server_name.lower() in [k.lower() for k in conf['servers'].keys()]:
        conf['servers'][server_name]={}
    conf['servers'][server_name][env]={
            "address":server_address,
            "database":dbname,
            "port":port,
            "username":decode(encrypt(key,username)),
            "password":decode(encrypt(key,pw))
        }
    _write_config(conf_path,conf)
def update_server_creds(env:str,username:str,password:str):
    _check_env()
def get_server_info(
    env:str
    ,server_name:str
    ,conf_path:str='config.toml'
    ):
    """
    Returns a dictionary of containing server information.
    """
    _check_env(env)
    conf = read_config(conf_path)
    if not server_name.lower() in [k.lower() for k in conf['servers'].keys()]:
        raise ValueError(f"{server_name} was not found in the TOML file. Check the spelling, or add the server using add_server_config()")
    if not env.lower() in [k.lower() for k in conf['servers'][server_name].keys()]:
        raise ValueError(f"{server_name}'s {env} environment was not found in the TOML file. Use add_server_config() to add the server info for {env}")
    data = conf['servers'][server_name][env]
    key = read_key_file(env,conf_path)
    data['username'] = decode(decrypt(key,encode(data['username'])))
    data['password'] = decode(decrypt(key,encode(data['password'])))
    return data

# make_config_shell() #should error
make_config_shell(overwrite=True) #should pass
for v in ['prod','stage','dev']:
    make_key_file(v,f'{v}_key.json','config.toml',True)
config_server('prod',"SqlServer1","localhost",'AdventureWorks2021')
print(get_server_info('prod','SqlServer1'))
config_server('prod',"SqlServer1","localhost",'AdventureWorks2021')
print(get_server_info('prod','SqlServer1'))

config_server('prod',"SqlServer2","loc192.alhost",'okok')
print(get_server_info('prod','SqlServer2'))
config_server('prod',"SqlServer2","c192.al",'okok')
print(get_server_info('prod','SqlServer1'))

conf={
    'paths':{
        "public_keys":'public keyfile path'
    },
    'servers':{
        "SqlServer1":{
            "prod":{
                "ServerAddress":"192.168.0.1",
                "Database":"Adventureworks2021",
                "Username":"someUserName",
                "password":"someHashedValue"
            },
            "stage":{
                "ServerAddress":"192.168.0.1",
                "Database":"Adventureworks2021",
                "Username":"someUserName",
                "password":"someHashedValue" 
            },
            "dev":{
                "ServerAddress":"192.168.0.1",
                "Database":"Adventureworks2021",
                "Username":"someUserName",
                "password":"someHashedValue" 
            }
        },
        "SqlServer2":{
            "prod":{
                "ServerAddress":"localhost",
                "Database":"Adventureworks2021",
                "Username":"someUserName",
                "password":"someHashedValue",
            },
            "stage":{
                "ServerAddress":"localhost",
                "Database":"Adventureworks2021",
                "Username":"someUserName",
                "password":"someHashedValue",
            },
            "dev":{
                "ServerAddress":"localhost",
                "Database":"Adventureworks2021",
                "Username":"someUserName",
                "password":"someHashedValue",
            }
        }
    }
}
# path = os.path.dirname(__file__)
# conf_path = '/home/lozik/Desktop/config.toml'
# make_config(conf_path,conf)
# # prv_path = os.path.join(path,'keys_prv.json')
# # pub_path = os.path.join(path,'keys_pub.json')
# # make_keys('test keys3','lozik','12345test!%4$',path,path)
# {"username":'lozik',"pw":'12345test!%4$',"pin":12345}
# toml_dict = read_config(conf_path)
# esingle = encrypt("some value")
# edict = encrypt({"test1":""})

""