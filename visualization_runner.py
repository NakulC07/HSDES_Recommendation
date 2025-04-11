import pandas as pd
from Output_visualization import generate_visualizations

# List of projects with their respective file paths and column names
projects = {
    'nga_fv_gnrd': {
        'file_path': './Clustering_Output.csv',
        'sheet_name': 'Clustering_Output',
        'group_col': 'Group Name',
        'output_dir': './output'
    }
}

for project_name, params in projects.items():
    if project_name == 'nga_fv_gnr':
        continue

    # Dynamically determine the cluster column by inspecting the file's header
    df = pd.read_csv(params['file_path'])
    cluster_col_candidates = [col for col in df.columns if 'Clustering' in col]

    if not cluster_col_candidates:
        raise ValueError(f"No clustering column found in {params['file_path']} for project {project_name}.")
    
    # Use the first matching clustering column
    cluster_col = cluster_col_candidates[0]
    print(f"Detected clustering column for {project_name}: {cluster_col}")

    # Call the visualization function with the dynamically determined cluster column
    generate_visualizations(
        file_path=params['file_path'],
        sheet_name=params['sheet_name'],
        cluster_col=cluster_col,
        group_col=params['group_col'],
        output_dir=params['output_dir']
    )