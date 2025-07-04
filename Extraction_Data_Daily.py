import os
import json
import pandas as pd
import re
import pyaxon
import svtools.report
from pyaxon import ServerError
from dotenv import load_dotenv

class HSDES_Extraction:
    def hyperlink(self, hyperlinks):
        # Converting debug snapshots from https:// .. format to a code format
        code = []
        for hyperlink in hyperlinks:
            if isinstance(hyperlink, float):
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
                except Exception:
                    continue
            return hsdes_links
        except ServerError as e:
            print(f"Error: {e.reason}")
            print(f"Details: {e.details}")
        except KeyError:
            pass

    def get_status_scope_summary(self, vallog, axon):
        summaries = []
        status_scope_report = "intel-svtools-report-v1"
        
        # Get all possible insights from the SVReport
        try:
            payload = axon.failure.content.object.get(vallog, status_scope_report)
            svtools_report_dict = json.loads(payload.decode())
            svreport = svtools.report.Report.from_dict(svtools_report_dict)
            
            # Extract all possible insights recursively
            extracted_insights = self.extract_all_insights(svreport)
            summaries.extend(extracted_insights)
            
        except Exception as e:
            print(f"Error extracting insights for {vallog}: {e}")
            
        return summaries

    def get_summary(self, uuid, report, domain, attribute, axon):
        """
        Enhanced method to extract summary with fallback to comprehensive extraction.
        Maintains backward compatibility while providing more robust extraction.
        """
        try:
            payload = axon.failure.content.object.get(uuid, report)
            svtools_report_dict = json.loads(payload.decode())
            svreport = svtools.report.Report.from_dict(svtools_report_dict)
            
            # Try the original domain-specific approach first
            try:
                domain_parts = domain.split('.')
                target_obj = svreport
                for part in domain_parts:
                    target_obj = getattr(target_obj, part)
                
                insights = getattr(target_obj, "insights")
                messages = self.extract_messages_from_insights(insights)
                if messages:
                    return messages
                    
            except (AttributeError, KeyError):
                # If domain-specific approach fails, use comprehensive extraction
                pass
            
            # Fallback to comprehensive extraction
            all_insights = self.extract_all_insights(svreport)
            return all_insights
            
        except Exception as e:
            print(f"Error in get_summary for {uuid}: {e}")
            return []

    def extract_all_insights(self, svreport):
        """
        Recursively extract all possible insights from an SVReport object.
        This method dynamically discovers all analyzer domains and extracts
        all available insights without relying on hardcoded domain names.
        """
        all_insights = []
        
        try:
            # Get all attributes of the svreport object
            for attr_name in dir(svreport):
                # Skip private attributes and methods
                if attr_name.startswith('_'):
                    continue
                    
                try:
                    attr_value = getattr(svreport, attr_name)
                    
                    # Check if this is an analyzers object
                    if hasattr(attr_value, '__dict__') and 'analyzers' in attr_name.lower():
                        # Extract insights from analyzers
                        analyzer_insights = self.extract_analyzer_insights(attr_value)
                        all_insights.extend(analyzer_insights)
                    
                    # Also check for direct analyzer attributes
                    elif hasattr(attr_value, 'insights') or hasattr(attr_value, '__dict__'):
                        insights = self.extract_insights_from_object(attr_value)
                        all_insights.extend(insights)
                        
                except Exception:
                    # Skip attributes that can't be accessed
                    continue
                    
        except Exception as e:
            print(f"Error in extract_all_insights: {e}")
            
        return all_insights
    
    def extract_analyzer_insights(self, analyzers_obj):
        """Extract insights from all analyzer objects."""
        insights = []
        
        try:
            # Get all analyzer attributes
            for analyzer_name in dir(analyzers_obj):
                if analyzer_name.startswith('_'):
                    continue
                    
                try:
                    analyzer = getattr(analyzers_obj, analyzer_name)
                    analyzer_insights = self.extract_insights_from_object(analyzer)
                    insights.extend(analyzer_insights)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error in extract_analyzer_insights: {e}")
            
        return insights
    
    def extract_insights_from_object(self, obj):
        """Extract insights from a single object."""
        insights = []
        
        try:
            # Check if object has insights attribute
            if hasattr(obj, 'insights'):
                insights_attr = getattr(obj, 'insights')
                messages = self.extract_messages_from_insights(insights_attr)
                insights.extend(messages)
            
            # Also check for other potential insight attributes
            for attr_name in dir(obj):
                if attr_name.startswith('_'):
                    continue
                    
                # Look for attributes that might contain insights
                if 'insight' in attr_name.lower() or 'message' in attr_name.lower() or 'summary' in attr_name.lower():
                    try:
                        attr_value = getattr(obj, attr_name)
                        if hasattr(attr_value, '__iter__') and not isinstance(attr_value, str):
                            # It's a collection of insights
                            messages = self.extract_messages_from_insights(attr_value)
                            insights.extend(messages)
                        elif hasattr(attr_value, 'message'):
                            # It's a single insight with message
                            insights.append(attr_value.message)
                        elif isinstance(attr_value, str) and attr_value.strip():
                            # It's a direct string message
                            insights.append(attr_value)
                    except Exception:
                        continue
                        
        except Exception:
            pass
            
        return insights
    
    def extract_messages_from_insights(self, insights_collection):
        """Extract messages from a collection of insights."""
        messages = []
        
        try:
            if isinstance(insights_collection, list):
                for insight in insights_collection:
                    message = self.extract_message_from_insight(insight)
                    if message:
                        messages.append(message)
            else:
                # Single insight
                message = self.extract_message_from_insight(insights_collection)
                if message:
                    messages.append(message)
                    
        except Exception:
            pass
            
        return messages
    
    def extract_message_from_insight(self, insight):
        """Extract message from a single insight object."""
        try:
            # Check for HW_ or SW_ class names (Intel specific)
            if hasattr(insight, '__class__') and insight.__class__.__name__:
                class_name = insight.__class__.__name__
                if re.match(r"HW_", class_name) or re.match(r"SW_", class_name):
                    if hasattr(insight, 'message'):
                        return insight.message
            
            # Check for message attribute directly
            if hasattr(insight, 'message'):
                return insight.message
                
            # Check for other potential message attributes
            for attr_name in ['description', 'summary', 'details', 'text', 'content']:
                if hasattr(insight, attr_name):
                    attr_value = getattr(insight, attr_name)
                    if isinstance(attr_value, str) and attr_value.strip():
                        return attr_value
                        
            # If it's a string itself
            if isinstance(insight, str) and insight.strip():
                return insight
                
        except Exception:
            pass
            
        return None

    def debug_svreport_structure(self, svreport, max_depth=3, current_depth=0):
        """
        Debug utility to inspect the structure of an SVReport object.
        This helps understand what attributes and data are available.
        """
        if current_depth >= max_depth:
            return
            
        print(f"{'  ' * current_depth}SVReport Structure (depth {current_depth}):")
        
        try:
            for attr_name in dir(svreport):
                if attr_name.startswith('_'):
                    continue
                    
                try:
                    attr_value = getattr(svreport, attr_name)
                    attr_type = type(attr_value).__name__
                    print(f"{'  ' * (current_depth + 1)}{attr_name}: {attr_type}")
                    
                    # If it's a complex object, recurse
                    if hasattr(attr_value, '__dict__') and current_depth < max_depth - 1:
                        self.debug_svreport_structure(attr_value, max_depth, current_depth + 1)
                        
                except Exception:
                    print(f"{'  ' * (current_depth + 1)}{attr_name}: <inaccessible>")
                    
        except Exception as e:
            print(f"{'  ' * current_depth}Error inspecting object: {e}")
    
    def debug_extraction_results(self, vallog, axon):
        """Debug utility to show what data is being extracted."""
        print(f"\n=== DEBUG: Extraction Results for {vallog} ===")
        
        try:
            status_scope_report = "intel-svtools-report-v1"
            payload = axon.failure.content.object.get(vallog, status_scope_report)
            svtools_report_dict = json.loads(payload.decode())
            svreport = svtools.report.Report.from_dict(svtools_report_dict)
            
            print("SVReport structure:")
            self.debug_svreport_structure(svreport)
            
            print("\nExtracted insights:")
            all_insights = self.extract_all_insights(svreport)
            for i, insight in enumerate(all_insights):
                print(f"  {i+1}. {insight}")
                
            print(f"\nTotal insights extracted: {len(all_insights)}")
            
        except Exception as e:
            print(f"Error in debug extraction: {e}")
        
        print("=== END DEBUG ===\n")

def process_project(project_name, input_file, output_dir, debug=False):
    load_dotenv()
    df = pd.read_csv(input_file)
    hsd = HSDES_Extraction()
    hyperlinks = df['Debug Snapshot']
    code = hsd.hyperlink(hyperlinks)

    api_token = os.getenv("AXON_API_TOKEN")
    axon = pyaxon.axon.Axon("https://axon.intel.com", token=api_token)

    summary = []
    messages = []
    for i, value in enumerate(code):
        print(f"Processing {i+1}/{len(code)}: {value}")
        
        # Optional debug output
        if debug:
            hsd.debug_extraction_results(value, axon)
            
        messages.append(hsd.get_status_scope_summary(value, axon))
        summary.append(hsd.get_hsdes_summary(value, axon))
        print(f"Summary Status {summary[-1]}")

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
        """Merge multiple columns into a single string, filtering out unwanted content."""
        merged_values = []
        for col in row:
            col = str(col)
            # Filter out empty values, empty lists, and specific unwanted content
            if (pd.notnull(col) and 
                col != '[]' and 
                col != 'nan' and
                col.strip() and
                not re.search(r'Jumpers J5562 and J5563', col) and 
                not re.search(r'BIOS Post Code', col)):
                merged_values.append(col)
        return ' '.join(merged_values)

    print("Processing extracted messages...")
    df_msgs = pd.DataFrame(messages)
    
    if not df_msgs.empty:
        num_col = len(df_msgs.columns)
        df_msgs['Errors'] = df_msgs.iloc[:, 0:num_col].apply(merge_columns, axis=1)
        df_msgs.drop(df_msgs.columns[0:num_col], axis=1, inplace=True)
    else:
        # Handle case where no messages were extracted
        df_msgs = pd.DataFrame({'Errors': [''] * len(code)})
    
    print("Processing HSDES summaries...")
    df_hsdes = pd.DataFrame(hsdes_summary_list)
    
    print("Combining data...")
    filtered_df = df[df['Debug Snapshot'].notna()]
    
    # Ensure all DataFrames have the same length
    min_length = min(len(filtered_df), len(df_hsdes), len(df_msgs))
    if min_length < len(filtered_df):
        print("Warning: Some rows may be missing data due to processing errors.")
        filtered_df = filtered_df.iloc[:min_length]
        df_hsdes = df_hsdes.iloc[:min_length]
        df_msgs = df_msgs.iloc[:min_length]
    
    df_concat = pd.concat([
        filtered_df.reset_index(drop=True), 
        df_hsdes.reset_index(drop=True), 
        df_msgs.reset_index(drop=True)
    ], axis=1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, f"Updated_failures_{project_name}_Daily.csv")
    df_concat.to_csv(output_file, index=False)
    print(f"Data for {project_name} saved to {output_file}")
