import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def preprocess_group_names(df, error_col, group_col):
    """
    Preprocess the Group Name column by filling empty values based on matching errors.
    """
    # Identify rows with empty Group Name
    empty_group_rows = df[df[group_col].isnull() | (df[group_col] == "")]
    
    # Iterate over rows with empty Group Name
    for index, row in empty_group_rows.iterrows():
        error = row[error_col]
        
        # Find matching rows with the same error and a non-empty Group Name
        matching_rows = df[(df[error_col] == error) & (df[group_col].notnull()) & (df[group_col] != "")]
        
        if not matching_rows.empty:
            # Assign the most common Group Name from matching rows
            df.at[index, group_col] = matching_rows[group_col].mode()[0]
        else:
            # Assign a default group name if no match is found
            df.at[index, group_col] = "Uncategorized"
    
    return df

def generate_visualizations(file_path, sheet_name, cluster_col, group_col, output_dir):
    # Load the CSV file
    df = pd.read_csv(file_path)
    
    # Preprocess Group Name column
    df = preprocess_group_names(df, error_col="Errors", group_col=group_col)
    
    # Extract relevant columns
    cluster_col = df.columns[1]
    clusters = df[cluster_col]
    groups = df[group_col]
    
    # Bar Chart of Cluster Sizes
    group_cluster_counts = df.groupby(group_col)[cluster_col].count()
    
    # Create a mapping of groups to numbers
    group_to_number = {group: i for i, group in enumerate(group_cluster_counts.index, start=1)}
    
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Bar Chart
    plt.figure(figsize=(12, 8))
    sns.barplot(x=[group_to_number[group] for group in group_cluster_counts.index], y=group_cluster_counts.values, palette='viridis')
    plt.title('Number of Errors in Each Group')
    plt.xlabel('Group Number')
    plt.ylabel('Number of Errors')
    plt.legend(title='Group Legend', labels=[f"{num}: {group}" for group, num in group_to_number.items()], loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
    plt.tight_layout()
    bar_chart_path = os.path.join(output_dir, 'bar_chart.png')
    plt.savefig(bar_chart_path, bbox_inches='tight')
    plt.close()
    
    print(f"Visualizations saved to {output_dir}")