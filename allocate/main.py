from service_mapping_plugin_framework.allocate_nssi_abc import AllocateNSSIabc
from .params import OS_MA_NFVO_IP,OS_USER_DOMAIN_NAME,OS_USERNAME,OS_PASSWORD,OS_PROJECT_DOMAIN_NAME,OS_PROJECT_NAME
import json
import os
import requests
import yaml
import glob
import time
import pprint
import uuid

class NFVOPlugin(AllocateNSSIabc):
    def __init__(self, nm_host, nfvo_host, subscription_host, parameter):
        super().__init__(nm_host, nfvo_host, subscription_host, parameter)
        # Don't devstack environment OS_AUTH_URL can't add 'identity'.
        self.OS_AUTH_URL = 'http://192.168.1.219:5000/v3/'
        #self.TACKER_URL = 'http://{}'.format(nfvo_host)
        self.TACKER_URL = "http://192.168.1.219:9890/v1.0"
        self.OS_USER_DOMAIN_NAME = OS_USER_DOMAIN_NAME
        self.OS_USERNAME = OS_USERNAME
        self.OS_PASSWORD = OS_PASSWORD
        self.OS_PROJECT_DOMAIN_NAME = OS_PROJECT_DOMAIN_NAME
        self.OS_PROJECT_NAME = OS_PROJECT_NAME
        self.OS_VIM_NAME = "jefferyvim"
        self.ary_data = list()
        self.nsd_id = str()
        self.nsd_name = str()
        self.get_token_result = str()
        self.project_id = str()
        self.nsinfo = dict()

    def get_token(self):
        # print("\nGet token:")
        self.get_token_result = ''
        get_token_url = 'http://192.168.1.219:5000/v3/auth/tokens'
        get_token_body = {
            'auth': {
                'identity': {
                    'methods': [
                        'password'
                    ],
                    'password': {
                        'user': {
                            'domain': {
                                'name': self.OS_USER_DOMAIN_NAME
                            },
                            'name': self.OS_USERNAME,
                            'password': self.OS_PASSWORD
                        }
                    }
                },
                'scope': {
                    'project': {
                        'domain': {
                            'name': self.OS_PROJECT_DOMAIN_NAME
                        },
                        'name': self.OS_PROJECT_NAME
                    }
                }
            }
        }
        get_token_response = requests.post(get_token_url, data=json.dumps(get_token_body))
        #print("Get OpenStack token status: " + str(get_token_response.status_code))
        self.get_token_result = get_token_response.headers['X-Subject-Token']
        return self.get_token_result

    def get_project_id(self, project_name):
        # print("\nGet Project ID:")
        self.project_id = ''
        get_project_list_url = self.OS_AUTH_URL + 'projects'
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        get_project_list_response = requests.get(get_project_list_url, headers=headers)
        # print("Get OpenStack project list status: " + str(get_project_list_response.status_code))
        get_project_list_result = get_project_list_response.json()['projects']
        for project in get_project_list_result:
            if project['name'] == project_name:
                self.project_id = project['id']
            pass
        # print("Project ID:" + self.project_id)
        return self.project_id

    def json_to_array(self, json_data):
        self.ary_data = []
        if len(json_data) > 0:
            for key, value in json_data.items():
                self.ary_data.append(value)
        return self.ary_data

    def create_vnf_package(self, vnf_package_path):
        pass

    def upload_vnf_package(self, vnf_package_path):
        file_path_list = glob.glob(os.path.join(vnf_package_path, 'Definitions/*.yaml'))
        vnfd_file = file_path_list[0].replace(os.path.join(vnf_package_path, 'Definitions/'), '')
        #print("vnfd_file: {}".format(vnfd_file))
        vnfd_name = vnfd_file.split('.yaml')[0]
        print('\nUpload VNFD: ' + vnfd_name)
        vnfd_description = 'VNFD:' + vnfd_name
        vnfd_body = {
            'vnfd': {
                'tenant_id': self.get_project_id(self.OS_PROJECT_NAME),
                'name': vnfd_name,
                'description': vnfd_description,
                'service_types': [
                    {
                        'service_type': 'vnfd'
                    }
                ],
                'attributes': {
                    'vnfd': yaml.safe_load(open(file_path_list[0], 'r+').read())
                }
            }
        }
        #upload_vnfd_url = 'http://192.168.1.219:9890/v1.0/vnfds'
        upload_vnfd_url = self.TACKER_URL + "/vnfds"
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        response = requests.post(upload_vnfd_url, data=json.dumps(vnfd_body), headers=headers)
        print('Upload VNFD status: ' + str(response.status_code))
        #self.create_vnf(vnfd_name)

    def create_vnf(self,vnf_name):
        post_create_vnf_url = self.TACKER_URL + "/vnfs"
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        tenant_id = self.get_project_id(self.OS_PROJECT_NAME)
        vnfd_id = self.get_vnfd_id(vnf_name)
        vim_id = self.get_vim_id(self.OS_VIM_NAME)
        vnf_description = 'description'
        vnf_body = {
                'vnf': {
                    'name': vnf_name,
                    'description': vnf_description,
                    'tenant_id': tenant_id,
                    'vnfd_id': vnfd_id,
                    'vim_id': vim_id,
                }
        }
        res_create_vnf = requests.post(post_create_vnf_url, data=json.dumps(vnf_body), headers=headers)
        print('Create VNF status: ' + str(res_create_vnf.status_code))
        vnf_id = res_create_vnf.json()['vnf']['id']
        create_vnf_status = res_create_vnf.json()['vnf']['status']
        '''count =0
        while create_vnf_status !='ACTIVE' and create_vnf_status != 'ERROR':
            show_vnf_url = self.TACKER_URL + "/vnfs/" + vnf_id
            res_show_vnf = requests.get(show_vnf_url, headers=headers).json()
            create_vnf_status = res_show_vnf['vnf']['status']
            time.sleep(1)
            count = count+1
            print('wait ' + str(count) + 's')'''
        print('create ' + vnf_name + ' successfully!!')
    
    def set_vnf_info(self):
        print('enter set_vnf_info')
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        list_vnf_url = self.TACKER_URL + '/vnfs'
        res_list_vnf = requests.get(list_vnf_url, headers=headers).json()['vnfs']
        vnf_id = dict()
        for vnf in res_list_vnf:
            print('name {name} : {id}'.format(name=vnf['name'],id=vnf['id']))
            vnf_id[vnf['name']]=vnf['id']
        #print('nrf id: {}'.format(vnf_id['nrfd']))
        self.nsinfo = {
            'mongodb': vnf_id['mongodb'],
            'nrfd':vnf_id['nrfd'],
            'amfd':vnf_id['amfd'],
            'smfd':vnf_id['smfd'],
            'udrd':vnf_id['udrd'],
            'pcfd':vnf_id['pcfd'],
            'udmd':vnf_id['udmd'],
            'nssfd':vnf_id['nssfd'],
            'ausfd':vnf_id['ausfd']
        }

    def list_vnfd(self):
        get_vnfd_list_url = self.TACKER_URL + "/vnfds"
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        get_vnfd_list_response = requests.get(get_vnfd_list_url, headers=headers)
        #print("Get Tacker vnfd list status: " + str(get_vnfd_list_response.status_code))
        get_vnfd_list_result = get_vnfd_list_response.json()
        #text = get_nsd_list_response.text
        #print(get_nsd_list_result)
        #print(text)
        return get_vnfd_list_result    

    def get_vnfd_id(self, vnfd_name):
        vnfd_list = self.list_vnfd()
        #print(vnfd_list)
        vnfd_id = None
        for vnfd in vnfd_list['vnfds']:
            if vnfd['name'] == vnfd_name:
                vnfd_id = vnfd['id']
                #print vnfd_id
            pass
        #print('vnfd id: {}'.format(vnfd_id))
        return vnfd_id

    def upload_ns_descriptor(self, ns_descriptor_path):
        file_path_list = glob.glob(os.path.join(ns_descriptor_path, 'Definitions/*.yaml'))
        nsd_file = file_path_list[0].replace(os.path.join(ns_descriptor_path, 'Definitions/'), '')
        self.nsd_name = nsd_file.split('.yaml')[0]
        print('\nUpload NSD: ' + self.nsd_name)
        nsd_description = 'NSD:' + self.nsd_name
        nsd_body = {
            'nsd': {
                'tenant_id': self.get_project_id(self.OS_PROJECT_NAME),
                'name': self.nsd_name,
                'description': nsd_description,
                'attributes': {
                    'nsd': yaml.safe_load(open(file_path_list[0], 'r+').read())
                }
            }
        }
        print(str(nsd_body))
        #upload_nsd_url = 'http://192.168.1.219:9890/v1.0/nsds'
        upload_nsd_url = self.TACKER_URL + "/nsds"
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        response = requests.post(upload_nsd_url, data=json.dumps(nsd_body), headers=headers)
        print('Upload NSD status: ' + str(response.status_code))
        self.nsd_id = response.json()['nsd']['id']

    def create_ns_descriptor(self):
        pass

    def check_feasibility(self):
        pass

    def create_ns_instance(self):
        pass

    def list_vim(self):
        get_vim_list_url = self.TACKER_URL + '/vims'
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        get_vim_list_response = requests.get(get_vim_list_url, headers=headers)
        #print("Get Tacker vim list status: " + str(get_vim_list_response.status_code))
        get_vim_list_result = get_vim_list_response.json()
        #text = get_vim_list_response.text
        #print(get_vim_list_result)
        #print(text)
        return get_vim_list_result

    def get_vim_id(self, vim_name):
        vim_list = self.list_vim()
        #print(vim_list)
        vim_id = None
        for vim in vim_list['vims']:
            if vim['name'] == vim_name:
                vim_id = vim['id']
                #print (vim_id)
            pass
        return vim_id


    def ns_instantiation(self, ns_descriptor_path):
        nsd_params_file = os.path.join(ns_descriptor_path, 'Definitions/params/{}.yaml').format(
            self.nsd_name)
        print('\nNS instantiation: ' + self.nsd_name)
        ns_description = "NS:" + self.nsd_name
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        res_show_ns = {}
        if os.path.isfile(nsd_params_file):
            nsd_params = yaml.safe_load(open(nsd_params_file, 'r+').read())
        else:
            nsd_params = {}
        vim_id = self.get_vim_id(self.OS_VIM_NAME)
        ns_body = {
            'ns': {
                'name': self.nsd_name,
                'nsd_id': self.nsd_id,
                'description': ns_description,
                'tenant_id': self.get_project_id(self.OS_PROJECT_NAME),
                'attributes': {
                    'param_values': nsd_params
                },
                'vim_id': vim_id,
            }
        }
        #create_ns_url = 'http://192.168.1.219:9890/v1.0/nss'
        create_ns_url = self.TACKER_URL + "/nss"
        res_create_ns = requests.post(create_ns_url, data=json.dumps(ns_body), headers=headers)
        print('Create NS status: ' + str(res_create_ns.status_code))
        ns_id = res_create_ns.json()['ns']['id']
        create_ns_status = res_create_ns.json()['ns']['status']
        count = 0
        while create_ns_status != 'ACTIVE' and create_ns_status != 'ERROR':
            show_ns_url = self.TACKER_URL + '/nss/' + ns_id
            res_show_ns = requests.get(show_ns_url, headers=headers).json()
            create_ns_status = res_show_ns['ns']['status']
            time.sleep(1)
            count = count + 1
            print('wait ' + str(count) + 's')
        pprint.pprint(res_show_ns)
        ns_instance_id = res_show_ns['ns']['id']
        description = res_show_ns['ns']['description']
        nsd_info_id = res_show_ns['ns']['nsd_id']
        vnf_info = res_show_ns['ns']['vnf_ids']
        vnffg_info = res_show_ns['ns']['vnffg_ids']
        ns_state = res_show_ns['ns']['status']
        monitoringParameter = res_show_ns['ns']['mgmt_urls']
        #print(res_show_ns['ns']['vnf_ids'][0])
        self.random_uuid=str(uuid.uuid4())
        ''''mongodb':res_show_ns['ns']['vnf_ids']['VNF0'],
        'nrfd':res_show_ns['ns']['vnf_ids']['VNF1'],
        'amfd':res_show_ns['ns']['vnf_ids']['VNF2'],
        'smfd':res_show_ns['ns']['vnf_ids']['VNF3'],
        'udrd':res_show_ns['ns']['vnf_ids']['VNF4'],
        'pcfd':res_show_ns['ns']['vnf_ids']['VNF5'],
        'udmd':res_show_ns['ns']['vnf_ids']['VNF6'],
        'nssfd':res_show_ns['ns']['vnf_ids']['VNF7'],
        'ausd':res_show_ns['ns']['vnf_ids']['VNF8']'''
        str_ = '123'
        self.nsinfo = {
            'id': ns_instance_id,
            'nsInstanceDescription': description,
            'nsdInfoId': nsd_info_id,
            'vnfInstance': vnf_info,
            'vnffgInfo': vnffg_info,
            'nsState': ns_state,
            'monitoringParameter': monitoringParameter,
            'mongodb':self.random_uuid,
            'nrfd':self.random_uuid,
            'amfd':self.random_uuid,
            'smfd':self.random_uuid,
            'udrd':self.random_uuid,
            'pcfd':self.random_uuid,
            'udmd':self.random_uuid,
            'nssfd':self.random_uuid,
            'ausfd':self.random_uuid
        }

    def list_vnf(self):
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        list_vnf_url = self.TACKER_URL + 'vnfs'
        res_list_vnf = requests.get(list_vnf_url, headers=headers).json()
        printf(str(res_list_vnf))

    def coordinate_tn_manager(self):
        pass

    def create_vnf_package_subscriptions(self, vnf):
        pass

    def listen_on_vnf_package_subscriptions(self):
        pass

    def create_ns_descriptor_subscriptions(self, ns_des):
        pass

    def listen_on_ns_descriptor_subscriptions(self):
        pass

    def create_ns_instance_subscriptions(self):
        pass

    def listen_on_ns_instance_subscriptions(self):
        pass

    def scale_ns_instantiation(self, ns_instance_id, scale_info):
        pass

    def update_ns_instantiation(self, ns_instance_id, update_info):
        pass

    def read_ns_instantiation(self, ns_instance_id):
        pass

    def read_ns_descriptor(self, nsd_object_id):
        pass

    def read_vnf_package(self, vnf_pkg_id):
        pass
