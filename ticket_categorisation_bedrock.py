import json
import boto3
import configparser
from jira import JIRA
from datetime import datetime

# UPDATED: Using the region where your test script worked
bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='eu-west-1')

def get_bedrock_categorization(prompt):
    """
    Invokes AWS Bedrock using the Converse API (more robust than invoke_model).
    """
    # UPDATED: Using the model ID that worked in your test script
    model_id = "mistral.mixtral-8x7b-instruct-v0:1"
    
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    try:
        # UPDATED: Using the .converse() method as per your working script
        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.1 # Low temperature for consistent JSON categorization
            }
        )
        
        # Extract the text from the response structure
        return response['output']['message']['content'][0]['text']
        
    except Exception as e:
        print(f"Error calling Bedrock: {e}")
        return None

# ... [Keep determine_jira_setting_category and the rest of the script as is] ...

def determine_jira_setting_category(issue, jira_client):
    # 1. Try to find the Parent (the Epic)
    # Modern Jira uses 'parent'; older versions/APIs might use 'customfield_10014'
    parent_id = None
    if hasattr(issue.fields, 'parent'):
        parent_id = issue.fields.parent.key
    elif hasattr(issue.fields, 'customfield_10014'): # Common 'Epic Link' ID
        parent_id = getattr(issue.fields, 'customfield_10014')

    if parent_id:
        try:
            # We need to fetch the actual Epic issue to see ITS custom fields
            epic = jira_client.issue(parent_id)

            # 1. Get the field object
            category_obj = getattr(epic.fields, 'customfield_10188', None)

            # 2. Extract the string value if the object exists
            # We use getattr(category_obj, 'value', None) to avoid errors if the field is empty
            investment_category = getattr(category_obj, 'value', None) if category_obj else None


            mapping = {
                "New Capability": "New Capabilities",
                "Quality Improvement": "Quality Improvements",
                "Engineering Productivity": "Engineering Productivity",
                "Routine Operational Procedure": "Regular/routine operational procedures",
                "Maintenance": "Maintenance"
            }
            
            if investment_category in mapping:
                return mapping[investment_category]
        except Exception as e:
            print(f"Error fetching epic {parent_id}: {e}")

    # 2. Fallback to Issue Type Map if no Epic category was found
    it_map = {
        "Story": "New Capabilities",
        "Improvement": "Quality Improvements",
        "Productivity Task": "Engineering Productivity",
        "Bug": "Functional Bug Fixing",
        "Operational Task": "Regular/routine operational procedures",
        "Tech Support": "Regular/routine operational procedures",
        "Maintenance Task": "Maintenance",
        "Incident Action": "Incident Support"
    }
    return it_map.get(issue.fields.issuetype.name, "Uncategorized")

def main():
    config = configparser.ConfigParser()
    config.read("config.properties")
    
    jira_url = config.get("jira", "jira_url")
    jira_username = config.get("jira", "jira_username")
    jira_api_token = config.get("jira", "jira_api_token")
    start_date = config.get("dates", "start_date")
    end_date = config.get("dates", "end_date")
    project_keys = config.get("projects", "project_keys")

    jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))

    jql_query = f"project IN ({project_keys}) AND resolved >= '{start_date}' AND resolved <= '{end_date}' AND issuetype NOT IN subtaskIssueTypes()"
    print(f"Fetching tickets with JQL: {jql_query}")

    issues = jira.search_issues(jql_query, maxResults=100) 

   

    investment_definitions = """
    Investment Breakdown

Why?

We track where we invest our time and effort so that we can make more informed prioritisation decisions, address key issues and opportunities based on specific insights, and benchmark externally. We have been tracking our investment breakdown for some time, and have recently launched a new approach to categorisation so we can gain better insight.

What?

There are two types of investments, each with a clear purpose:
1) Elective Investments: Building new things or improving existing ones.
Defined as building new things or improving existing ones (CAPEX & OPEX)
    Sub-categories:

    a) New Capabilities (CAPEX)
    - Adding a new product
    - Adding a new feature or sub-feature
    - Supporting a new platform or partner application
    - New enabling capabilities towards target state architecture

    b) Quality Improvements (CAPEX & OPEX on a case by case basis)
    - Customer requested improvements
    - Better performance / utilisation
    - Iterations to improve adoption, retention, and quality
    - Improved product reliability or security

    c) Engineering Productivity (OPEX)
    - Better developer tooling
    - Testing automation and deployment
    - Code restructuring and optimisation
    - Work to reduce size of KTLO bucket in the future

2) KTLO: The minimum tasks required to maintain the current level of service in the eyes of our customers.
Defined as the minimum tasks required to maintain the current level of service in the eyes of our customers (OPEX)
    Sub-categories:

    a) Functional Bug Fixing (OPEX)
    - Addressing functional defects reported by customers (outside of testing cycles)

    b) Regular/routine operational procedures (OPEX)
    - Adding customers to the system through code changes
    - Amending parameters for pricing updates
    - Re-running failed workflows
    - Other engineering activities and changes to support operational procedures
    c) Maintenance (OPEX)
    - Maintaining current security posture
    - Maintaining current levels of service uptime
    - Staying up to date with external dependencies
    - Browsers, libraries, platforms, web services, partner changes, hardware, etc.
    d) Incident Support (OPEX)
    - Incident response and follow-up
    - Service and ticket monitoring & troubleshooting
    """

    # 1. Prepare the full list of ticket data
    all_tickets = []
    for issue in issues:
        all_tickets.append({
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": (issue.fields.description or "No description")[:500], # Truncate long descriptions
            "issue_type": issue.fields.issuetype.name,
            "current_jira_category": determine_jira_setting_category(issue, jira)
        })

    # 2. Split tickets into batches of 10
    batch_size = 10
    print(f"Processing {len(all_tickets)} tickets in batches of {batch_size}...")
    
    for i in range(0, len(all_tickets), batch_size):
        batch = all_tickets[i : i + batch_size]
        print(f"\n--- Processing Batch {i//batch_size + 1} ({batch[0]['key']} to {batch[-1]['key']}) ---")

        # Create a clear instruction for the structure
        structure_instruction = """
        Return ONLY a valid JSON array of objects. 
        CRITICAL: If you use double quotes inside the "reason" string, you MUST escape them with a backslash (e.g., \\"like this\\"). 
        Better yet, use single quotes inside the strings to avoid breaking the JSON.

        Each object must have:
        - "key": ticket key
        - "subCategory": sub-category name
        - "reason": short explanation justifying the chosen investment category
        """

        # Update the prompt string
        prompt = f"{investment_definitions}\n{structure_instruction}\n\nCategorize these tickets. Return ONLY a valid JSON array:\n{json.dumps(batch)}"
       
        ai_response_raw = get_bedrock_categorization(prompt)
        
        ai_results = []
        
        if ai_response_raw:
            try:

                # Find the start and end of the actual JSON array
                start_index = ai_response_raw.find("[")
                end_index = ai_response_raw.rfind("]")
                
                if start_index != -1 and end_index != -1:
                    cleaned_json = ai_response_raw[start_index:end_index+1]
                    
                    # This handles common LLM escaping mistakes
                    # It replaces problematic backslashes that aren't valid JSON escapes
                    cleaned_json = cleaned_json.replace('\\', '\\\\')
                    
                    ai_results = json.loads(cleaned_json)
                
                for res in ai_results:
                    key = res.get('key')
                    ai_cat = res.get('subCategory')
                    jira_cat = next((t['current_jira_category'] for t in batch if t['key'] == key), "Unknown")
                    status = "MATCH" if ai_cat == jira_cat else "MISMATCH"
                    if status == "MISMATCH":
                        print(f"[{status}] {key}: AI says '{ai_cat}', JIRA set to '{jira_cat}'")
                        print(f"   Reason: {res.get('reason')}")
            except Exception as e:
                print(f"Failed to parse AI response for this batch: {e}")


if __name__ == "__main__":
    main()