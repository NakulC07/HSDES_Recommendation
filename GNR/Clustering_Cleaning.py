import pandas as pd

# Load the Excel file
file_path = "./GNR/modelling_output.xlsx"
xls = pd.ExcelFile(file_path , engine = 'openpyxl')

# Load the sheets into DataFrames
performance_metrics_df = pd.read_excel(xls, 'Performance Metrics')
clusters_df = pd.read_excel(xls, 'Clusters')

print(performance_metrics_df.head())
print(clusters_df.head())
# Identify the best performing model based on Model_Rank
best_model_name = performance_metrics_df.loc[performance_metrics_df['Model_Rank'].idxmin(), 'Model Name']

columns_to_keep = ['Errors', best_model_name]
filtered_clusters_df = clusters_df[columns_to_keep]

# Save the filtered Clusters sheet back to the Excel file
with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='replace') as writer:
    filtered_clusters_df.to_excel(writer, sheet_name='Clusters', index=False)

print(f"The best performing model is '{best_model_name}'. The Clusters sheet has been updated accordingly.")
