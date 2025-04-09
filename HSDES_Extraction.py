from requests_kerberos import HTTPKerberosAuth
import requests
import pandas as pd
from openai_connector import OpenAIConnector
from datetime import datetime
import os
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

    def get_hsd(self, hsd_id, fields=None):
        if fields == "":
            fields = None
        assert fields is None or (len(fields) > 0 and not isinstance(fields, str) and all([isinstance(f, str) for f in fields])), \
            "fields must be None or a list/iterator of strings. Got %s." % (repr(fields),)
        retry = 10
        while retry > 0:
            try:
                req = f"https://hsdes-api.intel.com/rest/article/{hsd_id}"
                if fields is not None:
                    req += "?fields=" + "%2C%20".join(fields)
                headers = {'Content-type': 'application/json'}
                response_data = self._get_response(req, headers)
                if "data" in response_data:
                    return response_data["data"][0]
                else:
                    raise Exception('Could not find "data" in response...')
            except (requests.exceptions.RequestException, Exception) as e:
                retry -= 1
                if retry == 0:
                    raise e

def replace_characters_in_dict_values(dictionary, char_to_replace1, replacement1, char_to_replace2, replacement2):
    for key, value in dictionary.items():
        if isinstance(value, str):
            value = value.replace(char_to_replace1, replacement1).replace(char_to_replace2, replacement2)
            dictionary[key] = value
    return dictionary

def process_data_in_chunks(df, connector, chunk_size=50):
    final_summary = ""
    output = df.to_string()
    lines = output.split('\n')
    smaller_chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
    for small_chunk in smaller_chunks:
        try:
            prompt = f"""
            Extract the following details from the given data of failures and provide a comprehensive report:
            - Root Cause Notes
            - Fix Description
            - Component
            - Comments

            Data:
            {''.join(small_chunk)}
            """
            messages = [
                {"role": "system", "content": "summary"},
                {"role": "user", "content": prompt}
            ]
            res = connector.run_prompt(messages)
            res = replace_characters_in_dict_values(res, ',', ';', '|', ',')
            final_summary += res['response'] + "\n"
        except OpenAIConnector.BadRequestError as e:
            print(e)
    return final_summary

def process_project(project_name, input_file, output_dir):
    now = datetime.now()
    Date = now.strftime("%Y-%m-%d")
    df = pd.read_csv(input_file)
    connector = OpenAIConnector()
    final_summary = process_data_in_chunks(df, connector)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_name = os.path.join(output_dir, now.strftime(f"Failure_summary_{project_name}_%Y-%m-%d_%H-%M-%S.csv"))
    file_name1 = os.path.join(output_dir, now.strftime(f"Failure_input_{project_name}_%Y-%m-%d_%H-%M-%S.txt"))

    with open(file_name, "w") as file:
        file.write(final_summary)
    with open(file_name1, "w") as file:
        file.write(df.to_string())

    print(f"Data for {project_name} saved to {file_name} and {file_name1}")