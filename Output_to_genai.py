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

def replace_characters_in_dict_values(dictionary, char_to_replace1, replacement1, char_to_replace2, replacement2):
    for key, value in dictionary.items():
        if isinstance(value, str):  # Ensure the value is a string
            value = value.replace(char_to_replace1, replacement1)
            value = value.replace(char_to_replace2, replacement2)
            dictionary[key] = value
    return dictionary

def process_chunk(chunk, connector, current_summary):
    cluster_number = chunk['dbscan_UMAP_BERT_euclidean23']
    output = chunk.to_string(index=False)
    prompt = f"""
    {current_summary}
    Hi, this is the failure report of the last 15/30 days in the GNR-D project. For now, I am providing you with similar hang occurrences with some initial insight about the signature.
    The following data contains details about unique failures processed with a clustering algorithm. Each cluster is formed based on the failure signature similarity. The 'Base sentence cluster' column indicates the assigned cluster for each failure. Please provide a detailed summary for each cluster in the following format:
    - **Failure Type {cluster_number} - Cluster {cluster_number}**
    - **Sentences in this cluster primarily involve errors regarding:** [List of key error phrases]
    - **Descriptions highlight multiple systems involved; often centered around:** [Summary of systems and errors]
    - **Typical errors describe situations where:** [Detailed description of typical errors]
    - **The issues are repeatedly tied to:** [Common causes or patterns]
    - **Hsdes link:** [Provide link if available]
    - **Axon Link:** [Provide link if available]
    Here is the data for the current chunk:
    {output}
    """
    messages = [
        {"role": "system", "content": "You are an AI assistant. Your role is to furnish individuals with comprehensive details."},
        {"role": "user", "content": prompt}
    ]
    res = connector.run_prompt(messages)
    res = replace_characters_in_dict_values(res, ',', ';', '|', ',')
    return res['response']

if __name__ == "__main__":
    now = datetime.now()
    Date = now.strftime("%Y-%m-%d")
    df = pd.read_excel("./output (8)/output/modelling_output.xlsx" , 'Clusters' , engine = "openpyxl")

    # OpenAI Integration
    connector = OpenAIConnector()

    # Split the dataframe into chunks of 50 rows each
    chunk_size = 50
    chunks = [df[i:i + chunk_size] for i in range(0, df.shape[0], chunk_size)]

    # Initialize an empty summary
    current_summary = ""
    count = 0
    final_summary = ""

    # Process each chunk and update the summary
    for chunk in chunks:
        count += 1
        if count == 10:
            break
        current_summary = process_chunk(chunk, connector, current_summary)
        final_summary += current_summary + "\n"

    file_name = now.strftime("Failure_summary_%Y-%m-%d_%H-%M-%S.csv")
    file_name1 = now.strftime("Failure_input_%Y-%m-%d_%H-%M-%S.txt")

    with open(file_name, "w") as file:
        file.write(final_summary)
    with open(file_name1, "w") as file:
        file.write(df.to_string(index=False))

    print("\n################Response################\n")
    print(f"The response: {final_summary}")

    email_addresses = input("Please provide one or more comma-separated email recipients: ")

    # Prepare the email content
    subject_text = f"AI generated Failure summary with auto Triage - GNR-D {Date}"
    body_text = f"Here is the summary of the failure details:\n Query  GNR-D: {final_summary}\n For a Better look, please open the attached csv. \nThanks and Regards,\nNakul Choudhari\nIntel Corporation"
    attachments = [f"{file_name}"]

    # Send the email
    email_connector.sendEmail(
        toaddr=email_addresses,
        fromaddr="your_email@intel.com",
        subjectText=subject_text,
        bodyText=body_text,
        attachments=attachments,
        htmlText=None,  # Use this if you have HTML content
    )
