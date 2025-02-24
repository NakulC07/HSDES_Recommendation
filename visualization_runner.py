from Output_visualization import generate_visualizations

# List of projects with their respective file paths and column names
projects = {
    'nga_fv_gnr': {
        'file_path': './nga_fv_gnr/nga_fv_gnr_Clustering_Output.csv',
        'cluster_col': 'dbscan_UMAP_BERT_euclidean23',
        'sheet_name' : 'nga_fv_gnr_Clustering_Output',
        'group_col': 'Group Name',
        'output_dir': './nga_fv_gnr'
    },
    'nga_fv_gnrd': {
        'file_path': './nga_fv_gnrd/nga_fv_gnrd_Clustering_Output.csv',
        'cluster_col': 'agglomerativeClustering_SpectralEmbedding_BERT8',
        'sheet_name' : 'nga_fv_gnrd_Clustering_Ouptut',
        'group_col': 'Group Name',
        'output_dir': './nga_fv_gnrd'
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
