import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the Excel file
file_path = 'C:/NLP_Project_1/GNRD/GNRD_Output.csv'
df = pd.read_csv(file_path)

# Extract relevant columns
clusters = df['agglomerativeClustering_SpectralEmbedding_BERT8']
groups = df['Group Name']

# 2. Bar Chart of Cluster Sizes
group_cluster_counts = df.groupby('Group Name')['agglomerativeClustering_SpectralEmbedding_BERT8'].count()

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
plt.savefig('C:/NLP_Project_1/GNRD/bar_chart.png', bbox_inches='tight')  # Save to disk with tight bounding box
#plt.show()
plt.close()

# 1. Cluster Distribution Pie Chart
plt.figure(figsize=(10, 10))  # Increase figure size
plt.pie(group_cluster_counts, labels=[group_to_number[group] for group in group_cluster_counts.index], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('viridis', len(group_cluster_counts)))
plt.title('Cluster Distribution')

# Add legend in the upper right corner
plt.legend(title='Group Legend', labels=[f"{num}: {group}" for group, num in group_to_number.items()], loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')

plt.tight_layout()  # Adjust layout
plt.savefig('C:/NLP_Project_1/GNRD/pie_chart.png', bbox_inches='tight')  # Save to disk with tight bounding box
#plt.show()
plt.close()
