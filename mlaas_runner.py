import os
import requests
import time
import zipfile
import pandas as pd

# Define the base URL of the API
BASE_URL = 'https://ssmp.intel.com:9001/api'
token = os.getenv('SSMPTOKEN')
MLAAS_OUTPUT = './mlaas_output'

def get_data():
    response = requests.get(f'{BASE_URL}/data', verify=False)
    return response.json()

def add_job(project_name, input_fields, file_path):
    with open(file_path, 'rb') as file:
        files = {'file': file}
        data = {'project_name': project_name, 'input_fields': input_fields}
        headers = {'Authorization': f'{token}'}
        response = requests.post(f'{BASE_URL}/add_job', headers=headers, files=files, data=data, verify=False)

        if response.status_code == 201:
            try:
                data = response.json()
                print(data)
                return data
            except ValueError as e:
                print("Error decoding JSON:", e)
                print("Response content:", response.text)
        else:
            print("Request failed with status code:", response.status_code)
            print("Response content:", response.text)

def add_clustering_job(model, project_name, multi_inputs, file_path):
    with open(file_path, 'rb') as file:
        files = {'file': file}
        data = {'model': model, 'project_name': project_name, 'multi_inputs': multi_inputs}
        headers = {'Authorization': f'{token}'}
        response = requests.post(f'{BASE_URL}/v1/add_job', headers=headers, files=files, data=data, verify=False)

        if response.status_code == 201:
            try:
                data = response.json()
                print(data)
                return data
            except ValueError as e:
                print("Error decoding JSON:", e)
                print("Response content:", response.text)
        else:
            print("Request failed with status code:", response.status_code)
            print("Response content:", response.text)

def add_similarity_job(model, project_name, index_input, single_input, file_path):
    with open(file_path, 'rb') as file:
        files = {'file': file}
        data = {'model': model, 'project_name': project_name, 'index_input': index_input, 'single_input': single_input}
        headers = {'Authorization': f'{token}'}
        response = requests.post(f'{BASE_URL}/v1/add_job', headers=headers, files=files, data=data, verify=False)

        if response.status_code == 201:
            try:
                data = response.json()
                print(data)
                return data
            except ValueError as e:
                print("Error decoding JSON:", e)
                print("Response content:", response.text)
        else:
            print("Request failed with status code:", response.status_code)
            print("Response content:", response.text)

def download_job_output(job_id):
    url = f'{BASE_URL}/output?job_id={job_id}'
    headers = {'Authorization': f'{token}'}

    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code == 200:
        with open(f'{MLAAS_OUTPUT}/{job_id}_output.zip', 'wb') as file:
            file.write(response.content)
        print(f'File downloaded successfully as {job_id}_output.zip')
        return True
    elif response.status_code == 202:
        print('Job is not complete yet.')
    elif response.status_code == 404:
        print('Output file not found.')
    else:
        print(f'Failed to download file. Status code: {response.status_code}')
    
    return False

def process_clustering_output(file_path, output_csv_path, source_file_path):
    # Read the Excel file
    xls = pd.ExcelFile(file_path)
    
    # Read the first sheet to find the top-ranked Model Name
    df_first_sheet = pd.read_excel(xls, sheet_name=0)
    top_model_name = df_first_sheet.loc[df_first_sheet['Model_Rank'].idxmin()]['Model Name']
    
    # Read the second sheet and keep only the column with the top Model Name
    df_second_sheet = pd.read_excel(xls, sheet_name=1)
    df_filtered = df_second_sheet[['Errors', top_model_name]]

    # Read the source csv file and merge into the clustering csv output
    df_source = pd.read_csv(source_file_path)
    df_filtered['Failure Name'] = df_source['Failure Name']

    # Save the filtered DataFrame to a CSV file
    df_filtered.to_csv(output_csv_path, index=False)
    print(f"Processed clustering output saved to {output_csv_path}")

def main():
    # basic test
    print("get data...")
    response = get_data()
    print(f"Complete Response: {response}")

    # check if MLAAS_OUTPUT exists
    if not os.path.exists(MLAAS_OUTPUT):
        os.makedirs(MLAAS_OUTPUT)
        print(f"Folder '{MLAAS_OUTPUT}' created.")
    else:
        print(f"Folder '{MLAAS_OUTPUT}' already exists.")

    projects = ['nga_fv_gnr', 'nga_fv_gnrd']

    for project in projects:
        print("Adding a clustering job...")
        # Define the file to upload
        FILE_PATH = f'{project}/Updated_failures_{project}.csv'
        add_job_response = add_clustering_job('choice1', 'HSDES_recommendation_clustering_job', '["Errors"]', FILE_PATH)
        job_id = add_job_response['project_data'].get('job_id')
        print(f"Job ID: {job_id}")

        while not download_job_output(job_id):
            # Check for updates every 5 mins
            time.sleep(300)

        zip_file_path = f'{MLAAS_OUTPUT}/{job_id}_output.zip'
        file_to_extract = f'output/modelling_output.xlsx'
        clustering_output_file = f'./{project}/{project}_Clustering_Output.xlsx'
        processed_clustering_output_csv = f'./{project}/{project}_Clustering_Output.csv'
        # Open the ZIP file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Extract the specific file
            zip_ref.extract(file_to_extract, f'./')
        if os.path.exists(clustering_output_file):
            os.remove(clustering_output_file)
        os.rename(file_to_extract, clustering_output_file)

        # Process the clustering output
        process_clustering_output(clustering_output_file, processed_clustering_output_csv, FILE_PATH)

        print("Adding a similarity job...")
        # Define the file to upload
        FILE_PATH = f'{project}/Updated_failures_{project}.csv'
        add_job_response = add_similarity_job('app1', 'HSDES_recommendation_similarity_job', 'Failure Name', 'Errors', FILE_PATH)
        job_id = add_job_response['project_data'].get('job_id')
        print(f"Job ID: {job_id}")

        while not download_job_output(job_id):
            # Check for updates every 5 mins
            time.sleep(300)
        
        zip_file_path = f'{MLAAS_OUTPUT}/{job_id}_output.zip'
        file_to_extract = f'output/sentence_similarity.csv'
        sentence_similarity_file = f'./{project}/{project}_sentence_similarity.csv'
        # Open the ZIP file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Extract the specific file
            zip_ref.extract(file_to_extract, f'./')
        if os.path.exists(sentence_similarity_file):
            os.remove(sentence_similarity_file)
        os.rename(file_to_extract, sentence_similarity_file)

if __name__ == '__main__':
    main()
