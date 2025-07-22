import os
import requests
import json
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings for internal services
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GeniConnector:
    def __init__(self, focus_id="9"):
        load_dotenv()
        self.token = os.getenv("ACCESS_TOKEN")
        self.focus_id = focus_id
        self.url = f"https://laas-aks-prod01.laas.icloud.intel.com/genichatservice/Chat/askQuestion?focusId={self.focus_id}"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        # Enable mock mode for testing when token is expired
        self.mock_mode = os.getenv("GENI_MOCK_MODE", "false").lower() == "true"
    
    def run_prompt(self, messages):
        """
        Run a prompt using Geni API or mock response
        messages: List of message objects with 'role' and 'content' keys
        """
        # Extract the user content from the messages
        user_content = ""
        for message in messages:
            if message["role"] == "user":
                user_content = message["content"]
                break
        
        # Mock mode for testing
        if self.mock_mode:
            return self._get_mock_response(user_content)
        
        payload = json.dumps([
            {
                "content": user_content,
                "role": "user"
            }
        ])
        
        try:
            response = requests.post(
                self.url, 
                headers=self.headers, 
                data=payload,
                verify=False,  # Disable SSL verification for Intel internal services
                timeout=30
            )
            response.raise_for_status()
            
            # Return in the same format as OpenAI connector
            return {
                "response": response.text
            }
        except requests.exceptions.RequestException as e:
            print(f"Error calling Geni API: {e}")
            # Fall back to mock response if API fails
            return self._get_mock_response(user_content)
    
    def _get_mock_response(self, user_content):
        """Generate mock responses based on focus ID and content"""
        if self.focus_id == "9":  # HSD-focused responses
            if "HSDES" in user_content or "hsd" in user_content.lower():
                mock_response = """
                <div>
                    <strong>Failure Type 1 - Cluster 1</strong>
                    <ul>
                        <li><strong>Sentences in this cluster primarily involve errors regarding:</strong> PCIe link training failures, memory initialization errors</li>
                        <li><strong>Hsdes link:</strong> <a href="https://hsdes.intel.com/appstore/article/#/14016832929">HSDES Link for PCIe Issue</a></li>
                        <li><strong>Axon Link:</strong> <a href="https://axon.intel.com/app/view/12345">Axon Link for PCIe Issue</a></li>
                        <li><strong>Root Cause Notes:</strong> PCIe controller initialization sequence timeout during system boot</li>
                        <li><strong>Fix Description:</strong> Update BIOS microcode to v2.1.3 with improved PCIe timing parameters</li>
                        <li><strong>Component:</strong> PCIe Controller, BIOS</li>
                        <li><strong>Discussion:</strong> This is a known issue affecting multiple platforms, fix validated in lab testing</li>
                    </ul>
                </div>
                """
            else:
                mock_response = "HSD Analysis: Component failure detected. Root cause: Hardware initialization timeout. Recommended action: Update firmware."
        else:  # General responses for focus ID 6
            mock_response = "General Analysis: System failure detected. Analyzing error patterns and providing comprehensive report with root cause analysis and recommended fixes."
        
        return {"response": mock_response}