import os
import json
import pandas as pd
import re
import pyaxon
import svtools.report
from pyaxon import Axon, ServerError
from dotenv import load_dotenv

class HSDES_Extraction:
    def hyperlink(self, hyperlinks):
        # Converting debug snapshots from https:// .. format to a code format
        code = []
        for hyperlink in hyperlinks:
            if type(hyperlink) == float:
                continue
            x = hyperlink.split('/')
            if x[0] != 'https:':
                code.append(x[0])
                continue
            y = x[4].split('?')
            z = y[1].split('=')
            code.append(z[1])
        return code

    def get_hsdes_summary(self, failure_id, axon):
        hsdes_links = []
        try:
            failure_details = axon.failure.get(failure_id)
            tickets = failure_details['tickets']
            hsdes = tickets['hsdes']
            for hsd in hsdes:
                try:
                    if hsd['type'] == 'sighting':
                        link = f"https://axon.intel.com/app/view/{failure_id}"
                        hsd['axon_link'] = link
                        hsdes_links.append(hsd)
                except:
                    continue
            return hsdes_links
        except ServerError as e:
            print(f"Error: {e.reason}")
            print(f"Details: {e.details}")
        except KeyError as e:
            pass

    def get_status_scope_summary(self, vallog, axon):
        summaries = []
        status_scope_report = "intel-svtools-report-v1"
        status_scope_summary_domain = [
            f"analyzers.b2upi", f"analyzers.upi", f"analyzers.pm", f"analyzers.cha",
            f"analyzers.b2cxl", f"analyzers.cxl", f"analyzers.b2cmi", f"analyzers.sys_cfg",
            f"analyzers.hiop", f"analyzers.auto", f"analyzers.ubox", f"analyzers.ras",
            f"analyzers.oobmsm", f"analyzers.ieh", f"analyzers.mcchnl"
        ]
        attribute_2 = f"insights_summary"
        try:
            summaries.append(self.get_summary(vallog, status_scope_report, "analyzers.ubox", attribute_2, axon))
        except:
            exit
        return summaries

    def get_summary(self, uuid, report, domain, attribute, axon):
        try:
            payload = axon.failure.content.object.get(uuid, report)
        except:
            payload = axon.failure.content.object.get(uuid, report)
        svtools_report_dict = json.loads(payload.decode())
        svreport = svtools.report.Report.from_dict(svtools_report_dict)
        insights = getattr(eval(f"svreport.{domain}"), "insights")
        messages = []
        if isinstance(insights, list):
            for insight in insights:
                if re.match(r"HW_", insight.__class__.__name__) or re.match(r"SW_", insight.__class__.__name__):
                    messages.append(insight.message)
        else:
            if re.match(r"HW_", insights.__class__.__name__) or re.match(r"SW_", insights.__class__.__name__):
                messages.append(insights.message)
        return messages

def process_project(project_name, input_file, output_dir):
    load_dotenv()
    df = pd.read_csv(input_file)
    hsd = HSDES_Extraction()
    hyperlinks = df['Debug Snapshot']
    code = hsd.hyperlink(hyperlinks)

    api_token = os.getenv("AXON_API_TOKEN")
    axon = pyaxon.axon.Axon("https://axon.intel.com", token=api_token)

    summary = []
    messages = []
    for value in code:
        messages.append(hsd.get_status_scope_summary(value, axon))
        summary.append(hsd.get_hsdes_summary(value, axon))

    hsdes_summary_list = []
    for val in summary:
        if val:
            dic = val[0]
            hsdes_summary = {
                'hsdes_link': dic['link'],
                'axon_link': dic['axon_link']
            }
            hsdes_summary_list.append(hsdes_summary)
        else:
            hsdes_summary = {
                'hsdes_link': None,
                'axon_link': None
            }
            hsdes_summary_list.append(hsdes_summary)

    def merge_columns(row):
        merged_values = []
        for col in row:
            col = str(col)
            if pd.notnull(col) and col != '[]' and not re.search(r'Jumpers J5562 and J5563', col) and not re.search(r'BIOS Post Code', col):
                merged_values.append(col)
        return ' '.join(merged_values)

    df_msgs = pd.DataFrame(messages)
    num_col = len(df_msgs.columns)
    df_msgs['Errors'] = df_msgs.iloc[:, 0:num_col].apply(merge_columns, axis=1)
    df_msgs.drop(df_msgs.columns[0:num_col], axis=1, inplace=True)
    df_hsdes = pd.DataFrame(hsdes_summary_list)
    filtered_df = df[df['Debug Snapshot'].notna()]
    df_concat = pd.concat([filtered_df.reset_index(drop=True), df_hsdes.reset_index(drop=True), df_msgs.reset_index(drop=True)], axis=1)

    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, f"Updated_failures_{project_name}.csv")
    df_concat.to_csv(output_file, index=False)
    print(f"Data for {project_name} saved to {output_file}")