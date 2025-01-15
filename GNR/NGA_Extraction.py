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

now = datetime.now()
Date = now.strftime("%Y-%m-%d")


df = pd.DataFrame() 
 
class SSLContextAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = urllib3.util.ssl_.create_urllib3_context()
        kwargs['ssl_context'] = context
        context.load_default_certs()  # this loads the OS defaults on Windows
        return super(SSLContextAdapter, self).init_poolmanager(*args, **kwargs)
 
    def proxy_manager_for(self, *args, **kwargs):
        context = urllib3.util.ssl_.create_urllib3_context()
        kwargs['ssl_context'] = context
        context.load_default_certs()
        return super(SSLContextAdapter, self).proxy_manager_for(*args, **kwargs)
 
 
nga_app_reg_id = '2e75abe8-764a-4773-9433-d064c27eacbf'          # Insert Application Registration ID
nga_app_reg_secret = 'Uix0KsdXU0Zzv3pN2hmPLHJ+Ti]V?v_i'  # Insert Application Registration Secret
nga_project_name = 'nga_fv_gnr'           # Insert Project Name --> Ex: 'nclg_pve_sandbox'
app = ConfidentialClientApplication(nga_app_reg_id, nga_app_reg_secret,
                                    str("https://login.microsoftonline.com/intel.onmicrosoft.com"))     # Endpoint to get the Token at INTEL Azure Directory
 
retries = urllib3.Retry(
    total=10,
    status_forcelist=[408],
    allowed_methods=['POST', 'GET', 'PUT'],
    raise_on_status=True,
    backoff_factor=0.2,
)
 
SslContextAdapter = SSLContextAdapter(max_retries=retries)
session = requests.Session()
session.mount('https://nga-prod.laas.icloud.intel.com', SslContextAdapter)     # Add "-stage" if the project environment is stage environment
                                                                                # There are 2 Environment for NGA user which are Stage and Production
token = app.acquire_token_for_client([str("6af0841e-c789-4b7b-a059-1cec575fbddb/.default")])
 
#project_name = input("Enter the project name (e.g., 'nga_fv_gnr'): ")
get_failure_details = f'https://nga-prod.laas.icloud.intel.com/Failure/nga_fv_gnr/api/Failure/Failures/2'
response = session.get(get_failure_details, headers={"Authorization": "Bearer " + token["access_token"]})
#print(response.json())



# Convert the response to JSON and then to a string
response_data = response.json()


number_of_records = response_data['RecordsCount']

print("Number of records:", number_of_records)

#################################################################################
fetch = response.json()
#print(json.dumps(fetch, indent=4))
data = json.dumps(fetch)

data = json.loads(data)
#print("Data: ", data)
# Extract the required information
extracted_data = []
for record in data["Records"]:
    #print("Record:", record)
    # Find the key that starts with "AxonSV Record Viewer"
    #print(record)
    axon_sv_record_viewer_key = next((key for key in record.get("StringExternalInfo", {}) if key.startswith("AxonSV Record Viewer")), None)
    
    # Extract the AxonSV Record Viewer link using the found key, or use None if the key wasn't found
    axon_sv_record_viewer_link = record.get("StringExternalInfo", {}).get(axon_sv_record_viewer_key, None)
    
    # Safely extract signatures or use an empty list if 'Signatures' key is not present
    signatures = [signature["Signature"] for signature in record.get("Signatures", [])]
    tags = record.get("Tags", [])
    try:
        test_run_id = record['TestRunId']
        print("Test_Run_Id" , test_run_id)
        token = app.acquire_token_for_client([str("6af0841e-c789-4b7b-a059-1cec575fbddb/.default")])
        get_testrunid_details = f'https://nga-prod.laas.icloud.intel.com/TestRun/nga_fv_gnr/api/TestRun/{test_run_id}'
        response_test_run_Id = session.get(get_testrunid_details, headers={"Authorization": "Bearer " + token["access_token"]})
        info_test_run_Id = response_test_run_Id.json()
        group_dict = info_test_run_Id['TestGroupIdentifier']
        for key in group_dict:
            if key == 'EntityId':
                ID = group_dict[key]
                print("Entitiy-ID ", ID)
                get_group_details = f'https://nga-prod.laas.icloud.intel.com/Planning/nga_fv_gnr/api/TestGroup/{ID}'
                response_group = session.get(get_group_details, headers={"Authorization": "Bearer " + token["access_token"]})
                group_info = response_group.json()
                #print("Group_info" , group_info)
                Group_Name = group_info['Name']
                print("Group-Name: ",Group_Name)
    except:
        pass
    try:
        if record['StringExternalInfo']:
            for key in record['StringExternalInfo']:
                if key.endswith('_signature'):
                    debug_snapshot = key.split('_')[1]
                    print(debug_snapshot)
                    break
    except:
        debug_snapshot = ""
    try:
        record_data = {
            "Failure Name": record["Name"],
            "Station Name": record["StationName"],
            "Stage": record["StageName"],
            "Debug Snapshot": debug_snapshot,
            "Group Name": Group_Name, 
            "Failure_Id": record["Id"],
            "SightingId": record.get("SightingId", "NA"),
            "AxonSV Record Viewer": axon_sv_record_viewer_link ,
            "Signatures": tags
        }
        extracted_data.append(record_data)


    except:
        pass
    
    

# Output the extracted data
#for item in extracted_data:
#    print(item)

df = pd.DataFrame(extracted_data)
print(df)
# Display the DataFrame
#print(df.to_string(index=False))
df.to_csv("./GNR/NGA_Extracted.csv" , index = False)
output = df.to_string(index=False)


