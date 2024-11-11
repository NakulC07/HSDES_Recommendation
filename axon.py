import pyaxon
import svtools.report
import json
import pandas as pd
df = pd.read_excel("C:/NLP_Project_1/Failures.xlsx" , engine = 'openpyxl')
code = []
hyperlinks = df['Debug Snapshot']
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
def get_status_scope_summary(vallog):
    summaries = []
    bios_report = "intel-platformconfig-report-v1"
    content_report = "intel-content-report-v1"
    status_scope_report = "intel-svtools-report-v1"
    status_scope_summary_domain = [f"analyzers.sys_cfg" , f"analyzers.auto" , f"analyzers.ubox" , f"analyzers.ras" , f"analyzers.oobmsm" , f"analyzers.ieh" , f"analyzers.mcchnl"]
    svos_domain = f"sys.software.os.svos"
    bios_domain = f"sys.firmware.bios.system.frontpage"
    bios_summary_domain = f"knobs"
    attribute = f"summary"
    attribute_2 = f"insights"
    for domain in status_scope_summary_domain:
        try:
            summaries.append(get_summary(vallog,status_scope_report,domain,attribute_2))
        except:
            continue
    return summaries

def get_summary(uuid,report,domain,attribute):
    axon = pyaxon.axon.Axon(f"https://axon.intel.com")
    payload = axon.failure.content.object.get(uuid, report)
    svtools_report_dict = json.loads(payload.decode())
    svreport = svtools.report.Report.from_dict(svtools_report_dict)
    
    
    insights = getattr(eval(f"svreport.{domain}"), "insights")
    #print(insights)
    messages = []
    if isinstance(insights, list):
        for insight in insights:
            if isinstance(insight, svtools.report._rust.insight.HW_CFG_ERR):
                messages.append(insight.message)
            if isinstance(insight, svtools.report._rust.insight.HW_ERR):
                messages.append(insight.message)
            if isinstance(insight, svtools.report._rust.insight.HW_MCE_IIO):
                messages.append(insight.message)
            if isinstance(insight, svtools.report._rust.insight.HW_MCE_IMC):
                messages.append(insight.message)
            if isinstance(insight, svtools.report._rust.insight.HW_CORR):
                messages.append(insight.message)
            if isinstance(insight, svtools.report._rust.insight.HW_KNOWN_ISSUE):
                messages.append(insight.message)
            if isinstance(insight, svtools.report._rust.insight.SW_FW):
                messages.append(insight.message)
    else:
        if isinstance(insight, svtools.report._rust.insight.HW_CFG_ERR):
            messages.append(insight.message)
        if isinstance(insight, svtools.report._rust.insight.HW_ERR):
            messages.append(insight.message)
        if isinstance(insight, svtools.report._rust.insight.HW_MCE_IIO):
            messages.append(insight.message)
        if isinstance(insight, svtools.report._rust.insight.HW_MCE_IMC):
            messages.append(insight.message)
        if isinstance(insight, svtools.report._rust.insight.HW_CORR):
            messages.append(insight.message)
        if isinstance(insight, svtools.report._rust.insight.HW_KNOWN_ISSUE):
            messages.append(insight.message)
        if isinstance(insight, svtools.report._rust.insight.SW_FW):
                messages.append(insight.message)
    return messages

#print(get_status_scope_summary('1760324d-a6d4-bd3d-6fd2-e2e9b3bc5a3c'))
messages = []
count = 0
for value in code:
    count+=1
    print(f"Count-{count}: {value}")
    messages.append(get_status_scope_summary(value))
df = pd.DataFrame(messages)
df.to_csv("C:/NLP_Project_1/messages.csv" , index = False)
print("Conversion done!!")