import pandas as pd

projects = ["nga_fv_gnr", "nga_fv_gnrd"]

for project in projects:
    # File paths
    clustering_output_file = f'./{project}/{project}_Clustering_Output.csv'
    sentence_similarity_file = f'./{project}/{project}_sentence_similarity.csv'
    db_file = f'./{project}/Updated_failures_{project}.csv'
    
    # Read the CSV files
    clustering_output_df = pd.read_csv(clustering_output_file)
    sentence_similarity_df = pd.read_csv(sentence_similarity_file)
    db_df = pd.read_csv(db_file)
    # Add 'Failure Name', 'hsdes_link', and 'axon_link' columns from db_df to clustering_output_df if they do not exist
    columns_to_add = ['Failure Name', 'hsdes_link', 'axon_link', 'Group Name']
    for col in columns_to_add:
        if col not in clustering_output_df.columns and col in db_df.columns:
            clustering_output_df = clustering_output_df.merge(db_df[['Failure Name', 'hsdes_link', 'axon_link', 'Group Name']], on='Failure Name', how='left')
    
    clustering_output_df.to_csv(clustering_output_file , index=False)
    print(f"Updated the {clustering_output_file}")
    # Perform a VLOOKUP-like merge
    if 'Failure Name' in clustering_output_df.columns:
        merged_df = pd.merge(sentence_similarity_df, clustering_output_df, how='left', left_on='Base index', right_on='Failure Name')
    else:
        print(f"'Failure Name' column not found in {clustering_output_file}. Skipping project {project}.")
        continue

    # Columns to keep
    columns_to_keep = [
        'Base index', 'Base Sentence', 'Compared index', 'Compared Sentence', 'Similarity',
        'Errors', 'hsdes_link', 'axon_link', 'Group Name', 'Failure Name' , 'Group'
    ]

    # Identify and handle additional columns
    for col in merged_df.columns:
        if col not in columns_to_keep:
            if 'Unnamed' in col:
                merged_df = merged_df.drop(columns=[col])
            else:
                merged_df.rename(columns={col: 'Base Sentence Cluster'}, inplace=True)
    
    # Drop unnecessary columns if needed
    merged_df = merged_df.drop(columns=['Failure Name'])

    # Save the merged DataFrame to a new CSV file
    output_file = f'./{project}/Combined_cluster_similarity.csv'
    merged_df.to_csv(output_file, index=False)

    print(f"Combined data saved to {output_file}")
