import json
import os
import re
from sqlite3.dbapi2 import Binary
import pandas as pd
import sqlite3
import numpy as np
import toml 

from struct import pack, unpack
from cryptography.fernet import Fernet

def encode(obj):
    """
    Takes string or integer. Returns bytes value.
    """
    if isinstance(obj,(int,float)):
        obj = str(obj)
    obj=bytes(obj,'ascii')
    return obj 
def decode(byte:bytes):
    """
    Takes bytes value. Returns original value.
    """
    v = byte.decode('ascii')
    if v.replace(".","",1).isdigit():
        if len([i for i in v if i=="."])==1:
            v=float(v)
        else:
            v=int(v)
    return v

def encrypt(obj):
    """
    Returns dictionary of public and private key using cryptography.fernet.
    Encrypt a string/integer OR a dict. If dict, each value will be encrypted 
    and stored in the returned dictionary.
    """
    bytes()
    keys={}
    key = Fernet.generate_key()
    f = Fernet(key)
    keys["key_prv"] = key.decode('utf-8')
    if isinstance(obj,(str,int)):
        keys["key_pub"] = f.encrypt(encode(obj)).decode('utf-8')
    elif isinstance(obj,dict):
        for k,v in obj.items():
            keys[k]=f.encrypt(bytes(v)).decode('utf-8')
    return keys

def decrypt(key:str,value):
    pass
def _dump_key_file(d,desc,path):
    if not os.path.exists(path):
        with open(path,'w') as f:
            json.dump([d],f,indent=2)
    else:
        with open(path) as f:
            j = json.load(f)
            rm_idx=None
            for idx,i in enumerate(j):
                for k,v in i.items():
                    if k=='desc' and v==desc:
                        rm_idx = idx
                        break
                if rm_idx !=None:
                    break
        with open(path,'w') as f:
            if rm_idx !=None:
                j.pop(rm_idx)
                j.append(d)
            else:
                j.append(d)
            json.dump(j,f,indent=2)
def make_key_file(
    desc:str
    ,username:str
    ,pw:str
    ,prv_path:str
    ,pub_path:str
    ,prv_fname:str=None
    ,pub_fname:str=None
    ):
    if os.path.isfile(prv_path):
        raise ValueError(f"{prv_path} must be a directory.")
    if os.path.isfile(pub_path):
        raise ValueError(f"{pub_path} must be a directory.")
    if not os.path.isdir(prv_path):
        raise ValueError(f"Directory {prv_path} does not exist.")
    if not os.path.isdir(pub_path):
        raise ValueError(f"Directory {pub_path} does not exist.")
    if prv_fname == None:
        prv_fname = 'keys.json'
    if pub_fname == None:
        pub_fname = 'keys_pub.json'
    prv_path=os.path.join(prv_path,prv_fname)
    pub_path=os.path.join(pub_path,pub_fname)

    key = Fernet.generate_key()
    f = Fernet(key)
    username = f.encrypt(username.encode('ascii'))
    pw = f.encrypt(pw.encode('ascii'))
    username = encrypt(username)
    pw = encrypt(pw)
    pub={
        'desc':desc,
        'username':username.decode('utf-8'),
        'password':pw.decode('utf-8')
    }
    prv={
        'desc':desc,
        'key':key.decode('utf-8')
    }
    _dump_key_file(prv,desc,prv_path)
    _dump_key_file(pub,desc,pub_path)

def read_key_file(
    conf_path:str=None
):
    pass
def make_config(conf_path:str,d:dict):
    """
    Creates a new TOML configuration file. This will overwrite if there's an existing file.
    """
    with open(conf_path,'w') as f:
        toml_str = toml.dump(d,f)

def read_config(conf_path:str):
    """
    Reads and existing TOML file.
    """
    with open(conf_path,'r') as f:
        return toml.load(f) 

def add_server_config(
    conf_path
    ,env:str
    ,server_name:str
    ,dbname:str
    ,port:int
    ,username:str=None
    ,pw:str=None
    ):
    """
    Adds a server to the TOML configuration file.
    """

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
# conf_path = '/home/lozik/Desktop/conf.toml'
# make_config(conf_path,conf)
# # prv_path = os.path.join(path,'keys_prv.json')
# # pub_path = os.path.join(path,'keys_pub.json')
# # make_keys('test keys3','lozik','12345test!%4$',path,path)
# {"username":'lozik',"pw":'12345test!%4$',"pin":12345}
# toml_dict = read_config(conf_path)
# esingle = encrypt("some value")
# edict = encrypt({"test1":""})

""