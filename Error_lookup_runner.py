import os
from Error_Lookup_genai import process_project

def main():
    # Prompt the user for the project name
    project_names = ["nga_fv_gnr" , "nga_fv_gnrd"]
    for project_name in project_names:
        # Define the input and output directories based on the project name
        input_dir = f"./{project_name}"
        output_dir = f"./{project_name}/output"

        # Process the project
        process_project(
            project_name=project_name,
            input_dir=input_dir,
            output_dir=output_dir
        )

if __name__ == "__main__":
    main()
