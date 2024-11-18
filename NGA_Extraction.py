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
 
project_name = input("Enter the project name (e.g., 'nga_fv_gnr'): ")
#failure_id = input("Enter the failure ID (e.g., '35fcdd7f-b2ff-426a-a9a8-bf1261d4f4c1'): ")

#get_failure_details = 'https://nga-prod.laas.icloud.intel.com/Failure/fv_gnr_sp/api/Failure/a9d5c005-cef6-43b2-9570-fd06a24693a7'
#get_failure_details = f'https://nga-prod.laas.icloud.intel.com/Failure/{project_name}/api/Failure/{failure_id}'
get_failure_details = f'https://nga-prod.laas.icloud.intel.com/Failure/{project_name}/api/Failure/Failures/1'
 
response = session.get(get_failure_details, headers={"Authorization": "Bearer " + token["access_token"]})
#print(response.json())



# Convert the response to JSON and then to a string
response_data = response.json()
'''
for record in response_data["Records"]:
    if "AttachedDate" in record:
        del record["AttachedDate"]
    if "StringExternalInfo" in record:
        del record["StringExternalInfo"]
    if "test_failed_Acquire_Idle_Time" in record:
        del record["test_failed_Acquire_Idle_Time"]
    if "Globals_OD_version" in record:
        del record["Globals_OD_version"]
    if "UpdatedBy" in record:
        del record["UpdatedBy"]
    if "StringExternalInfos" in record:
        del record["StringExternalInfos"]
'''
#response_text = json.dumps(response_data)

#print(response_data['Records'][1])


#file_path = 'failure_details.json'
    
    # Write the JSON data to the file
#with open(file_path, 'w') as file:
#    json.dump(response_data, file, indent=4)

#print(f"JSON data has been written to {file_path}")

number_of_records = response_data['RecordsCount']

print("Number of records:", number_of_records)



    

'''
connector = OpenAIConnector()

i = 0;
for i in range (number_of_records):
    prompt = f"Take this input {i}'{response_data['Records'][i]}'"
    messages = [
        {"role": "system", "content": "summary"},
        {"role": "user", "content": prompt}
    ]
    res = connector.run_prompt(messages)
    print(f"The response: {res['response']}")
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
prompt = f"For last {i} json text input of failures summarize that captures key information, including only Sighting ID, general discription, error signatures, failed steps.Write this in table. "
messages = [
        {"role": "system", "content": "summary"},
        {"role": "user", "content": prompt}
    ]
res = connector.run_prompt(messages)
print(f"The response: {res['response']}")
'''

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
    axon_sv_record_viewer_key = next((key for key in record.get("StringExternalInfo", {}) if key.startswith("AxonSV Record Viewer")), None)
    
    # Extract the AxonSV Record Viewer link using the found key, or use None if the key wasn't found
    axon_sv_record_viewer_link = record.get("StringExternalInfo", {}).get(axon_sv_record_viewer_key, None)
    
    # Safely extract signatures or use an empty list if 'Signatures' key is not present
    signatures = [signature["Signature"] for signature in record.get("Signatures", [])]
    tags = record.get("Tags", [])
    record_data = {
        "Failure Name": record["Name"],
        "Station Name": record["StationName"],
        "Stage": record["StageName"],
        "Debug Snapshot": record['TestRunId'],
        "Failure_Id": record["Id"],
        "SightingId": record.get("SightingId", "NA"),
        "AxonSV Record Viewer": axon_sv_record_viewer_link ,
        "Signatures": tags
    }
    extracted_data.append(record_data)
    

# Output the extracted data
#for item in extracted_data:
#    print(item)

df = pd.DataFrame(extracted_data)
print(df)
# Display the DataFrame
#print(df.to_string(index=False))

output = df.to_string(index=False)


'''import pandas as pd
import io
from io import StringIO



# Split the output into chunks of 10 lines
lines = output.split('\n')
chunks = [lines[i:i + 10] for i in range(0, len(lines), 10)]
for chunk in chunks:
    print(chunk)
    print("\n")


# Function to replace characters in string values
def replace_characters_in_string(text, char_to_replace1, replacement1, char_to_replace2, replacement2):
    text = text.replace(char_to_replace1, replacement1)
    text = text.replace(char_to_replace2, replacement2)
    return text

# Assuming 'chunks' is a list of chunks of data to be processed
# Initialize the OpenAI connector
connector = OpenAIConnector()

# Read the existing Excel file into a DataFrame or create a new one if it doesn't exist
try:
    existing_df = pd.read_excel('response11.xls')
except FileNotFoundError:
    existing_df = pd.DataFrame()

for chunk in chunks:
    # Create the prompt using the chunk of data
    prompt = f"{chunk} With given data of failures bucketize similar Failure_Id (not SightingId) with respect to similar Signatures and in table share corresponding StageName for the Failure_IDs. Table should look like ID(all similar IDs) | Signature | StageName. Display table properly aligned. Do it for all IDs, even if its unique have unique entry in table. Have all the FailureIDs in table don't miss even a single ID"
    
    # Create messages for the prompt
    messages = [
        {"role": "system", "content": "summary"},
        {"role": "user", "content": prompt}
    ]
    
    # Run the prompt through the OpenAI model
    res = connector.run_prompt(messages)
    response_text = res['response']
    
    # Replace newline escape characters with actual newlines
    response_text = response_text.replace('\\n', '\n')
    
    # Replace characters in the response if needed
    response_text = replace_characters_in_string(response_text, ',', ';', '|', ',')
    
    # Convert the response text to a DataFrame
    new_data_df = pd.read_csv(pd.compat.StringIO(response_text), sep='|')
    
    # Append the new data to the existing DataFrame
    existing_df = existing_df.append(new_data_df, ignore_index=True)

# Save the updated DataFrame back to the Excel file
existing_df.to_excel('response12.xls', index=False)'''



'''#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$44444
import pandas as pd

# Assuming 'df' is your DataFrame and 'extracted_data' is defined
#df = pd.DataFrame(extracted_data)
#output = df.to_string(index=False)

# Function to replace characters in dictionary values
def replace_characters_in_dict_values(dictionary, char_to_replace1, replacement1, char_to_replace2, replacement2):
    for key, value in dictionary.items():
        if isinstance(value, str):  # Ensure the value is a string
            value = value.replace(char_to_replace1, replacement1)
            value = value.replace(char_to_replace2, replacement2)
            dictionary[key] = value
    return dictionary

# Split the output into chunks of 10 lines
lines = output.split('\n')
chunks = [lines[i:i + 10] for i in range(0, len(lines), 10)]
for chunk in chunks:
    print(chunk)
    print("\n")
    
# Initialize the OpenAI connector
connector = OpenAIConnector()


prompt = f"{output} With given data of failures bucketize similar Failure_Id (not SightingId) with respect to similar Signatures and in table share corresponding StageName for the Failure_IDs. Table should look like ID(all similar IDs) | Signature | StageName. Display table properly aligned. Do it for all IDs, even if its unique have unique entry in table. Have all the FailureIDs in table don't miss even a single ID"
        
# Create messages for the prompt
messages = [
    {"role": "system", "content": "summary"},
    {"role": "user", "content": prompt}
]

# Run the prompt through the OpenAI model
res = connector.run_prompt(messages)
print(res)


# Open the CSV file for appending
with open("response13.csv", "a", encoding='utf-8') as file:
    for chunk in chunks:
        #chunk_output = '\n'.join(chunk)
        prompt = f"{chunk} With given data of failures bucketize similar Failure_Id (not SightingId) with respect to similar Signatures and in table share corresponding StageName for the Failure_IDs. Table should look like ID(all similar IDs) | Signature | StageName. Display table properly aligned. Do it for all IDs, even if its unique have unique entry in table. Have all the FailureIDs in table don't miss even a single ID"
        
        # Create messages for the prompt
        messages = [
            {"role": "system", "content": "summary"},
            {"role": "user", "content": prompt}
        ]
        
        # Run the prompt through the OpenAI model
        res = connector.run_prompt(messages)
        response_text = res['response']
        response_text = response_text.replace('\\n', '\n')
        print(response_text)
        # Replace characters in the response
        response_text = replace_characters_in_dict_values(res, ',', ';', '|', ',')
        
        # Write the processed response to the CSV file
        file.write(f"{response_text}")'''

# EOA - The code processes data in chunks of 10 lines, sends prompts to an AI model, applies character replacements, and appends results to a CSV file.

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$44444'''

#################################################################################'''

'''
#Use the response_text as the prompt for the OpenAI model
connector = OpenAIConnector()
#prompt = f"Given the following data from a sighting report, provide a concise summary that captures the key information, including only Sighting ID, general discription, error signatures, failed steps.Write this in table. this is the data '{response_text}' display data for all Records"
#prompt = f"With give data {output}, bucketize all failures with corresponding IDs with similar signatures in one table, which has complete signature and Stage name."
prompt = f"{output} With given data of failures bucketize Failure_Id (not SightingId) with respect to similar Signatures and in table share corresponsing StageName for the Failure_IDs. Table should look like ID(all similar IDs) | Signature | StageName. Use dashed line to seperate the bucketed failure_id rows. Display table properly alligned.Do it for all IDs, even if its unique have unique entry in table. Have all the FailureIDs in table dont miss even a single ID"


print(f"\n\n\n\n\n\n###################################################Prompt#############################################\n{output}\n\nWith given data of failures bucketize Failure_Id (not SightingId) with respect to similar Signatures and in table share corresponsing StageName for the Failure_IDs. Table should look like ID(all similar IDs) | Signature | StageName. Use dashed line to seperate the bucketed failure_id rows. Display table properly alligned.Do it for all IDs, even if its unique have unique entry in table. Have all the FailureIDs in table dont miss even a single ID\n\n#############################################################################################################\n\n\n\n\n")

messages = [
        {"role": "system", "content": "summary"},
        {"role": "user", "content": prompt}
   ]
#Initialize the OpenAI connector
#connector = OpenAIConnector()
res = connector.run_prompt(messages)



def replace_characters_in_dict_values(dictionary, char_to_replace1, replacement1, char_to_replace2, replacement2):
    for key, value in dictionary.items():
        if isinstance(value, str):  # Ensure the value is a string
            # Replace the first character
            value = value.replace(char_to_replace1, replacement1)
            # Replace the second character
            value = value.replace(char_to_replace2, replacement2)
            # Update the dictionary with the new value
            dictionary[key] = value
    return dictionary
    
#print(f"The response: {res['response']}")    
    
res = replace_characters_in_dict_values(res, ',', ';', '|', ',')
#res1=res


prompt1 = f"{res} write a brief summary for this data in maximum 3-4 sentences."
messages1 = [
        {"role": "system", "content": "summary"},
        {"role": "user", "content": prompt1}
   ]
#Initialize the OpenAI connector
#connector = OpenAIConnector()
res1 = connector.run_prompt(messages1)



#Print the result from OpenAI
print("\n################Response################\n" )
print(f"The response: {res['response']}")
file_name = now.strftime("Failure_summary_%Y-%m-%d_%H-%M-%S.csv")
file_name1 = now.strftime("Failure_input_%Y-%m-%d_%H-%M-%S.txt")


file = open(file_name, "w")
file.write(res['response'])
file.close()  # Explicitly closing the file

file = open(file_name1, "w")
file.write(output)
file.close()  # Explicitly closing the file

#df1 = pd.read_csv(StringIO(res1['response']))
# Convert the DataFrame to a CSV string with tab-delimited columns
#csv_string = df.to_csv(index=False, header=True, sep='\t')

# Apply word wrapping to each line
#wrapped_string = '\n'.join(textwrap.fill(line, width=200) for line in csv_string.splitlines())

# Write the wrapped string to a text file
#with open('output.txt', 'w', encoding='utf-8') as txt_file:
 #   txt_file.write(wrapped_string)

#print("CSV has been converted to a text file with word wrap.")


#prompt2 = f"Continue remaining table succeeding previous response: {res} which you printed earlier"
#messages = [
 #       {"role": "system", "content": "summary"},
  #      {"role": "user", "content": prompt2}
   #]
#Initialize the OpenAI connector
#connector = OpenAIConnector()
#res2 = connector.run_prompt(messages)
#print(f"The response: {res2['response']}")


# After obtaining the response from OpenAI
openai_summary = res['response']

# Prompt for email addresses
email_addresses = input("Please provide one or more comma-separated email recipients: ")

# Prepare the email content
subject_text = f"NGA Failure Summary for ({project_name}) {Date}"
body_text = f"Here is the summary of the failure details:\n Query  ({project_name}): {get_failure_details}\n For a Better look, please open the attached csv. \n\n{openai_summary}\n\n\nThanks and Regards,\nAiTech Trailblazers\nIntel Corporation"
attachments = [f"{file_name}",f"{file_name1}"]
# Send the email
email_connector.sendEmail(
    toaddr=email_addresses,
    fromaddr="your_email@intel.com",
    subjectText=subject_text,
    bodyText=body_text,
    attachments=attachments,
    htmlText=None,  # Use this if you have HTML content
)'''