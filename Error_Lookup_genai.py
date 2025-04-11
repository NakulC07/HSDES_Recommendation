import os
import pandas as pd
import base64
import re
from datetime import datetime
from openai_connector import OpenAIConnector
import send_email_connector as email_connector
from HSDES_Extraction import HsdConnector , process_data_in_chunks
import time

def image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def make_links_clickable(text):
    if text is None:
        return
    url_pattern = re.compile(r'(http[s]?://\S+)')
    return url_pattern.sub(r'<a href="\1">\1</a>', text)

def process_cluster(group, connector, hsd_connector):
    hsdes_link = group['hsdes_link']
    axon_link = group['axon_link']
    cluster_number = group['Base Sentence Cluster']
    hsd_summary = None

    # Skip processing if hsdes_link does not exist or is empty
    if not isinstance(hsdes_link, str) or not hsdes_link.strip():
        print(f"Skipping cluster {cluster_number} due to missing hsdes_link.")
        return None

    if isinstance(hsdes_link, str):
        val = hsdes_link.split('/')
        hsd_id = val[6]
        hsd_data = hsd_connector.get_hsd(hsd_id)
        hsd_summary = process_data_in_chunks(pd.DataFrame([hsd_data]), connector)
        hsd_summary = f"HSDES Summary for {hsd_id}: {hsd_summary}"

    output = group.to_string(index=False)
    if len(output) > 128000:
        output = output[:128000]

    prompt = f"""
    Hi, this is the failure report of the last 2 days in the project. For now, I am providing you with similar hang occurrences with some initial insight about the signature.
    The following data contains details about unique failures processed with a clustering algorithm. Each cluster is formed based on the failure signature similarity. The 'Base sentence cluster' column indicates the assigned cluster for each failure. Please provide a detailed summary for each cluster in the following HTML format:
    <div>
        <strong>Failure Type {cluster_number} - Cluster {cluster_number}</strong>
        <ul>
            <li><strong>Sentences in this cluster primarily involve errors regarding:</strong> [List of key error phrases]</li>
            <li><strong>Hsdes link:</strong> Please list each link completely with a description <a href="{hsdes_link}">{hsdes_link}</a>, e.g., "HSDES Link for PCIe Issue"</li>
            <li><strong>Axon Link:</strong> Please list each link completely with a description <a href="{axon_link}">{axon_link}</a>, e.g., "Axon Link for PCIe Issue"</li>
            <li><strong>Root Cause Notes</strong></li>
            <li><strong>Fix Description</strong></li>
            <li><strong>Component</strong></li>
            <li><strong>Comments</strong></li>
        </ul>
    </div>
    Extract the following details from the given data of failures and provide a comprehensive report:
    
    Here is the data for the current cluster:
    {output}
    {hsd_summary}
    """
    messages = [
        {"role": "system", "content": "You are an AI assistant. Your role is to furnish individuals with comprehensive details."},
        {"role": "user", "content": prompt}
    ]
    res = connector.run_prompt(messages)
    response = res['response']
    formatted_response = make_links_clickable(response)
    formatted_response = response.replace("**", "")
    formatted_response = re.sub(r'\)\)', ')', formatted_response)
    return formatted_response

def get_top_similar_entries(hang_error, hang_error_df):
    escaped_hang_error = re.escape(hang_error)
    matched_entries = hang_error_df[hang_error_df['Base Sentence'].str.contains(escaped_hang_error, na=False)]
    top_similar_entries = matched_entries.sort_values(by='Similarity', ascending=False).head(3)
    return top_similar_entries

def consolidate_summaries(summaries):
    consolidated = {}

    for summary in summaries:
        # Extract failure type and cluster from the summary
        failure_type_match = re.search(r'Failure Type (\d+)', summary)
        cluster_match = re.search(r'Cluster (\d+)', summary)
        failure_type = failure_type_match.group(1)
        cluster = cluster_match.group(1)

        # Use (failure_type, cluster) as the grouping key
        key = (failure_type, cluster)

        # Initialize the group if it doesn't exist
        if key not in consolidated:
            consolidated[key] = []

        # Append the summary to the group
        consolidated[key].append(summary)

    # Combine summaries for each group
    consolidated_summaries = []
    for key, group_summaries in consolidated.items():
        # Merge summaries into a single string
        combined_summary = "\n".join(group_summaries)
        consolidated_summaries.append(combined_summary)

    return consolidated_summaries

def extract_links(html_string):
    hsdes_link_pattern = re.compile(r'<li><strong>Hsdes link:</strong>.*?<a href="(.*?)">')
    axon_link_pattern = re.compile(r'<li><strong>Axon Link:</strong>.*?<a href="(.*?)">')

    hsdes_link_match = hsdes_link_pattern.search(html_string)
    axon_link_match = axon_link_pattern.search(html_string)

    hsdes_link = hsdes_link_match.group(1) if hsdes_link_match else None
    axon_link = axon_link_match.group(1) if axon_link_match else None

    return hsdes_link, axon_link


def generate_html_table(summaries):
    html = """
    <html>
    <body>
        <h2>Summary of Daily Failure Details</h2>
        <table border="1" style="width:100%; border-collapse: collapse; text-align: left;">
            <tr>
                <th>Failure Type</th>
                <th>Error</th>
                <th>Root Cause Notes</th>
                <th>Fix Description</th>
                <th>HSDES Links</th>
                <th>Component</th>
                <th>Comments</th>
            </tr>
    """
    for summary in summaries:
        #cluster = re.search(r'Cluster (\d+)', summary).group(1)
        hsdes_link, axon_link = extract_links(summary)

        # Skip rows where hsdes_link is None or empty
        if not hsdes_link:
            continue

        failure_type = "New Failure type" if hsdes_link is None else "Failure Type exists"
        error_descriptions = re.search(r'<li><strong>Sentences in this cluster primarily involve errors regarding:</strong> (.*?)</li>', summary)
        time.sleep(1)
        if error_descriptions is not None:
            error_descriptions=error_descriptions.group(1)
        hsdes_link = make_links_clickable(hsdes_link)
        time.sleep(1)
        root_cause_notes = re.search(r'Root Cause Notes:\s*(.*?)(?=\n|$)', summary)
        time.sleep(1)
        fix_description = re.search(r'Fix Description:\s*(.*?)(?=\n|$)', summary)
        time.sleep(1)
        component = re.search(r'Component:\s*(.*?)(?=\n|$)', summary)
        time.sleep(1)
        comments = re.search(r'Comments:\s*(.*?)(?=\n|$)', summary)
        
        root_cause_notes = root_cause_notes.group(1).strip() if root_cause_notes else "N/A"
        fix_description = fix_description.group(1).strip() if fix_description else "N/A"
        component = component.group(1).strip() if component else "N/A"
        comments = comments.group(1).strip() if comments else "N/A"
        html += f"""
            <tr>
                <td>{failure_type}</td>
                <td>{error_descriptions}</td>
                <td>{root_cause_notes}</td>
                <td>{fix_description}</td>
                <td>{hsdes_link}</td>
                <td>{component}</td>
                <td>{comments}</td>
            </tr>
        """
    html += """
        </table>
    </body>
    </html>
    """
    return html
def process_project(project_name, input_dir, output_dir):
    now = datetime.now()
    Date = now.strftime("%Y-%m-%d")
    input_file = input_dir + f"/Updated_failures_{project_name}_Daily.csv"
    sentence_similarity_file = "./Combined_cluster_similarity.csv"
    hsd_connector = HsdConnector()
    if not os.path.exists(input_file) or not os.path.exists(sentence_similarity_file):
        print(f"Required files for project '{project_name}' do not exist in '{input_dir}'.")
        return

    failures_df = pd.read_csv(input_file)
    failures_df = failures_df.loc[:, ~failures_df.columns.str.contains('^Unnamed')]
    hang_error_df = pd.read_csv(sentence_similarity_file)
    hang_error_df = hang_error_df.loc[:, ~hang_error_df.columns.str.contains('^Unnamed')]
    hang_errors = failures_df

    
    connector = OpenAIConnector()
    final_summary_list = []

    for index, row in hang_errors.iterrows():
        error_description = row['Errors']
        parts = error_description.split(' ')
        cleaned_parts = [part for part in parts if part != 'None']
        error_description = ''.join(cleaned_parts)
        top_entries = get_top_similar_entries(error_description, hang_error_df)
        for _, entry in top_entries.iterrows():
            entry_summary = process_cluster(entry, connector, hsd_connector)
            if entry_summary:
                final_summary_list.append(entry_summary)

    # Check if there are no failures to report
    if not final_summary_list:
        html_table = """
        <html>
        <body>
            <h2>No Failures Today</h2>
            <p>There are no failures to report for the {project_name} project on {Date}.</p>
        </body>
        </html>
        """.format(project_name=project_name, Date=Date)
    else:
        consolidated_summary = consolidate_summaries(final_summary_list)
        #final_summary_df = pd.DataFrame(consolidated_summaries, columns=['Summary'])
        html_table = generate_html_table(consolidated_summary)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    email_addresses = "nakul.choudhari@intel.com"  # input("Please provide one or more comma-separated email recipients: ")
    bar_chart_base64 = image_to_base64('./output/bar_chart.png')
    subject_text = f"AI generated Failure summary with auto Triage - {project_name} {Date}"
    body_text = f"""
    <html>
    <body>
        <p>Dear Reader,</p>
        <p>We are pleased to share the AI-generated summary of the failure details from the {project_name} project. Please find the detailed analysis below:</p>
        <h2>Visualizations</h2>
        <h3>Number of Errors in Each Group</h3>
        <img src="data:image/png;base64,{bar_chart_base64}" alt="Bar Chart">
        {html_table}
        
        <p>Thank you for your attention. Please feel free to reach out if you have any questions or need further assistance.</p>
        <p>Best Regards,<br>Nakul Choudhari<br>Intel Corporation</p>
    </body>
    </html>
    """
    email_connector.sendEmail(
        toaddr=email_addresses,
        fromaddr="your_email@intel.com",
        subjectText=subject_text,
        bodyText=None,
        htmlText=body_text,
    )
    print(f"Data for {project_name} processed and email sent.")