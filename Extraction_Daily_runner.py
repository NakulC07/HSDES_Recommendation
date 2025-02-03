# Second Script: run_extraction.py
from Extraction_Data_Daily import process_project
import os

def main():
    # Read the project name from the file
    with open("current_project.txt", "r") as file:
        project_name = file.read().strip()

    # Define the input file and output directory based on the project name
    input_file = f"./{project_name}/{project_name}_NGA_Daily_Extracted.csv"
    output_dir = f"./{project_name}"

    # Check if the input file exists
    if not os.path.isfile(input_file):
        print(f"Input file '{input_file}' does not exist. Please check the project name and try again.")
        return

    # Process the project
    process_project(
        project_name=project_name,
        input_file=input_file,
        output_dir=output_dir
    )

if __name__ == "__main__":
    main()
