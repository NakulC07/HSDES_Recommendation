from openai import AzureOpenAI
import os
import httpx
from dotenv import load_dotenv


# Get token from environ if available (and not hardcoded above)

load_dotenv()

openai_key = os.getenv("OPENAI_KEY") 
DEFAULT_DEPLOYMENT_NAME = "gpt4"

# create an instance of the AzureOpenAI class
# Why pass both 'api_key' and default_headers={"Ocp-Apim-Subscription-Key"}?
#    Not sure. Passing only api_key seems to work
#    Passing only default_headers... (with a valid key) and api_key with any string also seems to work
#    We decided to keep both
client = AzureOpenAI(
    api_version = "2023-07-01-preview",
    api_key = openai_key,
    base_url = "https://laasapim01.laas.icloud.intel.com/azopenai",
    default_headers={"Ocp-Apim-Subscription-Key" :openai_key},
    http_client=httpx.Client(verify=False)
    )


# class to connect to OpenAI chatGPT deployment
class OpenAIConnector:

    # Initialize the OpenAI connector class
    def __init__(self, deployment_name = None):
        if deployment_name is None:
            deployment_name = DEFAULT_DEPLOYMENT_NAME
            print("INFO - %s: using default deployment: %s"%(__file__, deployment_name,))
        self.deployment_name = deployment_name
    
    # Run the prompt on the OpenAI model
    def run_prompt(self, prompt):
        '''
        See documentation at 
            https://platform.openai.com/docs/guides/text-generation/chat-completions-api
            https://platform.openai.com/docs/api-reference/chat/create
        '''

        completion = client.chat.completions.create(model=self.deployment_name,
            messages=prompt, max_tokens = 1000)

        # Uncomment these prints to show number of input/output tokens used and finish_reason
        # print(f"Prompt tokens: {completion.usage.prompt_tokens}")
        # print(f"Completion tokens: {completion.usage.completion_tokens}")
        # print(f"GPT finish reason: {completion.choices[0].finish_reason}")
    
        gpt_response = completion.choices[0].message.content

        return {
            "response" : gpt_response
        }

if __name__ == '__main__':
    import random
    num = random.randint(0, 100)
    
    # prompt to be sent to the OpenAI model
    # Select one from several examples
    if num < 90:
        system_msg = "You are a helpful assistant"
        prompt = "Say something short in 1 line"
    else:
        system_msg = "You are a friendly and helpful teaching assistant. You explain concepts in great depth using simple terms, and you give examples to help people learn. At the end of each explanation, you ask a question to check for understanding"
        prompt = "What is python programming?"
    
    print(f"\nRunning prompt:\n   system: {system_msg}\n    user: {prompt}\n\n")
    
    # messages to be sent to the OpenAI model
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": prompt}
    ]
    
    # create an instance of the OpenAIConnector class
    print("Starting openAI connection")
    connector = OpenAIConnector()
    
    # run the prompt on the OpenAI model
    print("Running query:\n%s"%(messages,))
    res = connector.run_prompt(messages)
    
    print(f"The response: {res['response']}")