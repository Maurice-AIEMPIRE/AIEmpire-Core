# 01 N8N BASICS MASTERCLASS.MD

# Master Class in Automation Tools with N8N

## Introduction to N8N Basics for Cashflow Optimization
Welcome to the **01 n8n basics masterclass**, a high-value module designed specifically for those looking to automate and optimize their cashflows using Node-RED. In this class, we'll cover everything you need from setting up your environment right through building complex automated workflows.

### Course Objectives:
1. Understand what N8N is.
2. Set up an initial n8n workspace setup on a cloud service or locally.
3. Learn to create basic nodes and understand the Node-RED flow concepts within n8n's framework.
4. Build simple automation tasks that can improve cashflow.

Let's dive straight into getting you started!

---

### Step 1: Setting Up Your N8N Environment
Before we start building any flows, you'll need an active instance of [n8n](https://n8n.io/).

#### Cloud Setup:
1. **Sign up for n8t.io**
   - Go to https://n8t.io and click "Get started".
2. Choose a subscription plan.
3. Log in using your preferred method (GitHub/GitLab/Spring Framework authentication).
4. Create an account with 'Automated Cashflow' as the organization name.

#### Local Setup:
1. Install Node.js on your machine ([https://nodejs.org/](https://nodejs.org)).
2. Open a terminal and run:

```bash
npx n8n start
```

3. Access [http://localhost:5678/n8n](http://localhost:5678/n8n) in your browser.

---

### Step 2: Familiarizing with N8N Interface

Upon login, you'll see the dashboard:
1. **Project Management** - Create new projects.
   ```markdown
   Click on 'New Project'
   ```
   
2. **Nodes Panel (Left)** - Drag and drop nodes here to start building your flow.

3. **Connections (Right)** panel where you can link up different components of a node for more complex operations or data transformations.

---

### Step 3: Building Your First Automation Task

#### Goal:
Automate the process that checks if an expense was correctly categorized in QuickBooks, and auto-corrects it into proper categories to optimize your cashflow categorization over time.

1. **Create New Node** - Drag a 'QuickBooks' node onto the canvas.
2. Set up connection parameters for authentication:

```json
{
  "clientId": "<your_client_id>",
  "secretKey": "<your_secret_key>"
}
```

3. Connect this to an input operation (e.g., `HTTP Request` if fetching from a web service) and another QuickBooks node as the output.

---

### Step 4: Processing Data in Nodes

Add intermediary nodes for processing your data:
1. **Function Node** - To manipulate strings or JSON objects:

```json
{
    "type": "n8n-function",
    "name": "",
    {
        "functions":[
            {

                name:"Correct Category"

                parameters:{
                    values: "$[\"QuickBooks\"]"
                }
                code:true

                returnType:String

                body:function (input) {

                    input["categories"] = ["new_category"]

                    return { flowProperties: input, properties: {} };
                    
                }        
            }
        ]
    }

}
```

2. Connect this to your QuickBooks node.

---

### Step 5: Testing and Debugging Your Flows

Always test before deploying:
1. **Test Mode** - Toggle on Test mode from the n8n dashboard.
2. Run nodes individually by clicking them, or start an automated run using a 'Trigger Node'.

---

By following this masterclass in N8N basics with action-oriented instructions and hands-on snippets of code, you'll be well-equipped to automate your cashflow processes efficiently.

Happy Automating! 🚀

---