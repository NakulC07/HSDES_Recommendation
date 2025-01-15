import pandas as pd
import base64
import re
from datetime import datetime
from openai_connector import OpenAIConnector
import send_email_connector as email_connector

# Function to convert image file to base64 string
def image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def make_links_clickable(text):
    # Regular expression to find URLs
    url_pattern = re.compile(r'(http[s]?://\S+)')
    # Replace URLs with clickable links
    return url_pattern.sub(r'<a href="\1">\1</a>', text)

def process_cluster(group, connector):
    print(group)
    cluster_number = group['Base Sentence Cluster']
    output = group.to_string(index=False)
    if len(output) > 128000:
        output = output[:128000]
    prompt = f"""
    Hi, this is the failure report of the last 15/30 days in the GNR-D project. For now, I am providing you with similar hang occurrences with some initial insight about the signature.
    The following data contains details about unique failures processed with a clustering algorithm. Each cluster is formed based on the failure signature similarity. The 'Base sentence cluster' column indicates the assigned cluster for each failure. Please provide a detailed summary for each cluster in the following HTML format:
    <div>
        <strong>Failure Type {cluster_number} - Cluster {cluster_number}</strong>
        <ul>
            <li><strong>Sentences in this cluster primarily involve errors regarding:</strong> [List of key error phrases]</li>
            <li><strong>Descriptions highlight multiple systems involved; often centered around:</strong> [Summary of systems and errors]</li>
            <li><strong>Typical errors describe situations where:</strong> [Detailed description of typical errors]</li>
            <li><strong>The issues are repeatedly tied to:</strong> [Common causes or patterns]</li>
            <li><strong>Hsdes link:</strong> Please list each link completely with a description {group[8]}, e.g., "HSDES Link for PCIe Issue"</li>
            <li><strong>Axon Link:</strong> Please list each link completely with a description {group[9]}, e.g., "Axon Link for PCIe Issue"</li>
            <li><strong>Group Details:</strong> [Highlight different Group]</li>
        </ul>
    </div>
    Here is the data for the current cluster:
    {output}
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
        # Extract Failure Type and Cluster from the summary
        failure_type = re.search(r'Failure Type (\d+)', summary).group(1)
        cluster = re.search(r'Cluster (\d+)', summary).group(1)
        key = (failure_type, cluster)
        if key not in consolidated:
            consolidated[key] = []
        consolidated[key].append(summary)
    
    # Combine summaries for each unique Failure Type and Cluster
    consolidated_summaries = []
    for key, summaries in consolidated.items():
        combined_summary = "\n".join(summaries)
        consolidated_summaries.append(combined_summary)
    
    return consolidated_summaries

def generate_html_table(summaries):
    html = """
    <html>
    <body>
        <h2>Summary of Failure Details</h2>
        <table border="1" style="width:100%; border-collapse: collapse; text-align: left;">
            <tr>
                <th>Failure Type</th>
                <th>Cluster</th>
                <th>Error Descriptions</th>
                <th>Typical Errors</th>
                <th>Issues Tied To</th>
                <th>HSDES Links</th>
                <th>Axon Links</th>
                <th>Group Details</th>
            </tr>
    """
    for summary in summaries:
        # Extract data from summary using regex or HTML parsing
        failure_type = re.search(r'Failure Type (\d+)', summary).group(1)
        cluster = re.search(r'Cluster (\d+)', summary).group(1)
        error_descriptions = re.search(r'<li><strong>Sentences in this cluster primarily involve errors regarding:</strong> (.*?)</li>', summary).group(1)
        typical_errors = re.search(r'<li><strong>Typical errors describe situations where:</strong> (.*?)</li>', summary).group(1)
        issues_tied_to = re.search(r'<li><strong>The issues are repeatedly tied to:</strong> (.*?)</li>', summary).group(1)
        
        # Extract multiple links
        hsdes_links = re.findall(r'<li><strong>Hsdes link:</strong> <a href="(.*?)">', summary)
        axon_links = re.findall(r'<li><strong>Axon Link:</strong> <a href="(.*?)">', summary)
        
        # Format links as a list
        hsdes_links_formatted = ', '.join([f'<a href="{link}">HSDES Link</a>' for link in hsdes_links])
        axon_links_formatted = ', '.join([f'<a href="{link}">Axon Link</a>' for link in axon_links])
        
        group_details = re.search(r'<li><strong>Group Details:</strong> (.*?)</li>', summary).group(1)

        html += f"""
            <tr>
                <td>{failure_type}</td>
                <td>{cluster}</td>
                <td>{error_descriptions}</td>
                <td>{typical_errors}</td>
                <td>{issues_tied_to}</td>
                <td>{hsdes_links_formatted}</td>
                <td>{axon_links_formatted}</td>
                <td>{group_details}</td>
            </tr>
        """
    html += """
        </table>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    now = datetime.now()
    Date = now.strftime("%Y-%m-%d")
    failures_df = pd.read_csv("Updated_failures_GNR_Daily.csv")
    failures_df = failures_df.loc[:, ~failures_df.columns.str.contains('^Unnamed')]
    hang_error_df = pd.read_csv("Hang_Error_Clustering_ and Similarity.csv")
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
            entry_summary = process_cluster(entry, connector)
            final_summary_list.append(entry_summary)
    
    # Consolidate summaries
    consolidated_summaries = consolidate_summaries(final_summary_list)
    final_summary_df = pd.DataFrame(consolidated_summaries, columns=['Summary'])

    # Generate HTML table
    html_table = generate_html_table(consolidated_summaries)

    email_addresses = input("Please provide one or more comma-separated email recipients: ")
    bar_chart_base64 = image_to_base64('bar_chart.png')
    subject_text = f"AI generated Failure summary with auto Triage - GNR-D {Date}"
    body_text = f"""
    <html>
    <body>
        <p>Dear Reader,</p>
        <p>We are pleased to share the AI-generated summary of the failure details from the GNR-D project. Please find the detailed analysis below:</p>
        <h2>Visualizations</h2>
        <h3>Number of Errors in Each Group</h3>
        <img src="data:image/png;base64,{bar_chart_base64}" alt="Bar Chart">
        {html_table}
        <ul>
            {''.join(f'<li>{summary}</li>' for summary in final_summary_df['Summary'])}
        </ul>
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
