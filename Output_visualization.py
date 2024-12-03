import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import plotly.express as px

from wordcloud import WordCloud

# Load the Excel file
file_path = './output (8)/output/modelling_output.xlsx'
df = pd.read_excel(file_path, sheet_name='Clusters')

# Extract relevant columns
errors = df['Errors']
clusters = df['dbscan_UMAP_BERT_euclidean23']
#print(df.head())

# 2. Bar Chart of Cluster Sizes
cluster_counts = clusters.value_counts().sort_index()
plt.figure(figsize=(10, 6))
sns.barplot(x=cluster_counts.index, y=cluster_counts.values, palette='viridis')
plt.title('Number of Errors in Each Cluster')
plt.xlabel('Cluster Number')
plt.ylabel('Number of Errors')
plt.show()
'''
# 3. Heatmap (if additional features are available)
# Assuming additional features are available in the dataframe
# features = df.drop(columns=['Errors', 'dbscan_UMAP_BERT_euclidean23'])
# sns.heatmap(features.corr(), annot=True, cmap='coolwarm')
# plt.title('Feature Correlation Heatmap')
# plt.show()

# 4. Silhouette Plot
silhouette_avg = silhouette_score(tsne_results, clusters)
sample_silhouette_values = silhouette_samples(tsne_results, clusters)

plt.figure(figsize=(10, 6))
y_lower = 10
for i in np.unique(clusters):
    ith_cluster_silhouette_values = sample_silhouette_values[clusters == i]
    ith_cluster_silhouette_values.sort()
    size_cluster_i = ith_cluster_silhouette_values.shape[0]
    y_upper = y_lower + size_cluster_i

    plt.fill_betweenx(np.arange(y_lower, y_upper),
                      0, ith_cluster_silhouette_values,
                      alpha=0.7)
    plt.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))
    y_lower = y_upper + 10

plt.title('Silhouette Plot')
plt.xlabel('Silhouette Coefficient Values')
plt.ylabel('Cluster Label')
plt.axvline(x=silhouette_avg, color="red", linestyle="--")
plt.show()

# 5. 3D Plot using Plotly
fig = px.scatter_3d(x=tsne_results[:, 0], y=tsne_results[:, 1], z=tsne_results[:, 1],
                    color=clusters.astype(str), title='3D Scatter Plot of Clusters')
fig.show()
'''


# 1. Cluster Distribution Pie Chart
cluster_counts = clusters.value_counts().sort_index()
plt.figure(figsize=(8, 8))
plt.pie(cluster_counts, labels=cluster_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('viridis', len(cluster_counts)))
plt.title('Cluster Distribution')
plt.show()
