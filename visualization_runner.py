from Output_visualization import generate_visualizations

# List of projects with their respective file paths and column names
projects = {
    'nga_fv_gnr': {
        'file_path': './nga_fv_gnr/Combine_cluster_similarity.csv',
        'sheet_name': 'Clusters',
        'cluster_col': 'dbscan_UMAP_BERT_euclidean23',
        'group_col': 'Group',
        'output_dir': './GNR'
    },
    'another_project': {
        'file_path': './AnotherProject/modelling_output.xlsx',
        'sheet_name': 'Clusters',
        'cluster_col': 'another_cluster_column',
        'group_col': 'another_group_column',
        'output_dir': './AnotherProject'
    }
}

for project_name, params in projects.items():
    generate_visualizations(
        file_path=params['file_path'],
        sheet_name=params['sheet_name'],
        cluster_col=params['cluster_col'],
        group_col=params['group_col'],
        output_dir=params['output_dir']
    )
