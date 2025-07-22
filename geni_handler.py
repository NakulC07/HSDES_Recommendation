import os
from geni_connector import GeniConnector

class GeniHandler:
    def __init__(self, focus_id="6"):
        """
        Initialize Geni Handler with a specific focus ID
        
        Args:
            focus_id (str): Focus ID for Geni API (6 for general, 9 for HSD tasks)
        """
        self.focus_id = focus_id
        self.geni_connector = GeniConnector(focus_id=focus_id)
    
    def send_query(self, query, context=None):
        """
        Send a query to Geni API
        
        Args:
            query (str): The query/prompt to send
            context (str): Optional context information
            
        Returns:
            str: Response from Geni API
        """
        if context:
            formatted_query = f"Context: {context}\n\nQuery: {query}"
        else:
            formatted_query = query
            
        messages = [{"role": "user", "content": formatted_query}]
        result = self.geni_connector.run_prompt(messages)
        return result.get("response", "No response received")