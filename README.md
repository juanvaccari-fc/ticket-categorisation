# Jira Ticket Categorization via AWS Bedrock

An automated pipeline that classifies resolved Jira tickets into specific **Investment Breakdown** categories (*Elective Investments* vs. *Keep the Lights On [KTLO]*) using AWS Bedrock's Mistral Mixtral LLM.

The script fetches issues within a target date range, evaluates their current categories via Epic Links or fallback Issue Type mapping, and uses the Bedrock Converse API to audit and reconcile classifications.

---

## 📂 Project Structure

* `ticket_categorisation_bedrock.py` — Core Python script handling the Jira extraction, Bedrock batching, and classification logic.
* `config.properties` — Configuration file managing API credentials, target Jira project keys, and date ranges.
* `requirements.txt` — Python dependency manifest.

---

## ⚙️ Prerequisites

* **Python 3.7+**
* **AWS CLI** configured on your local machine with permissions to invoke AWS Bedrock in the `eu-west-1` (Ireland) region.

---

## 🚀 Installation & Setup

1. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
