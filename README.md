# Automating Failure Management using GenAI

## Description
In this project we are using Generative AI to streamline and automate the recommendation system for failure management. Failures from NGA is the main data which is worked upon and using the advanced ML algorithms along with GenAI techniques users are recommended of types of failures on a daily basis which help them analyse easily.

## Installation
The requirements.txt contains all the necessary libraries used. Along with that developers need proper API keys to access NGA, HSD, and openAI using APIs.
### Prerequisites
- python3
- all packages mentioned in requirement.txt
- API keys

## Workflow

The entire workflow is divided into two parts:

### 1. Creating a Database of Errors, Signatures, HSDES Links, and Axon Links

1.1. NGA_Extraction.py: This script is used to extract NGA details for a span of more than 30 days.

1.2. Extraction_Data.py: This script extracts error details from the failures identified in the first script.

1.3. Data Clustering and Similarity Analysis: The extracted details are used to perform clustering and sentence similarity analysis. The output of these analyses is then consolidated to form our database.

1.4. HSDES_Extraction.py: This script analyzes the HSD details attached to the failures and generates a report for the users.

1.5. Output_Visualization.py: This script visualizes the number of failures in each category within the database.

The above steps are triggered once a month to update the database with new failures, their types, and any changes visible in the visualization.

### 2. Collecting and Analyzing Failures on a Daily Basis

2.1. Daily Execution of Scripts: The scripts mentioned in steps 1.1 and 1.2 are run on a daily basis with minor modifications.

2.2. Error_Lookup_genai.py: This script analyzes daily failures and emails users about the cluster to which the failures belong. It also checks if there are any existing solutions in the HSDES tickets.

By following this workflow, the system ensures that the database is regularly updated and that users are promptly informed about new failures and potential solutions.
