import pandas as pd

projects = ["nga_fv_gnr", "nga_fv_gnrd"]

for project in projects:
    # File paths
    clustering_output_file = f'./{project}/{project}_Clustering_Output.csv'
    sentence_similarity_file = f'./{project}/{project}_sentence_similarity.csv'

    # Read the CSV files
    clustering_output_df = pd.read_csv(clustering_output_file)
    sentence_similarity_df = pd.read_csv(sentence_similarity_file)

    # Ensure hsdes_link and axon_link columns are present in clustering_output_df
    if 'hsdes_link' not in clustering_output_df.columns:
        clustering_output_df['hsdes_link'] = ''
    if 'axon_link' not in clustering_output_df.columns:
        clustering_output_df['axon_link'] = ''

    # Perform a VLOOKUP-like merge
    merged_df = pd.merge(sentence_similarity_df, clustering_output_df, how='left', left_on='Base index', right_on='Failure Name')

    # Drop unnecessary columns if needed
    merged_df = merged_df.drop(columns=['Failure Name'])

    # Save the merged DataFrame to a new CSV file
    output_file = f'./{project}/Combined_cluster_similarity.csv'
    merged_df.to_csv(output_file, index=False)

    print(f"Combined data saved to {output_file}")