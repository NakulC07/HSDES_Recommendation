import os
from HSDES_Extraction import process_project

def find_projects_and_files(base_dir):
    projects = {}
    for project_name in os.listdir(base_dir):
        project_dir = os.path.join(base_dir, project_name)
        if os.path.isdir(project_dir):
            # Construct the expected file name based on the project name
            expected_file_name = f"Updated_failures_{project_name.upper()}.csv"
            input_file = os.path.join(project_dir, expected_file_name)
            if os.path.isfile(input_file):
                projects[project_name] = input_file
    return projects

def main():
    # Define the base directory where all project directories are located
    base_dir = "./"

    # Find all projects and their respective input files
    projects = find_projects_and_files(base_dir)

    for project_name, input_file in projects.items():
        # Define the directory for the project
        project_dir = os.path.join(base_dir, project_name)

        # Process the project
        process_project(project_name, input_file, project_dir)

if __name__ == "__main__":
    main()
