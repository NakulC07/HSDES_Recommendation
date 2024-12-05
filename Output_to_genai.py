import requests
import urllib3
import http.client
import traceback
import pprint
import os
import json
from requests_kerberos import HTTPKerberosAuth
import pandas as pd
from openai_connector import OpenAIConnector  # Import the OpenAI connector
import textwrap
from io import StringIO
from datetime import datetime
import send_email_connector as email_connector
import base64

# Function to convert image file to base64 string
def image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def replace_characters_in_dict_values(dictionary, char_to_replace1, replacement1, char_to_replace2, replacement2):
    for key, value in dictionary.items():
        if isinstance(value, str):  # Ensure the value is a string
            value = value.replace(char_to_replace1, replacement1)
            value = value.replace(char_to_replace2, replacement2)
            dictionary[key] = value
    return dictionary

def process_cluster(group, connector):
    cluster_number = group['dbscan_UMAP_BERT_euclidean23'].iloc[0]
    output = group.to_string(index=False)
    #print("Output:\n",len(output))
    if len(output) > 128000:
        output = output[:128000]
        #print("Output:\n", output)
    prompt = f"""
    Hi, this is the failure report of the last 15/30 days in the GNR-D project. For now, I am providing you with similar hang occurrences with some initial insight about the signature.
    The following data contains details about unique failures processed with a clustering algorithm. Each cluster is formed based on the failure signature similarity. The 'Base sentence cluster' column indicates the assigned cluster for each failure. Please provide a detailed summary for each cluster in the following format:
    - **Failure Type {cluster_number} - Cluster {cluster_number}**
    - **Sentences in this cluster primarily involve errors regarding:** [List of key error phrases]
    - **Descriptions highlight multiple systems involved; often centered around:** [Summary of systems and errors]
    - **Typical errors describe situations where:** [Detailed description of typical errors]
    - **The issues are repeatedly tied to:** [Common causes or patterns]
    - **Hsdes link:** [Provide link if available]
    - **Axon Link:** [Provide link if available]
    - **Group Details:** [Highlight different Group]
    Here is the data for the current cluster:
    {output}
    """
    messages = [
        {"role": "system", "content": "You are an AI assistant. Your role is to furnish individuals with comprehensive details."},
        {"role": "user", "content": prompt}
    ]
    res = connector.run_prompt(messages)
    res = replace_characters_in_dict_values(res, ',', ';', '|', ',')
    return res['response']


def summarize_clusters(final_summary):
    # Implement logic to reduce redundancy and summarize common issues
    summarized_output = ""
    clusters = final_summary.split("### **Cluster")
    for cluster in clusters:
        if cluster.strip():
            summarized_output += f"### **Cluster{cluster}\n"
    return summarized_output

if __name__ == "__main__":
    now = datetime.now()
    Date = now.strftime("%Y-%m-%d")
    df = pd.read_excel("./output (8)/output/modelling_output.xlsx", 'Clusters', engine="openpyxl")

    # OpenAI Integration
    connector = OpenAIConnector()
    # Initialize an empty summary
    current_summary = ""
    count = 0
    final_summary = ""
    grouped = df.groupby('dbscan_UMAP_BERT_euclidean23')
    # Process each chunk and update the summary
    for cluster_number, group in grouped:
        #print(f"Group {cluster_number}: ", group)
        current_summary = process_cluster(group, connector)
        print(f"Summary for Cluster {cluster_number}: ", current_summary)
        final_summary += current_summary + "\n"

    print("\n################Response################\n")
    print(f"The response: {final_summary}")

    email_addresses = input("Please provide one or more comma-separated email recipients: ")

    # Load images and convert to base64
    bar_chart_base64 = image_to_base64('bar_chart.png')
    pie_chart_base64 = image_to_base64('pie_chart.png')

    # Prepare the email content
    subject_text = f"AI generated Failure summary with auto Triage - GNR-D {Date}"
    body_text = f"""
    <html>
    <body>
        <p>Dear Reader,</p>
        <p>We are pleased to share the AI-generated summary of the failure details from the GNR-D project. Please find the detailed analysis below:</p>
        
        <h2>Visualizations</h2>
        
        <h3>Number of Errors in Each Cluster</h3>
        <img src="data:image/png;base64,{bar_chart_base64}" alt="Bar Chart">
        <h3>Cluster Distribution</h3>
        <img src="data:image/png;base64,{pie_chart_base64}" alt="Pie Chart">

        <h2>Summary of Failure Details</h2>
        <pre>{final_summary}</pre>       

        <p>Thank you for your attention. Please feel free to reach out if you have any questions or need further assistance.</p>

        <p>Best Regards,<br>Nakul Choudhari<br>Intel Corporation</p>
    </body>
    </html>
    """

    # Send the email
    email_connector.sendEmail(
        toaddr=email_addresses,
        fromaddr="your_email@intel.com",
        subjectText=subject_text,
        bodyText=None,
        htmlText=body_text,  # Use this if you have HTML content
    )
