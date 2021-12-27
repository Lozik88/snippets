import json
import os
import re
import pandas as pd
import sqlite3
import numpy as np
from cryptography.fernet import Fernet

# os.path.dirname(__file__)
def _dump_keys(d,desc,path):
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
def make_keys(
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
    pub={
        'desc':desc,
        'username':username.decode('utf-8'),
        'password':pw.decode('utf-8')
    }
    prv={
        'desc':desc,
        'key':key.decode('utf-8')
    }
    _dump_keys(prv,desc,prv_path)
    _dump_keys(pub,desc,pub_path)

path = os.path.dirname(__file__)
prv_path = os.path.join(path,'keys_prv.json')
pub_path = os.path.join(path,'keys_pub.json')

make_keys('test keys3','lozik','12345test!%4$',path,path)