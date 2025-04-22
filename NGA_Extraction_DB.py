from __future__ import print_function, division, absolute_import, unicode_literals
from requests.adapters import HTTPAdapter
import requests, urllib3, json                      # requests > For HTTP Call
from msal import ConfidentialClientApplication      # msal > For Aouth2
import pandas as pd
from datetime import datetime
import certifi
from requests_kerberos import HTTPKerberosAuth
import time
#from openai_connector import OpenAIConnector
#import send_email_connector as email_connector
import textwrap
from io import StringIO
import os
import ssl
import warnings
from urllib3.exceptions import InsecureRequestWarning
from dotenv import load_dotenv

load_dotenv()
# Access the SSL-related environment variables
ssl_enabled = os.getenv('SSL_ENABLED', 'False').lower() in ('true', '1', 't')
ssl_cert_path = os.getenv('SSL_CERT_PATH')

# Default verify setting
verify_setting = True

if ssl_enabled:
    if ssl_cert_path:
        verify_setting = ssl_cert_path
    else:
        verify_setting = True
else:
    verify_setting = False
    # Suppress only the InsecureRequestWarning from urllib3
    warnings.simplefilter('ignore', InsecureRequestWarning)

class SSLContextAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = urllib3.util.ssl_.create_urllib3_context()
        if not ssl_enabled:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        context.load_default_certs()
        return super(SSLContextAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = urllib3.util.ssl_.create_urllib3_context()
        if not ssl_enabled:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        context.load_default_certs()
        return super(SSLContextAdapter, self).proxy_manager_for(*args, **kwargs)

def extract_data_for_project(project_name, app_reg_id, app_reg_secret):
    app = ConfidentialClientApplication(app_reg_id, app_reg_secret,
                                        str("https://login.microsoftonline.com/intel.onmicrosoft.com"))
    retries = urllib3.Retry(
        total=10,
        status_forcelist=[408],
        allowed_methods=['POST', 'GET', 'PUT'],
        raise_on_status=True,
        backoff_factor=0.2,
    )
    SslContextAdapter = SSLContextAdapter(max_retries=retries)
    session = requests.Session()
    session.mount('https://nga-prod.laas.icloud.intel.com', SslContextAdapter)

    token = app.acquire_token_for_client([str("6af0841e-c789-4b7b-a059-1cec575fbddb/.default")])
    get_failure_details = f'https://nga-prod.laas.icloud.intel.com/Failure/{project_name}/api/Failure/Failures/365'
    response = session.get(get_failure_details, headers={"Authorization": "Bearer " + token["access_token"]}, verify=verify_setting)
    response_data = response.json()
    number_of_records = response_data['RecordsCount']
    print(f"Number of records of {project_name}: {number_of_records}")

    extracted_data = []
    for record in response_data["Records"]:
        axon_sv_record_viewer_key = next((key for key in record.get("StringExternalInfo", {}) if key.startswith("AxonSV Record Viewer")), None)
        axon_sv_record_viewer_link = record.get("StringExternalInfo", {}).get(axon_sv_record_viewer_key, None)
        signatures = [signature["Signature"] for signature in record.get("Signatures", [])]
        tags = record.get("Tags", [])
        try:
            test_run_id = record['TestRunId']
            token = app.acquire_token_for_client([str("6af0841e-c789-4b7b-a059-1cec575fbddb/.default")])
            get_testrunid_details = f'https://nga-prod.laas.icloud.intel.com/TestRun/{project_name}/api/TestRun/{test_run_id}'
            response_test_run_Id = session.get(get_testrunid_details, headers={"Authorization": "Bearer " + token["access_token"]}, verify=verify_setting)
            info_test_run_Id = response_test_run_Id.json()
            group_dict = info_test_run_Id['TestGroupIdentifier']
            for key in group_dict:
                if key == 'EntityId':
                    ID = group_dict[key]
                    get_group_details = f'https://nga-prod.laas.icloud.intel.com/Planning/{project_name}/api/TestGroup/{ID}'
                    response_group = session.get(get_group_details, headers={"Authorization": "Bearer " + token["access_token"]}, verify=verify_setting)
                    group_info = response_group.json()
                    Group_Name = group_info['Name']
        except:
            Group_Name = ""
        try:
            if record['StringExternalInfo']:
                for key in record['StringExternalInfo']:
                    if key.endswith('_signature'):
                        debug_snapshot = key.split('_')[1]
                        break
        except:
            debug_snapshot = ""
        try:
            Id_NGA = record['Id']
            record_data = {
                "Failure Name": record["Name"],
                "NGA_Link": f"https://nga.laas.intel.com/#/{project_name}/failureManagement/failures/{Id_NGA}",
                "Station Name": record["StationName"],
                "Stage": record["StageName"],
                "Debug Snapshot": debug_snapshot,
                "Group Name": Group_Name,
                "Failure_Id": record["Id"],
                "SightingId": record.get("SightingId", "NA"),
                "AxonSV Record Viewer": axon_sv_record_viewer_link,
                "Signatures": tags
            }
            extracted_data.append(record_data)
        except:
            pass

    df = pd.DataFrame(extracted_data)
    return df