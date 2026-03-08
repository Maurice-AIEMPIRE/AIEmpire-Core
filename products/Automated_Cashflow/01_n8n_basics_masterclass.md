# 01 N8N BASICS MASTERCLASS.MD

# Automated Cashflow Mastery - Module 02: Advanced Automations with n8n

In this module of our comprehensive course on automated cash flow using n8n (Node Automation Network), we will take a deep dive into advanced automations. You’ll master complex workflows, learn to integrate multiple services seamlessly and ensure your finances run smoothly without manual intervention.

## Table of Contents
1. Setting Up Advanced Workflows with Multiple Nodes
2. Integrating External Services for Real-Time Data Syncing 
3. Error Handling & Retry Mechanisms in n8n Flows

---

### 1. Setting Up Advanced Workflows with Multiple Nodes

We'll start by creating advanced workflows that combine multiple nodes to handle intricate tasks.

#### Step-by-Step Guide:
- **Step A:** Start your existing workflow or create a new one.
    ```markdown
    Open the Workflow Designer in n8n and either open an ongoing project or click on "New Project" -> "Import Flow".
    ```

- **Step B:** Drag multiple nodes for complex processing. Example: Combining text parsing, date manipulation & HTTP requests.

```json
{
  "nodes": [
    {
      "parameters": {},
      "name": "",
      "type": ""
    }
  ],
  "connections": {}
}
```

#### Code Snippet:
- Create a combination of nodes for an automated expense tracker.
    
**Example:**
1. **HTTP Request Node (to fetch transaction data):**

```json
{
  "url":"https://api.example.com/transactions",
  "options":{"method":"GET"},
  "name": "Fetch Transactions"
}
```

2. **Function Item Node:** Parse the JSON response.

3. **Set node to filter transactions by date and amount:**
    ```markdown
    Set Filter:
      - Operation Type = AND
      - Condition1 (Field="date") [Date Range] -> >=2023-01-01, <=Current Date 
      - Condition2 (Field="amount") Value > 0.
    ```

4. **Combine multiple outputs for comprehensive data handling:**

---

### 2. Integrating External Services for Real-Time Data Syncing

Leverage real-time services to keep your cash flow insights up-to-date.

#### Steps:
- Connect n8n with financial databases, bank APIs or third-party platforms like PayPal.
  
**Example:** Fetch transactions from Bank API
```json
{
  "url":"https://bankapi.example.com/transactions",
  "options":{"method":"GET"},
  "name": "Fetch Transactions"
}
```

- Use **HTTP Request node with Authorization** to secure sensitive data:
    ```markdown
    - Set up OAuth2 Credentials for seamless integration.
        ```
      > Go to Bank API -> Security Settings -> Add New Client and copy the `Client ID` & `Secret Key`.
    ```

---

### 3. Error Handling & Retry Mechanisms in n8n Flows

Ensure your automated flows are resilient with robust error handling.

#### Steps:
- Configure **Error Trigger nodes**.
  
1. Set up a conditional retry mechanism for failed transactions:

```json
{
  "nodes": [
    {
      "parameters": {},
      "name":"Transaction",
      "type":"",
      "options":{
        "condition":[{"equals":{"$node[\"http_request\"][\"response_code\"]}":["200"]}]
      }
    },
    {
      "function":"retry",
      "parameters":{
        "maxRetries":10,
        "intervalTime":"00:01"
      }
    }
  ],
  "connections": {}
}
```

2. Log errors using **File node** for audit trails:

```markdown
- Add a File node to capture failed attempts.
    ```
      Name = Error Logs, Type="file", Path=/path/to/logs/failure_logs.txt 
    ```

---

Implement these advanced techniques in your automated cash flow workflows and you will gain unparalleled control over financial data automation. By mastering n8n's capabilities through this module of our Automated Cashflow course, you'll not only save time but also ensure precision.

Get ready to automate with confidence!