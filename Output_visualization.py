import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the Excel file
file_path = './output (8)/output/modelling_output.xlsx'
df = pd.read_excel(file_path, sheet_name='Clusters')

# Extract relevant columns
clusters = df['dbscan_UMAP_BERT_euclidean23']
groups = df['Group']

# 2. Bar Chart of Cluster Sizes
group_cluster_counts = df.groupby('Group')['dbscan_UMAP_BERT_euclidean23'].count()

# Create a mapping of groups to numbers
group_to_number = {group: i for i, group in enumerate(group_cluster_counts.index, start=1)}

plt.figure(figsize=(12, 8))  # Increase figure size
sns.barplot(x=[group_to_number[group] for group in group_cluster_counts.index], y=group_cluster_counts.values, palette='viridis')
plt.title('Number of Errors in Each Group')
plt.xlabel('Group Number')  # Change x-label to 'Group Number'
plt.ylabel('Number of Errors')

# Add legend in the upper right corner
plt.legend(title='Group Legend', labels=[f"{num}: {group}" for group, num in group_to_number.items()], loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')

plt.tight_layout()  # Adjust layout
plt.savefig('bar_chart.png', bbox_inches='tight')  # Save to disk with tight bounding box
#plt.show()
plt.close()

# 1. Cluster Distribution Pie Chart
plt.figure(figsize=(10, 10))  # Increase figure size
plt.pie(group_cluster_counts, labels=[group_to_number[group] for group in group_cluster_counts.index], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('viridis', len(group_cluster_counts)))
plt.title('Cluster Distribution')

# Add legend in the upper right corner
plt.legend(title='Group Legend', labels=[f"{num}: {group}" for group, num in group_to_number.items()], loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')

plt.tight_layout()  # Adjust layout
plt.savefig('pie_chart.png', bbox_inches='tight')  # Save to disk with tight bounding box
#plt.show()
plt.close()
