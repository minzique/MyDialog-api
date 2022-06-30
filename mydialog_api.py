import requests
import json
import random
import string
from base64 import b64encode
from math import floor
from time import time
import uuid

# API endpoints
API_BASE = 'https://selfcare.dialog.lk/scapp_6_0_1/index.php?r=/scapp'
API_SEND_PIN = '/accounts/checkAccountOther'  # sends the otp
API_REGISTER = '/accounts/pinValidateOther'     
API_USAGE = '/midendProxy/getUsageInfo'
API_DATA_USAGE = '/midendProxy/getDataUsageInfo'
API_CON_DETAILS = '/midendProxy/getConnDetails'
API_HEADERS = {
    'content-type':    'application/x-www-form-urlencoded; utf-8' # Only this would be enough, adding others for good measure
}

# Used to generate requestId and appSignature
# Hardcoded in the iOS app
APP_SIG = 'cMLSQD1z0wMqB3iBS80mbNCGWmY='
APP_TITLE = 'jvw+/G8W2Vzws8VIb2hniRUVs+snseLqe1ofW3TxMKM='

def gen_auth():
    '''
    Returns a dictionary containing "authentication" parameters used in the API requests 
    '''
    params = {
        'uniq_id': None,
        'traceId': None,
        'requestId': None,
        'appSignature': None
    }
    params['uniq_id'] = str(random.randint(1e11, 10e11))
    params['traceId'] = 'MDA' + params['uniq_id']

    def rand(len): return ''.join(random.choices(
        string.ascii_letters + string.digits, k=len))

    rand_rq = rand(8)  # this is encoded in both requestId and appSignature
    params['requestId'] = b64encode((rand_rq + rand(7)).encode()).decode()

    asig_1 = APP_SIG[:5] + rand(5) + APP_SIG[5:]
    asig_2 = b64encode((rand_rq[::-1] + str(floor(time()))).encode()).decode()
    # gotta love python :')
    asig_3 = b64encode(
        (rand(3) + APP_TITLE[:5] + rand(5) + APP_TITLE)[::-1].encode()).decode()
    params['appSignature'] = asig_1 + '_' + asig_2 + '_' + asig_3

    return params

def gen_params(no):
    n = str(no)
    return {
        'conn': n,
        # Register endpoints need this
        'conn_ref': n,
        # API_USAGE needs this to be valid, but usage info is not dependant on it
        'serviceType': 'mobile_prepaid',
        'appVersion': '14.3.0',
        # from /getConnDetails (API_CON_DETAILS)
        'lob': '', 
        'connType': '',
        # imsi is the only real 'authentication' used by the api
        # generated by the client on initial login and used with subsequent requests
        # it can be any string under 256 bytes
        # we use the base64 encoded hardware address from uuid.getnode() for convenience
        'imsi': b64encode(str(uuid.getnode()).encode()).decode()
    }


def query_encode(dict):
    l = []
    for x, y in dict.items():
        l.append(x + '=' + y)
    return '&'.join(l)

def request(path, params):
    # Yes, they use POST for everything lol
    res = requests.post(
        API_BASE + path, query_encode({**params, **gen_auth()}), headers=API_HEADERS)
    #FIXME: check and return the error instead
    #if not '"success":true' in res.text: return {'success': False}
    return res.json()

def get_con_details(params):
    """
        Parameters: 
            a dict containing auth parameters
        Returns: 
            a dictionary containing connection details
       
    """
    """Sample response (success):

    {"data": {
        "sub_category": "REGULAR",
        "bill_run_code": "PRE",
        "is_hybrid": false,
        "connStatus": "Connected",
        "type": "PREPAID",
        "user": {
            "identity": {
                "number": "{nic}",
                "type": "NIC"
            },
            "name": "{name}",
            "mobile": null,
            "email": null
        },
        "lob": "GSM",
        "status": {
            "ocs": {
                "payment": {
                    "mode": "PREPAID",
                    "outstanding": 0,
                    "balance": 51.5668,
                    "credit_limit": 0
                },
                "cx_category": "NIC",
                "status": "{nic}"
            },
            "crm": {
                "connection_status_date": "2017-05-26T13:07:08",
                "status": "CONNECTED"
            }
        }
    },
    "success": true
    }
    """
    res = request(API_CON_DETAILS, params)
    if res['success'] == True:
        params['lob'] = res['data']['lob']
        params['connType'] = res['data']['type']
    else:
        print('An error occurred; this device is likely not registered:' + str(res))
    return res

def send_pin(params, nic: str):
    """
    Parameters:
        A dict containing auth parameters
        The associated nic number
    Returns:
        True on success, False on failure 
    """
    res = request(API_SEND_PIN, {**params, **{'nic': nic}})
    if res['success'] == True and res['status'] == 'pin_sent':
        print('Pin sent.')
        return True
    print(f'Pin not sent. An error occurred: {json.dumps(res)}')
    return False

def register_with_pin(params, pin):
    """
    Parameters:
        A dict containing auth parameters
        The pin received
    Returns:
        True on success, False on failure 
    """
    """Sample response (success):
    
    {'success': True, 
    'status': 'ok', 
    'info': 'Ok', 
    'conn_rec': {
        'loyality': '', 
        'nic': '{nic}', 
        'confirm_sms': 0, 
        'primary_number': 1, 
        'added_by_pin': 1, 
        'device_id': '50611382', 
        'conn_ref': '{no}', 
        'connType': 'PREPAID', 
        'lob': 'MOBILE', 
        'loyality_type': '', 
        'id_type': 'NIC', 
        'nick_name': '', 
        'status': 1, 
        'create_ts': '2022-06-30 00:00:00', 
        'update_ts': '2022-06-30 00:00:00', 
        'id': '24332484', 
        'idType': 'NIC'
    }, 
    'device_id': '50611382', 
    'cv_theme': '', 
    'hybrid': False, 
    'idType': 'NIC'
    }"""
    res = request(API_REGISTER, {**params, **{'pin': str(pin)}})
    if res['success'] == True and 'conn_rec' in res:
        return True
    
    print(f'An error occurred, device could not be registered: {json.dumps(res)}')
    return False
    
    
def get_data_usage(params):
    res = request(API_DATA_USAGE, params)
    if res['success'] == False or res['apiFailure'] == True:
        print('Error fetching data usage data from the API: API_DATA_USAGE: ' + json.dumps(res))
    return res

def get_usage(params):
    res = request(API_USAGE, params)
    if res['success'] == False:
        print('Error fetching usage data from the API: API_USAGE: ' + json.dumps(res))
    return res