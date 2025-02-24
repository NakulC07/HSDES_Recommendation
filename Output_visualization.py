import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_visualizations(file_path, sheet_name, cluster_col, group_col, output_dir):
    # Load the Excel file
    df = pd.read_csv(file_path)
    
    # Extract relevant columns
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
    bar_chart_path = output_dir + '/bar_chart.png'
    plt.savefig(bar_chart_path, bbox_inches='tight')
    plt.close()
    
    # Pie Chart
    '''plt.figure(figsize=(10, 10))
    plt.pie(group_cluster_counts, labels=[group_to_number[group] for group in group_cluster_counts.index], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('viridis', len(group_cluster_counts)))
    plt.title('Cluster Distribution')
    plt.legend(title='Group Legend', labels=[f"{num}: {group}" for group, num in group_to_number.items()], loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
    plt.tight_layout()
    pie_chart_path = os.path.join(output_dir, 'pie_chart.png')
    plt.savefig(pie_chart_path, bbox_inches='tight')
    plt.close()'''
    
    print(f"Visualizations saved to {output_dir}")
