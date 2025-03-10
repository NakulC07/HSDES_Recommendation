import pandas as pd

# File names
file1 = './nga_fv_gnr/Updated_failures_nga_fv_gnr.csv'
file2 = './nga_fv_gnrd/Updated_failures_nga_fv_gnrd.csv'

# Read the CSV files into DataFrames
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# Concatenate the DataFrames vertically
merged_df = pd.concat([df1, df2], ignore_index=True)
merged_df = merged_df.dropna(subset=['Errors'])
    
# Save the merged DataFrame to a new CSV file
merged_df.to_csv('Updated_failures_Merged.csv', index=False)

print("Files have been merged successfully into 'Merged_failures.csv'")
