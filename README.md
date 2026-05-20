========================================================================
Jira Ticket Categorization via AWS Bedrock
========================================================================

Overview
--------
This project automates the classification of resolved Jira tickets into specific
Investment Breakdown categories (Elective Investments vs. Keep the Lights On [KTLO])
using AWS Bedrock's Mistral Mixtral LLM. 

It fetches issues from a targeted Jira project within a specific date window, 
evaluates the current category assigned via Epic Link or fallback Issue Type mapping, 
and leverages Amazon Bedrock to batch-categorize the issues using the Converse API.
The script finally cross-references the AI's classification against the Jira-assigned
category and highlights matches or mismatches with explanations.

Project Structure
-----------------
- ticket_categorisation_bedrock.py  : Main Python script containing Jira fetch, 
                                      Bedrock client initialization, batching, 
                                      and classification logic.
- config.properties                : Configuration file containing authentication 
                                      credentials, Jira parameters, and date thresholds.
- requirements.txt                 : Python dependencies required to run the script.

Prerequisites
-------------
1. Python 3.7+
2. AWS Credentials configured on your local machine or execution environment 
   with permissions to invoke AWS Bedrock in the target region (`eu-west-1`).

Installation & Setup
--------------------
1. Install the required Python packages:
   $ pip install -r requirements.txt

2. Update the `config.properties` file with your specific execution parameters:
   - Ensure the `jira_url`, `jira_username`, and `jira_api_token` are correct.
   - Set the `start_date` and `end_date` to define the ticket resolution window.
   - Define the project keys (e.g., `project_keys = STCP`).

Configuration Parameters
------------------------
The application reads from `config.properties` under three main sections:
- [jira]: Contains connection strings and API tokens for Jira authentication.
- [dates]: Specifies the target scope for resolved tickets (`YYYY-MM-DD`).
- [projects]: Specifies the JQL target project keys.

How It Works
------------
1. Jira Fetching: The script builds a JQL query matching the project keys and 
   resolution date range (filtering out subtasks).
2. Category Resolution:
   - Looks for an Epic Parent (`parent` or `customfield_10014`) to find the 
     Jira-defined field `customfield_10188` (Investment Category).
   - Falls back to an issue-type mapping array if no Epic context is found.
3. Bedrock Processing: Tickets are batched into groups of 10 to fit context sizes 
   and maximize efficiency. The script asks the `mistral.mixtral-8x7b-instruct-v0:1` 
   model via the Converse API to format structural JSON responses.
4. Reconciliation: The console outputs instances where the LLM's structural assessment 
   diverges from Jira's fallback configurations ("MISMATCH"), providing a concise 
   reasoning output.

Running the Application
-----------------------
You must first login to the Data Production Dev account (145953991976) using the terminal following instructions here:
https://fundingcircle.atlassian.net/wiki/spaces/AIML/pages/696352803/Getting+Started+With+AWS+Bedrock

Then execute the script from your terminal:
$ python ticket_categorisation_bedrock.py

Disclaimer / Security Note
---------------------------
Never commit plaintext Jira API tokens (`jira_api_token`) or credentials directly to 
version control repositories. Ensure `config.properties` is listed in your `.gitignore`.
========================================================================



