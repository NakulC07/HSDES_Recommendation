import os
from NGA_Extraction_DB import extract_data_for_project

#proxy
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["http_proxy"] = "http://proxy-chain.intel.com:912"
os.environ["https_proxy"] = "http://proxy-chain.intel.com:912"


# Configuration
app_reg_id = '2e75abe8-764a-4773-9433-d064c27eacbf'
app_reg_secret = 'Uix0KsdXU0Zzv3pN2hmPLHJ+Ti]V?v_i'

# List of projects
projects = ['nga_fv_gnr' , 'nga_fv_gnrd']

for project in projects:
    df = extract_data_for_project(project, app_reg_id, app_reg_secret)

    # Define the directory for the project
    project_dir = f"./{project}"

    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
        print(f"Directory created: {project_dir}")

    # Save the extracted data to a CSV file in the project's directory
    output_file = os.path.join(project_dir, f"{project}_Extracted_DB.csv")
    df.to_csv(output_file, index=False)

    print(f"Data for {project} saved to {output_file}")
