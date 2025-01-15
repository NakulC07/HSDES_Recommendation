import requests
import urllib3
import http.client
import traceback
import pprint
import os
import json
from requests_kerberos import HTTPKerberosAuth
import pandas as pd
from openai_connector import OpenAIConnector  # Import the OpenAI connector
import textwrap
from io import StringIO
from datetime import datetime
import send_email_connector as email_connector

requests.packages.urllib3.disable_warnings()

class HsdConnector:
    def _get_response(self, req, headers):
        response = requests.get(req, auth=HTTPKerberosAuth(), verify=False, headers=headers)
        if response.ok:
            try:
                response_data = response.json()
                return response_data
            except Exception as e:
                raise e
        else:
            response.raise_for_status()

    def _set_response(self, req, headers, data, operation="put"):
        if operation == "put":
            response = requests.put(req, auth=HTTPKerberosAuth(), verify=False, headers=headers, data=data)
        elif operation == "post":
            response = requests.post(req, auth=HTTPKerberosAuth(), verify=False, headers=headers, data=data)
        else:
            raise ValueError("Unsupported request operation: %s" % (repr(operation),))
        if response.ok:
            try:
                response = response.json()
            except Exception as e:
                return response
            return response
        else:
            response.raise_for_status()

    def get_query(self, q_id, max_number_of_entries_to_read):
        req = "https://hsdes-api.intel.com/rest/query/" + str(q_id) + "?expand=metadata&start_at=1&max_results=" + max_number_of_entries_to_read
        headers = {'Content-type': 'application/json'}
        return self._get_response(req, headers)

    def get_hsd(self, hsd_id, fields=None):
        if fields == "":  # Backwards compatibility
            fields = None
        assert fields is None or (len(fields) > 0 and type(fields) != str and all([type(f) == str for f in fields])), \
            "fields must be None or a list\iterator of strings. Got %s." % (repr(fields),)
        retry = 10
        while (retry > 0):
            try:
                req = "https://hsdes-api.intel.com/rest/article/" + str(hsd_id)
                if fields is not None:
                    req += "?fields=" + "%2C%20".join(fields)
                headers = {'Content-type': 'application/json'}
                response_data = self._get_response(req, headers)
                if "data" in response_data:
                    return response_data["data"][0]
                else:
                    raise Exception('Could not find "data" in response...')
            except urllib3.exceptions.MaxRetryError:
                print('Got "urllib3.exceptions.MaxRetryError" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except requests.exceptions.ProxyError:
                print('Got "requests.exceptions.ProxyError" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except http.client.RemoteDisconnected:
                print('Got "http.client.RemoteDisconnected" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except Exception as e:
                print('Got unknown exception: {}, retrying {} more attempts'.format(traceback.format_exc(), (retry - 1)))
                retry -= 1

    def get_hsd_revision_changeset(self, hsd_id, rev):
        req = "https://hsdes-api.intel.com/rest/article/{}/{}/changeset".format(hsd_id, rev)
        headers = {'Content-type': 'application/json'}
        response_data = self._get_response(req, headers)
        if "changeset" in response_data:
            return response_data["changeset"][0]
        else:
            raise Exception('Could not find "changeset" in response...')

    def get_hsd_user_info(self, user_name):
        req = "https://hsdes-api.intel.com/rest/user/{username}?expand=personal".format(username=user_name)
        headers = {'Content-type': 'application/json'}
        response_data = self._get_response(req, headers)
        if "data" in response_data:
            return response_data["data"][0]
        else:
            raise Exception('Could not find "data" in response...')

    def set_hsd(self, hsd_id, tenant, subject, fields="", values="", operation="put"):
        req = "https://hsdes-api.intel.com/rest/article" + (("/" + str(hsd_id)) if hsd_id is not None else "")
        headers = {'Content-type': 'application/json'}
        data = '{"tenant": "' + str(tenant) + '","subject": "' + str(subject) + '",'
        if len(fields) > 0:
            data += '"fieldValues": ['
            data += '{"' + str(fields[0]) + '": ' + json.dumps(values[0].replace("\n", "\r\n")) + '}'
            for i in range(len(fields) - 1):
                data += ',{"' + str(fields[i + 1]) + '": ' + json.dumps(values[i + 1].replace("\n", "\r\n")) + '}'
            data += ']}'
        return self._set_response(req, headers, data, operation=operation)

    def set_comment(self, tenant, parent_id, description, send_mail=False):
        res = self.set_hsd(None, tenant=tenant, subject="comments", operation="post",
                           fields=["description",
                                   "parent_id",
                                   "send_mail"],
                           values=[description,
                                   parent_id,
                                   "true" if send_mail else "false",
                                   ])
        return res['new_id']

    def get_hsd_links(self, hsd_id, fields=""):
        retry = 10
        while (retry > 0):
            try:
                req = "https://hsdes-api.intel.com/rest/article/" + str(hsd_id) + "/links"
                if len(fields) > 0:
                    req += "?fields=" + str(fields[0])
                    for i in range(len(fields) - 1):
                        req += "%2C%20" + str(fields[i + 1])
                    req += "&showHidden=Y&showDeleted=N"
                headers = {'Content-type': 'application/json'}
                response_data = self._get_response(req, headers)
                if "responses" in response_data:
                    return response_data
                else:
                    raise Exception('Could not find "data" in response...')
            except urllib3.exceptions.MaxRetryError:
                print('Got "urllib3.exceptions.MaxRetryError" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except requests.exceptions.ProxyError:
                print('Got "requests.exceptions.ProxyError" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except http.client.RemoteDisconnected:
                print('Got "http.client.RemoteDisconnected" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except Exception as e:
                print('Got unknown exception: {}, retrying {} more attempts'.format(traceback.format_exc(), (retry - 1)))
                retry -= 1

def replace_characters_in_dict_values(dictionary, char_to_replace1, replacement1, char_to_replace2, replacement2):
    for key, value in dictionary.items():
        if isinstance(value, str):  # Ensure the value is a string
            value = value.replace(char_to_replace1, replacement1)
            value = value.replace(char_to_replace2, replacement2)
            dictionary[key] = value
    return dictionary

def process_data_in_chunks(df, connector, chunk_size=10):
    extracted_data = []
    final_summary = ""

    for chunk in df:
        chunk_summary = ""
        for link in chunk['hsdes_link'].dropna():
            val = link.split('/')
            hsd_id = val[6]
            hsd = HsdConnector()
            data = hsd.get_hsd(hsd_id)
            extracted_data.append(data)

        df_extracted = pd.DataFrame(extracted_data)
        output = df_extracted.to_string(index=False)

        # Split output into smaller parts if necessary
        lines = output.split('\n')
        smaller_chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]

        for small_chunk in smaller_chunks:
            try:
                prompt = f"{small_chunk} With given data of failures analyze everything and give proper report of it without missing a single data."
                messages = [
                    {"role": "system", "content": "summary"},
                    {"role": "user", "content": prompt}
                ]
                res = connector.run_prompt(messages)
                res = replace_characters_in_dict_values(res, ',', ';', '|', ',')
                chunk_summary += res['response'] + "\n"
            except OpenAIConnector.BadRequestError as e:
                print(f"Error processing chunk: {e}")
                continue

        final_summary += chunk_summary

    return final_summary

if __name__ == "__main__":
    now = datetime.now()
    Date = now.strftime("%Y-%m-%d")
    df = pd.read_csv("./GNR/Updated_failures_GNR.csv")
    hsdes_links = df['hsdes_link']
    username = os.environ.get("USERNAME", "ginaburt")
    user = input("Give me an IDSD (user) go get info from HSD system [%s]: " % (username,))
    if user == "":
        user = username

    # Split the dataframe into chunks of 50 rows each
    chunk_size = 50
    chunks = [df[i:i + chunk_size] for i in range(0, df.shape[0], chunk_size)]

    connector = OpenAIConnector()
    final_summary = process_data_in_chunks(chunks, connector)

    file_name = now.strftime("Failure_summary_%Y-%m-%d_%H-%M-%S.csv")
    file_name1 = now.strftime("Failure_input_%Y-%m-%d_%H-%M-%S.txt")

    with open(file_name, "w") as file:
        file.write(final_summary)

    with open(file_name1, "w") as file:
        file.write(df.to_string(index=False))

    print("\n################Response################\n")
    print(f"The response: {final_summary}")

    email_addresses = input("Please provide one or more comma-separated email recipients: ")

    # Prepare the email content
    subject_text = f"NGA Failure Summary for (nga_fv_gnr) {Date}"
    body_text = f"Here is the summary of the failure details:\n Query  (nga_fv_gnr): {final_summary}\n For a Better look, please open the attached csv. \nThanks and Regards,\nNakul Choudhari\nIntel Corporation"
    attachments = [f"{file_name}", f"{file_name1}"]

    # Send the email
    email_connector.sendEmail(
        toaddr=email_addresses,
        fromaddr="your_email@intel.com",
        subjectText=subject_text,
        bodyText=body_text,
        attachments=attachments,
        htmlText=None,  # Use this if you have HTML content
    )