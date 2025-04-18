# First Script: extract_project.py
from NGA_Extraction import extract_data_for_project
import os

#proxy
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["http_proxy"] = "http://proxy-chain.intel.com:912"
os.environ["https_proxy"] = "http://proxy-chain.intel.com:912"
# Configuration
app_reg_id = '2e75abe8-764a-4773-9433-d064c27eacbf'
app_reg_secret = 'Uix0KsdXU0Zzv3pN2hmPLHJ+Ti]V?v_i'

# Prompt the user for the project name
projects = ['nga_fv_gnrd']

# Store the project name in a temporary file

for project_name in projects:
    #if project_name == 'nga_fv_gnr':
    #    continue
    with open("current_project.txt", "w") as file:
        file.write(project_name)

    # Define the output directory based on the project name
    output_dir = f"./{project_name}"

    # Extract data for the project
    extract_data_for_project(project_name, app_reg_id, app_reg_secret, output_dir)
