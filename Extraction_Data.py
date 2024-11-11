import pyaxon
import svtools.report
import json
import pandas as pd
import re
from pyaxon import Axon,ServerError
import requests

#Reading the source file extracted from NGA
df = pd.read_excel("./Failures_(1).xlsx" , engine = 'openpyxl')
print(df.head())
code = []
hyperlinks = df['Debug Snapshot']

#Converting debug snapshots from https:// .. format to a code format 
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

# Initialize the Axon client
api_token = "3ee33172-5a93-4a26-a761-28147bc2ef1d"
axon = pyaxon.axon.Axon("https://axon.intel.com" , token = api_token)


#Extracting hsdes summary
summary = []
def get_hsdes_summary(failure_id):
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


#Extracting Status Scope Summary
def get_status_scope_summary(vallog):
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
            summaries.append(get_summary(vallog,status_scope_report,domain,attribute_2))
        except:
            continue
    return summaries

def get_summary(uuid, report, domain, attribute):
    axon = pyaxon.axon.Axon("https://axon.intel.com")
    payload = axon.failure.content.object.get(uuid, report)
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

messages = []
count = 0
for value in code:
    count += 1
    if count == 5:
        break 
    print(f"Count-{count}: {value}")
    messages.append(get_status_scope_summary(value))
    summary.append(get_hsdes_summary(value))
    hsdes_summary  = {}

#From the extracted HSDES and AXON link converting into a proper format
hsdes_summary_list = []
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
        if pd.notnull(col) and col != '[]' and not re.search(r'Jumpers J5562 and J5563' , col) :
            merged_values.append(col)
    return ' '.join(merged_values)


# Original DataFrame merged with HSDES links and Errors
df_msgs = pd.DataFrame(messages)
df_msgs['Merged'] = df_msgs.iloc[:, 0:15].apply(merge_columns, axis=1)
df_msgs.drop(df_msgs.columns[0:15] , axis=1 , inplace=True)
df_hsdes = pd.DataFrame(hsdes_summary_list)
df_concat = pd.concat([df , df_msgs,df_hsdes] , axis = 1)
df_concat.to_csv("./Updated_failures.csv" , index=False)
print("Conversion done!!")