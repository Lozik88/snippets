from cryptography.fernet import Fernet
from pandas import DataFrame
from json import dumps,dump, load,loads
import os
import csv
import uuid
# import configparser as config

# conf = config.ConfigParser()
fcreds=os.path.join(os.path.dirname(__file__),'creds.json')
fkeys=os.path.join(os.path.dirname(__file__),'keys.json')

if os.path.exists(fcreds):
    os.remove(fcreds)
if os.path.exists(fkeys):
    os.remove(fkeys)

# ktree=[] # how can i get this inside encrypt_cred?
def encrypt_cred(iter,ktree=[]):
    """
    Recursively encrypts all client_id and client_secret dict values in a list/dict tree.
    Returns encrypted iter and key tree pair. uuid can be used to find matching pairs.
    """
    # if ktree is None:
    #     ktree=[]
    def dict_helper(i):
        key = Fernet.generate_key()
        f = Fernet(key)
        required_keys = ['client_id','client_secret']
        haskeys = all(k in i.keys() for k in required_keys)
        iskeyready=True # eliminates duplicates in keyfile
        for k,v in i.copy().items():
            if isinstance(v,dict):
                dict_helper(v)
            elif k in ['client_id','client_secret']:
                if not haskeys:
                    raise ValueError(f'Dictionary must contain both keys: {required_keys}')
                i[k] = f.encrypt(v.encode('utf-8')).decode('ascii')
                # i['key']=key.decode('ascii')
                if iskeyready:
                    i['uuid']=str(uuid.uuid4())
                    ktree.append(
                        {'uuid':i['uuid'],'key':key.decode('ascii')}
                        )
                iskeyready=False
            elif isinstance(v,list):
                encrypt_cred(v)
    if isinstance(iter,list):
        for i in iter:
            if isinstance(i,list):
                encrypt_cred(i)
            if isinstance(i,dict):
                dict_helper(i)
    if isinstance(iter,dict):
        dict_helper(iter)
    return iter,ktree

def make_key_pair():
    cred_template = {'Production':{'creds':[]},'Development':{'creds':[]}}

    creds_dev = [
            {'name':'someDevSqlDb1','client_id':'myDevId1','client_secret':'someDevPw1'},
            {'name':'someDevSqlDb2','client_id':'myDevId2','client_secret':'someDevPw2'},
            {'name':'someDevSqlDb3','client_id':'myDevId3','client_secret':'someDevPw3'},
            {'name':'someDevWebAPI4','client_id':'myDevId4','client_secret':'someDevPw4','url':'someDevUrl1'},
            {'name':'someDevWebAPI5','client_id':'myDevId5','client_secret':'someDevPw5','url':'someDevUrl2'},
            {
                'name':'someDevLinuxMachine','client_id':'someDevAdmin1','client_secret':'someDevPw1','users':
                [
                    {'client_id':'someDevLinuxId1','client_secret':'someDevPw1'},
                    {'client_id':'someDevLinuxId2','client_secret':'someDevPw2'},
                    {'client_id':'someDevLinuxId3','client_secret':'someDevPw3'},
                    {'client_id':'someDevLinuxId4','client_secret':'someDevPw4'},
                    {'client_id':'someDevLinuxId5','client_secret':'someDevPw5'}
                ]
            }
        ]
    creds_prod = [
            {'name':'someProdSqlDb1','client_id':'myProdId1','client_secret':'someProdPw1'},
            {'name':'someProdSqlDb2','client_id':'myProdId2','client_secret':'someProdPw2'},
            {'name':'someProdSqlDb3','client_id':'myProdId3','client_secret':'someProdPw3'},
            {'name':'someProdWebAPI4','client_id':'myProdId4','client_secret':'someProdPw4','url':'someProdUrl1'},
            {'name':'someProdWebAPI5','client_id':'myProdId5','client_secret':'someProdPw5','url':'someProdUrl2'},
            {
                'name':'someLinuxMachine','client_id':'someProdAdmin1','client_secret':'someProdPw1','users':
                [
                    {'client_id':'someProdLinuxId1','client_secret':'someProdPw1'},
                    {'client_id':'someProdLinuxId2','client_secret':'someProdPw2'},
                    {'client_id':'someProdLinuxId3','client_secret':'someProdPw3'},
                    {'client_id':'someProdLinuxId4','client_secret':'someProdPw4'},
                    {'client_id':'someProdLinuxId5','client_secret':'someProdPw5'}
                ]
            }
        ]
    creds = [
        {'Production':{'creds':creds_prod}},
        {'Development':{'creds':creds_dev}}
        ]
    list(map(cred_template['Production']['creds'].append,creds_prod))
    list(map(cred_template['Production']['creds'].append,creds_dev))

    ecreds,keys = encrypt_cred(creds)
    with open('creds.json','w') as f:
        dump(ecreds,f,indent=1)
    with open('keys.json','w') as f:
        dump(keys,f,indent=1)

# def decrypt_creds_file(name,creds,keys):
#     pass
class Decrypt:
    def __init__(self) -> None:
        self.match=False
        self.lookup_result=None
    def decrypt_cred(self,creds,keys,lookup:dict=None):
        """
        Recursively decrypts all client_id and client_secret dict values in a list/dict tree.
        Returns encrypted iter and key tree pair. uuid can be used to find matching pairs.    
        """
        hasfiles = os.path.isfile(creds) and os.path.isfile(keys)
        haslookup = lookup != None
        if not hasfiles:
            raise ValueError('Missing files.')
        elif hasfiles:
            with open(creds,'r') as f:
                creds=load(f)
            with open(keys,'r') as f:
                keys=load(f)
        # if haslookup:
        #     lookup_result = None

        def _recur_iter(iter):
            if self.match:
                pass
            else:
                if isinstance(iter,list):
                    for v in iter:
                        if isinstance(v,(list,dict)):
                            if self.match:
                                break
                            _recur_iter(v)
                if isinstance(iter,dict):
                    required_keys = ['client_id','client_secret','uuid']
                    haskeys = all(k in iter.keys() for k in required_keys)
                    if haskeys:
                        for key in keys:
                            if key['uuid']==iter['uuid']:
                                f = Fernet(key['key'].encode('utf-8'))
                                client_id = f.decrypt(iter['client_id'].encode('utf-8')).decode('ascii')
                                client_secret = f.decrypt(iter['client_secret'].encode('utf-8')).decode('ascii')
                                if lookup == None:
                                    iter['client_id'] = client_id
                                    iter['client_secret'] = client_secret
                                # elif all(k in iter.keys() for k in lookup):
                                elif all((k,v) in iter.items() for (k,v) in lookup.items()):
                                    iter['client_id'] = client_id
                                    iter['client_secret'] = client_secret
                                    self.lookup_result = iter
                                    self.match=True
                                break
                    if self.match:
                        pass
                    else:
                        for k,v in iter.items():
                            if isinstance(v,(list,dict)):
                                if self.match:
                                    break
                                _recur_iter(v)
            if haslookup:
                return iter
            else:
                return iter

        creds =_recur_iter(creds)
        if haslookup:
            creds = self.lookup_result
        return creds
# def decrypt_cred(creds,keys,lookup:dict=None):
#     """
#     Recursively decrypts all client_id and client_secret dict values in a list/dict tree.
#     Returns encrypted iter and key tree pair. uuid can be used to find matching pairs.    
#     """
#     hasfiles = os.path.isfile(creds) and os.path.isfile(keys)
#     haslookup = lookup != None
#     if not hasfiles:
#         raise ValueError('Missing files.')
#     elif hasfiles:
#         with open(creds,'r') as f:
#             creds=load(f)
#         with open(keys,'r') as f:
#             keys=load(f)
#     if haslookup:
#         lookup_result = None

#     def _recur_iter(iter,match=False):
#         if match:
#             pass
#         else:
#             if isinstance(iter,list):
#                 for v in iter:
#                     if isinstance(v,(list,dict)):
#                         if match:
#                             break
#                         _recur_iter(v,match)
#             if isinstance(iter,dict):
#                 required_keys = ['client_id','client_secret','uuid']
#                 haskeys = all(k in iter.keys() for k in required_keys)
#                 if haskeys:
#                     for key in keys:
#                         if key['uuid']==iter['uuid']:
#                             f = Fernet(key['key'].encode('utf-8'))
#                             client_id = f.decrypt(iter['client_id'].encode('utf-8')).decode('ascii')
#                             client_secret = f.decrypt(iter['client_secret'].encode('utf-8')).decode('ascii')
#                             if lookup == None:
#                                 iter['client_id'] = client_id
#                                 iter['client_secret'] = client_secret
#                             # elif all(k in iter.keys() for k in lookup):
#                             elif all((k,v) in iter.items() for (k,v) in lookup.items()):
#                                 iter['client_id'] = client_id
#                                 iter['client_secret'] = client_secret
#                                 lookup_result = iter
#                                 match=True
#                             break
#                 if match:
#                     pass
#                 else:
#                     for k,v in iter.items():
#                         if isinstance(v,(list,dict)):
#                             if match:
#                                 break
#                             _recur_iter(v,match)
#         if haslookup:
#             return iter, match
#         else:
#             return iter

#     creds =_recur_iter(creds)
#     if haslookup:
#         creds = lookup_result
#     return creds
make_key_pair()
d=Decrypt()
dcreds = d.decrypt_cred(fcreds,fkeys,{'name':'someDevSqlDb1'})
# dcreds = decrypt_cred(fcreds,fkeys,{'name':'someDevSqlDb1'})
# dcreds = decrypt_cred(fcreds,fkeys)

fdcreds = os.path.join(os.path.dirname(__file__),'decrypted_creds.json')
if os.path.exists(fdcreds):
    os.remove(fdcreds)
with open(fdcreds,'w') as f:
    dump(dcreds,f,indent=1)
y=""

class KeyGenerator:

    def __init__(self) -> None:

        self.pw_dir = os.path.join(os.path.dirname(__file__),'creds')

        self.config_file = os.path.join(self.pw_dir,'config.json')       

        self.pw_file = os.path.join(self.pw_dir,'creds.json')

        self.pw_template = os.path.join(self.pw_dir,'pw.csv')

        if not os.path.exists(self.config_file):

            print(f'Config file not found at: {self.config_file}. A new one must be created.')

        if not os.path.exists(self.pw_dir):

            print(f'Creating new creds directory: {self.pw_dir}')

            os.mkdir(self.pw_dir)

        if not os.path.exists(self.pw_file):

            self.make_key()

    def _set_key_path(self):

        print("Input a secure directory to save your private key file. Other users SHOULD NOT HAVE ACCESS.")

        while True:

            path = input()

            if not os.path.exists(path):

                print(f"{path} does not exist. Please ensure the application has visibility to this directory.")

                continue

            elif os.path.exists(path):

                self.key_file = os.path.join(path,'private_key.json')

                break

    def _open_pw_template(self):

        os.startfile(self.pw_template)

        print(f"""

        Template has been generated at: {self.pw_template}

        Please fill in the fields:

        host = source that the creds tied to.

        client_id = username

        client_secret = password

        Save and close pw.csv when complete, then press any key to continue...

        """)

        input()

    def make_pw_template(self,headers):

        print(f'Generating a new template at: {self.pw_template}')

        with open(self.pw_template,'w',newline='') as f:

            descriptors=[

                {'host':'ccat'}

                ,{'host':'netezza'}

                ,{'host':'windows'}

            ]

            writer=csv.DictWriter(f,fieldnames=headers)

            writer.writeheader()

            writer.writerows(descriptors)

        return os.path.getmtime(self.pw_template)

    def make_key(self):

        headers=['host','client_id','client_secret']

        while True:

            print("""

            Which environment is are these credentials for?

            1 - Development

            2 - Production

            """)

            env = input()

            if not env.isdigit():

                print(f"{env.isdigit()} is not a valid value. Must be integer.")

            elif env=='1':

                isprod=True

                break

            elif env=='2':

                isprod=False

                break

            else:

                print(f"{env.isdigit()} is not a valid option.")

        if not hasattr(self,'key_file'):

            self._set_key_path()

        self.make_pw_template(headers)

        self._open_pw_template()

       

        csvfile = open(self.pw_template,'r')

        reader = csv.DictReader(csvfile, headers)

        next(reader)

        encrypted_creds={'env':[]}

        # for row in reader:

        private_key={'env':[]}

        [encrypted_creds['env'].append((encrypt_cred(**row))) for row in reader]

        for d in encrypted_creds['env']:

            private_key['env'].append(

                {k:v for k,v in d.items() if k not in ['client_secret']}

            )

        if isprod:

            encrypted_creds['Production'] = encrypted_creds['env']

            private_key['Production'] = private_key['env']

            encrypted_creds.pop('env')

            private_key.pop('env')

        else:

            encrypted_creds['Development'] = encrypted_creds['env']

            private_key['Development'] = private_key['env']

            encrypted_creds.pop('env')

            private_key.pop('env')

 

        with open(self.pw_file,'w') as f:

            dump(encrypted_creds,f,indent=1)

        with open(self.key_file,'w') as f:

            dump(private_key,f,indent=1)

 

        os.remove(self.pw_template)

       

        print(f'Credential file created at: {self.pw_file}')

        print(f'Key file created at: {self.key_file}')

    def make_config(self):

        pass

       

k = KeyGenerator()