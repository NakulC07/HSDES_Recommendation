import pyaxon
import svtools.report
import json
import pandas as pd
import re
from pyaxon import Axon,ServerError
import requests
import os
from dotenv import load_dotenv


class HSDES_Extraction:
    def hyperlink(self, hyperlinks):
        #Converting debug snapshots from https:// .. format to a code format 
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
    
    #Extracting hsdes summary
    def get_hsdes_summary(self,failure_id):
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

    #Extracting Status Scope Summary
    def get_status_scope_summary(self,vallog):
        summaries = []
        content_report = "intel-content-report-v1"
        status_scope_report = "intel-svtools-report-v1"
        status_scope_summary_domain = [
            f"analyzers.b2upi", f"analyzers.upi", f"analyzers.pm", f"analyzers.cha",
            f"analyzers.b2cxl", f"analyzers.cxl", f"analyzers.b2cmi", f"analyzers.sys_cfg",
            f"analyzers.hiop", f"analyzers.auto", f"analyzers.ubox", f"analyzers.ras",
            f"analyzers.oobmsm", f"analyzers.ieh", f"analyzers.mcchnl"
        ]
        svos_domain = f"sys.software.os.svos"
        attribute_2 = f"insights_summary"
        for domain in status_scope_summary_domain:
            try:
                summaries.append(self.get_summary(vallog,status_scope_report,domain,attribute_2))
            except:
                continue
        return summaries

    def get_summary(self,uuid, report, domain, attribute):
        api_token = os.getenv("AXON_API_TOKEN")
        axon = pyaxon.axon.Axon("https://axon.intel.com" , token = api_token)
        api_test_token = os.getenv("AXON_TEST_API_TOKEN")
        axon_test = pyaxon.axon.Axon("https://axon-test.intel.com" , token = api_test_token)
    
        try:
            payload = axon.failure.content.object.get(uuid, report)
        except:
            payload = axon_test.failure.content.object.get(uuid, report)
        svtools_report_dict = json.loads(payload.decode())
        svreport = svtools.report.Report.from_dict(svtools_report_dict)
        
        #print(svtools_report_dict)
        insights = getattr(eval(f"svreport.{domain}"), "insights")
        #print(insights)
        messages = []
        
        
        if isinstance(insights, list):
            for insight in insights:
                if re.match(r"HW_", insight.__class__.__name__) or re.match(r"SW_", insight.__class__.__name__):
                    #print(insight)
                    messages.append(insight.message)
        else:
            if re.match(r"HW_", insights.__class__.__name__) or re.match(r"SW_", insight.__class__.__name__):
                #print(insight)
                messages.append(insights.message)

        
        return messages



if __name__ == "__main__":

    load_dotenv()

    #Reading the source file extracted from NGA

    df = pd.read_csv("./GNRD/NGA_Extracted_DB.csv")
    print(df.head())

    hsd = HSDES_Extraction()    
    hyperlinks = df['Debug Snapshot']
    code = hsd.hyperlink(hyperlinks)

    # Initialize the Axon client

    api_token = os.getenv("AXON_API_TOKEN")
    axon = pyaxon.axon.Axon("https://axon.intel.com" , token = api_token)
    
    summary = []
    messages = []
    count = 0

    for value in code:
        count += 1
        print(f"Count-{count}: {value}")
        messages.append(hsd.get_status_scope_summary(value))
        summary.append(hsd.get_hsdes_summary(value))

    #From the extracted HSDES and AXON link converting into a proper format
    hsdes_summary_list = []
    hsdes_summary  = {}
    for val in summary:
        if val:
            dic = val[0]
            hsdes_summary = {
                'hsdes_link' : dic['link'] , 
                'axon_link' : dic['axon_link']
            }
            hsdes_summary_list.append(hsdes_summary)
        else:
            hsdes_summary = {
                'hsdes_link' : None ,
                'axon_link' : None
            }
            hsdes_summary_list.append(hsdes_summary)
    print(hsdes_summary_list)


    #The errors collected are cleaned and merged into a single csv for each row
    def merge_columns(row):
        merged_values = []
        for col in row:
            col = str(col)
            if pd.notnull(col) and col != '[]' and not re.search(r'Jumpers J5562 and J5563' , col) and not re.search(r'BIOS Post Code' , col) :
                merged_values.append(col)
        return ' '.join(merged_values)


    # Original DataFrame merged with HSDES links and Errors
    df_msgs = pd.DataFrame(messages)
    num_col = len(df_msgs.columns)
    df_msgs['Errors'] = df_msgs.iloc[:, 0:num_col].apply(merge_columns, axis=1)
    df_msgs.drop(df_msgs.columns[0:num_col] , axis=1 , inplace=True)
    df_hsdes = pd.DataFrame(hsdes_summary_list)
    filtered_df = df[df['Debug Snapshot'].notna()]
    df_concat = pd.concat([filtered_df.reset_index(drop=True), df_hsdes.reset_index(drop=True), df_msgs.reset_index(drop=True)], axis=1)
    df_concat.to_csv("./GNRD/Updated_failures_GNRD.csv", index=False)
    print("Conversion done!!")