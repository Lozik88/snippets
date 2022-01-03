import json
import os
import re
from sqlite3.dbapi2 import Binary
import pandas as pd
import sqlite3
import numpy as np
import toml 
import getpass
from pandas import DataFrame

from cryptography.fernet import Fernet

class FileExistsError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

def encode(obj):
    """
    Takes string, float, integer. Returns bytes value.
    """
    if isinstance(obj,(int,float,str)):
        obj = bytes(str(obj),'utf-8')
    else:
        raise Exception(f"Value must be string, float, or int. Not {type(obj)}.") 
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
    """
    Encrypts a value using a Fernet key. Decode bytes to non-bytes value.
    """
    f = Fernet(key)
    value = encode(value)
    return decode(f.encrypt(value))

def decrypt(key:bytes,value:object):
    """
    Encrypts a value using a Fernet key.
    """
    f = Fernet(key)
    if not isinstance(value,bytes):
        value=encode(value)
    return decode(f.decrypt(value))

def _check_overwrite(path,overwrite):
    "Overwrite protection. Throws an error if the file exists and overwrite is set to False."
    if os.path.exists(path) and overwrite==False:
        raise IOError(
            f"""{path} already exists. Raising exception as a precaution. 
            Set overwrite to True to overwrite the file. Ensure the old file is backed up.""")
def _check_element(conf:dict,env:str,group:str,lookup_value:str):
    """
    A validation tool to ensure we're working in a clean TOML structure.
    """
    d = {}
    matches = [k for k in conf[group].keys() if lookup_value.lower() == k.lower()]
    if len(matches)==0:
        # return None
        raise Exception(f"{lookup_value} doesn't exist. Current profile options under {group}: {', '.join(conf[group])}")
    elif len(matches)==1:
        lookup_value = matches[0]
        if not env.lower() in [k.lower() for k in conf[group][lookup_value].keys()]:
            raise Exception(f"{env} environment does not exist in {lookup_value} profile. Current options under {group}.{lookup_value}: {', '.join(conf[group][lookup_value])}")
        return lookup_value
    elif len(matches)>1:
        raise Exception(f"Duplicates exist: {matches}. Consider revising the TOML")
    return d

def _make_element(conf:dict,env:str,group:str,profile:str):
    """
    Performs a check on certain elements in the dict. If they don't exist, they are created.
    """
    if not group in conf.keys():
        conf[group] = {}
    if not profile.lower() in [v.lower() for v in conf[group].keys()]:
        conf[group][profile] = {}
    conf[group][profile][env] = {}
    return conf

def _check_env(env:str):
    """
    Validate incoming environment. Throw an error if incoming param is not in list.
    """
    if (['prod','stage','dev']).count(env.lower()) == 0:
        raise Exception('env parameter must be prod, stage, or dev')
        
def _write_config(conf_path:str,d:dict):
    """
    Write to TOML file. Returns TOML formatted string.
    """
    with open(conf_path,'w') as f:
        return toml.dump(d,f)

def read_config(conf_path:str):
    """
    Reads and existing TOML file. Returns dictionary

    Parameters
    ---
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    """
    with open(conf_path,'r') as f:  
        return toml.load(f) 

def read_key_file(
    env:str,
    conf_path:str='config.toml'
    ):
    """
    Returns secured keyfile.

    Parameters
    ---
    env : str
        Environment of the profile. Must be either prod, stage or dev.
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    """
    _check_env(env)
    conf = read_config(conf_path)
    if 'private_keys' not in conf['paths'].keys():
        raise Exception(f"path.private_keys does not exist in {conf_path} consider using make_key_file(), or manually add it.")
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

    Parameters
    ---
    env : str
        Environment of the profile. Must be either prod, stage or dev.
    key_path : str
        Path where the private key will be stored.
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    overwrite : bool (default False)
        Will throw an error if TOML file exists and is not set to False.
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
    },'servers':{},'apis':{}}
    _write_config(conf_path,template)
    return _write_config(conf_path,template)

def config_server(
    env:str
    ,server_name:str
    ,server_address:str
    ,dbname:str
    ,port:int=None
    ,username:str=None
    ,pw:str=None
    ,conf_path:str='config.toml'
    ,*kwargs
    ):
    """
    Adds a server to the TOML configuration file.

    Parameters
    ---
    env : str
        Environment of the profile. Must be either prod, stage or dev.
    server_name : str
        Nickname of the server. Not the actual server name.
    dbname : str 
        Database name
    port : int (Default None)
        Server port. 
    username : str (Default None)
        Username of the account.
    pw : str (Default None)
        Password of the account.
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    """
    _check_env(env)
    with open(conf_path) as f:
        conf = toml.load(f)
    conf = _make_element(conf,env,'servers',server_name)
    if username == None:
        username = getpass.getpass('Enter username.')
    if pw == None:
        pw = getpass.getpass('Enter password.')
    key = read_key_file(env,conf_path)
    conf['servers'][server_name][env]={
            "address":server_address,
            "database":dbname,
            "port":port,
            "username":encrypt(key,username),
            "password":encrypt(key,pw)
        }
    _write_config(conf_path,conf)

def update_server_creds(
    env:str
    ,server_name:str
    ,username:str=None
    ,pw:str=None
    ,conf_path:str='config.toml'):
    """
    Updates a servers credentials.

    Parameters
    ---
    env : str
        Environment of the profile. Must be either prod, stage or dev.
    server_name : str
        Nickname of the server. Not the actual server name.
    username : str
        Username of the account.
    pw : str
        Password of the account.
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    """
    _check_env(env)
    conf = read_config(conf_path)
    # replace server_name variable and replace using existing keyname in TOML to match case.
    server_name = _check_element(conf,env,'servers',server_name)
    if username == None:
        username = getpass.getpass('Enter username.')
    if pw == None:
        pw = getpass.getpass('Enter password.')
    key = read_key_file(env,conf_path)
    conf['servers'][server_name][env]['username'] = encrypt(key,username)
    conf['servers'][server_name][env]['password'] = encrypt(key,pw)
    _write_config(conf_path,conf)

def get_server_info(
    env:str
    ,server_name:str
    ,conf_path:str='config.toml'
    ):
    """
    Returns a dictionary containing server information.
    
    Parameters
    ---
    env : str
        Environment of the profile. Must be either prod, stage or dev.
    server_name : str
        Nickname of the server. Not the actual server name.
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    """
    _check_env(env)
    conf = read_config(conf_path)
    server_name = _check_element(conf,env,'servers',server_name)
    if not server_name.lower() in [k.lower() for k in conf['servers'].keys()]:
        raise Exception(f"{server_name} was not found in the TOML file. Check the spelling, or add the server using add_server_config()")
    if not env.lower() in [k.lower() for k in conf['servers'][server_name].keys()]:
        raise Exception(f"{server_name}'s {env} environment was not found in the TOML file. Use add_server_config() to add the server info for {env}")
    data = conf['servers'][server_name][env]
    key = read_key_file(env,conf_path)
    data['server_name'] = server_name
    data['username'] = decrypt(key,data['username'])
    data['password'] = decrypt(key,data['password'])
    return data

def config_api(
    env:str,
    api_name:str,
    url:str,
    # endpoint:dict,
    auth_creds:dict=None,
    auth_url:str=None,
    token_url:str=None,
    conf_path:str='config.toml'
    ):
    """
    Adds API info to TOML config.

    Parameters
    ---
    env : str
        Environment of the profile. Must be either prod, stage or dev.
    api_name : str
        Nickname of the api.
    auth_creds : dict (default None)
        dictionary containing autorization data.
    auth_url : str (default None)
        url used to authenticate user. All values are encrypted when written to TOML.
    token_url : str (default None)
        url used to generate user token.
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    """
    _check_env(env)
    conf = read_config(conf_path)
    # if not 'apis' in conf.keys():
    #     conf['apis'] = {}
    # if not api_name.lower() in [k.lower() for k in conf['apis'].keys()]:
    #     conf['apis'][api_name]={}
    _make_element(conf,env,'apis',api_name)
    key = read_key_file(env,conf_path)
    encrypted_auth={}
    if auth_creds != None:
        for k,v in auth_creds.items():
            encrypted_auth[k] = encrypt(key,v)

    conf['apis'][api_name][env]={
            "url":url,
            "auth_creds":encrypted_auth,
            "auth_url":auth_url,
            "token_url":token_url
        }
    _write_config(conf_path,conf)

def update_api_auth(
    env:str,
    api:str,
    auth_creds:dict,
    conf_path:str='config.toml'
    ):
    """
    Updates api's auth info.

    Parameters
    ---
    env : str
        Environment of the profile. Must be either prod, stage or dev.
    api_name : str
        Nickname of the api.
    auth_creds : dict (default None)
        dictionary containing autorization data. All values are encrypted when written to TOML.
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    """
    _check_env(env)
    conf = read_config(conf_path)
    api = _check_element(conf,env,'apis',api)
    key = read_key_file(env,conf_path)
    encrypted_auth_creds={}
    for k,v in auth_creds.items():
        encrypted_auth_creds[k]=encrypt(key,v)
    conf['apis'][api][env]['auth_creds'] = encrypted_auth_creds
    _write_config(conf_path,conf)

def get_api_info(    
    env:str
    ,api:str
    ,conf_path:str='config.toml'
    ):
    """
    Returns a dictionary of containing api information.

    Parameters
    ---
    env : str
        Environment of the profile. Must be either prod, stage or dev.
    api_name : str
        Nickname of the api.
    conf_path : str (default config.toml)
        Path of the TOML file. Defaults to the current location of the .py file.
    """
    _check_env(env)
    conf = read_config(conf_path)
    api = _check_element(conf,env,'apis',api)
    data = conf['apis'][api][env]
    key = read_key_file(env,conf_path)
    data['api'] = api
    auth_creds={}
    for k,v in data['auth_creds'].items():
        auth_creds[k]=decrypt(key,v)
    data['auth_creds'] = auth_creds
    return data

make_config_shell(overwrite=True) #should pass
for v in ['prod','stage','dev']:
    make_key_file(v,f'/home/lozik/.auth/{v}_key.json','config.toml',True)

lst=[]

config_server('prod',"SqlServer1","localhost",'AdventureWorks2021',username='lozik',pw='afca1')
lst.append(get_server_info('prod','SqlServer1'))
config_server('stage',"SqlServer1","localhost",'AdventureWorks2021',username='lozik',pw='afc#$a1')
lst.append(get_server_info('stage','SqlServer1'))
config_server('dev',"SqlServer1","localhost",'AdventureWorks2021',username='lozik',pw='afc#$a1')
lst.append(get_server_info('dev','SqlServer1'))

config_server('prod',"SqlServer1","localhost",'AdventureWorks2021',username='lozik',pw='afca1')
lst.append(get_server_info('prod','SqlServer1'))
update_server_creds('prod','sqlserver1','kizol','this is an update1')
lst.append(get_server_info('prod','SqlServer1'))
# update_server_creds('prod','SQLlserVer1','dozik','this is an update2')
# lst.append(get_server_info('prod','SqlServer1'))
# update_server_creds('prod','SQLlserVer12','dozik','this is an update2')
# lst.append(get_server_info('prod','SqlServer12'))


df = DataFrame(lst)
config_api(
    'prod'  
    ,'Kroger'
    ,url='https://api.kroger.com/v1/'
    ,auth_creds={'client_id':'lozik','client_secret':'someOauth2pw1'}
    ,auth_url='https://api.kroger.com/v1/connect/oauth2/authorize'
    ,token_url='https://api.kroger.com/v1/connect/oauth2/token'
)

print(get_api_info('prod','kroger'))
update_api_auth('prod','kroger',{'client_id':'someupdateduname','client_secret':'someupdatedpassword'})
print(get_api_info('prod','kroger'))
update_api_auth('dev','kroger',{'l':20})
""