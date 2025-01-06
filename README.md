# Automating Failure Management using GenAI

## Description
In this project we are using Generative AI to streamline and automate the recommendation system for failure management. Failures from NGA is the main data which is worked upon and using the advanced ML algorithms along with GenAI techniques users are recommended of types of failures on a daily basis which help them analyse easily.

## Installation
The requirements.txt contains all the necessary libraries used. Along with that developers need proper API keys to access NGA, HSD, and openAI using APIs.
### Prerequisites
- python3
- all packages mentioned in requirement.txt
- API keys

### Workflow
The entire work-flow is divided into 2 parts:
1. Creating a database of errors, signatures, hsdes links, axon links.
  1.1. The NGA_Extraction.py is used to extract NGA details for a span of > 30 days.
   1.2. The Extraction_Data.py is used to extract error details from the failures in the first code.
   1.3. This detail are used to perform clustering, sentence similarity, output of which are then collaborated. This detail is our database.
   1.4. The HSDES_Extraction.py is used to analyse the HSD details attached to the failures and give a report for the users.
   1.5. The Output_Visualization.py is used to visualise the number of failures in each category in the database.
The above is triggered once a month to update the database with new failures, its types, and also changes visible in visualization.
2. Collecting failures on daily basis analyse them and map it with database to recommend exisiting solutions if exists to the users.
   2.1. Codes mentioned in 1.1, 1.2 is ran on daily basis with small change.
   2.2 Error_Lookup_genai.py is used to analyse failures on daily basis and email the users about the cluster to which the failures belong and if there exists any solution in HSDES tickets. 
