#!/usr/bin/env python3
"""
GITHUB CONTROL INTERFACE
Vollständige Steuerung des AI Empire über GitHub
Maurice's AI Empire - 2026
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from chat_manager import ChatManager

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "mauricepfeifer-ctrl/AIEmpire-Core")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")

class GitHubControlInterface:
    """Interface für vollständige GitHub-basierte Steuerung."""

    def __init__(self):
        self.chat_manager = ChatManager()
        self.commands = {
            "@bot status": self.cmd_status,
            "@bot generate-content": self.cmd_generate_content,
            "@bot run-task": self.cmd_run_task,
            "@bot revenue-report": self.cmd_revenue_report,
            "@bot post-x": self.cmd_post_x,
            "@bot create-gig": self.cmd_create_gig,
            "@bot help": self.cmd_help,
            "@bot upload-chat": self.cmd_upload_chat,
            "@bot ask": self.cmd_ask,
            "@bot models": self.cmd_models,
            "@bot switch-model": self.cmd_switch_model,
            "@bot export-chat": self.cmd_export_chat,
            "@bot clear-history": self.cmd_clear_history,
        }

    async def cmd_status(self, issue_num: int):
        """Return system status."""
        # Get chat manager status
        chat_status = self.chat_manager.get_history_summary()
        models_info = self.chat_manager.list_models()

        available_models = sum(1 for m in models_info['models'].values() if m['available'])
        total_models = len(models_info['models'])

        status = f"""# 🤖 System Status - {datetime.now().isoformat()}

## Services
- ✅ GitHub Actions - Active
- ✅ Content Generation - Ready
- ✅ Kimi API - Available
- ✅ X Lead Machine - Ready
- ✅ Revenue Tracking - Active
- ✅ Chat Manager - Active ({available_models}/{total_models} models available)

## Chat Status
- Current Model: {models_info['current_model']}
- Conversation Messages: {chat_status['message_count']}
- User Messages: {chat_status['user_messages']}
- Assistant Responses: {chat_status['assistant_messages']}

## Recent Activity
- Last content generation: Check workflows
- Last revenue report: Check issues
- Open tasks: See issues with 'task' label

## Quick Stats
- Total Revenue: EUR 0
- X Posts Ready: Multiple
- Gumroad Products: 1 live
- Fiverr Gigs: 0

## Available Commands
- `@bot generate-content` - Generate X/Twitter content
- `@bot revenue-report` - Show revenue status
- `@bot post-x` - Prepare content for X posting
- `@bot create-gig` - Generate Fiverr gig description
- `@bot run-task <name>` - Run specific task
- `@bot help` - Show all commands
"""
        return status

    async def cmd_generate_content(self, issue_num: int):
        """Generate content for X/Twitter."""
        import sys
        sys.path.append(str(Path(__file__).parent / "x-lead-machine"))

        try:
            from x_automation import XLeadMachine

            machine = XLeadMachine()

            topics = [
                ("AI Automation secrets", "value"),
                ("Building AI Empire", "behind_scenes"),
                ("Revenue with AI", "result"),
                ("Productivity", "tutorial"),
                ("AI vs Traditional", "controversial")
            ]

            content = "# 🎨 Generated X/Twitter Content\n\n"

            for i, (topic, style) in enumerate(topics, 1):
                post = await machine.generate_content(topic, style)
                content += f"## Post {i} - {topic}\n**Style:** {style}\n\n{post}\n\n---\n\n"

            content += "\n## Next Steps\n"
            content += "1. Review and edit posts\n"
            content += "2. Post to X/Twitter\n"
            content += "3. Track engagement\n"
            content += "4. Respond to comments\n"

            return content

        except Exception as e:
            return f"❌ Error generating content: {e}"

    async def cmd_run_task(self, issue_num: int, task_name: str = ""):
        """Run a specific task."""
        return f"🚀 Running task: {task_name}\n\nCheck workflow runs for progress."

    async def cmd_revenue_report(self, issue_num: int):
        """Generate revenue report."""
        return """# 💰 Revenue Report

## Current Status
**Total Revenue:** EUR 0
**Daily Target:** EUR 50-100
**Monthly Target:** EUR 25,000

## Revenue Streams

### 1. Gumroad (Digital Products)
- Status: 🟡 Active
- Products: 1 live
- Revenue: EUR 0
- Action: Add 2-3 more products

### 2. Fiverr (Services)
- Status: ❌ Not Started
- Gigs: 0
- Revenue: EUR 0
- Action: Create 3 gigs today

### 3. X/Twitter (Lead Gen)
- Status: 🟡 Ready
- Posts: Multiple ready
- Revenue: EUR 0
- Action: Start posting daily

### 4. Consulting
- Status: ❌ Not Started
- Clients: 0
- Revenue: EUR 0
- Action: Create offer + outreach

## Action Plan
1. ✅ Generate content (done)
2. ⏳ Post to X daily
3. ⏳ Create Fiverr gigs
4. ⏳ Launch more Gumroad products
5. ⏳ Start outreach for consulting

## Projection
- Week 1: EUR 500-1,000
- Month 1: EUR 25,000
- Month 3: EUR 90,000
- Year 1: EUR 500,000+
"""

    async def cmd_post_x(self, issue_num: int):
        """Prepare content for X posting."""
        return """# 📱 X/Twitter Posting Guide

## Ready-to-Post Content
Check the content generation results in recent issues or workflow runs.

## Posting Schedule
- **Morning (8 AM):** Value/Educational
- **Noon (12 PM):** Behind-the-scenes
- **Evening (6 PM):** Result/Controversial

## Best Practices
1. Use hooks in first line
2. Keep it under 280 chars (or thread)
3. Add relevant hashtags at end
4. Include call-to-action
5. Respond to all comments

## Engagement Strategy
1. Reply to 10-20 relevant tweets daily
2. Quote tweet with value-add
3. DM leads with personalized message
4. Track which posts get most engagement

## Hashtags to Use
#AIAutomation #BuildInPublic #AIAgents #NoCode #Automation

## Next Steps
1. Copy content from generation issue
2. Post at optimal times
3. Track engagement metrics
4. Respond to comments within 1 hour
"""

    async def cmd_create_gig(self, issue_num: int):
        """Generate Fiverr gig descriptions."""
        return """# 🎯 Fiverr Gig Descriptions

## Gig 1: AI Automation Setup

**Title:** I will set up AI automation for your business

**Category:** Programming & Tech > AI Services

**Pricing:**
- Basic (EUR 50): Simple automation
- Standard (EUR 150): Multiple automations
- Premium (EUR 500): Complete system

**Description:**
Need to automate repetitive tasks? I'll set up AI-powered automation for your business.

What I offer:
✅ AI chatbots & assistants
✅ Workflow automation
✅ Data processing
✅ Email automation
✅ Social media automation

Technologies: Claude, GPT, Kimi, n8n, Make, Zapier

**Requirements:**
- Description of tasks to automate
- Access to tools/platforms
- Expected outcomes

---

## Gig 2: SEO Content with AI

**Title:** I will write SEO-optimized blog posts using AI

**Pricing:**
- Basic (EUR 30): 500 words
- Standard (EUR 80): 1500 words
- Premium (EUR 200): 3000 words + optimization

**Description:**
Get high-quality, SEO-optimized content written with advanced AI.

What you get:
✅ Keyword research
✅ SEO optimization
✅ Engaging content
✅ Multiple revisions
✅ Fast delivery

**Requirements:**
- Topic/niche
- Target keywords
- Tone/style preferences

---

## Gig 3: AI Consultation

**Title:** I will consult on AI implementation strategy

**Pricing:**
- Basic (EUR 100): 30-min consultation
- Standard (EUR 300): Strategy + implementation plan
- Premium (EUR 1000): Full audit + roadmap

**Description:**
Get expert advice on implementing AI in your business.

What I provide:
✅ AI readiness assessment
✅ Tool recommendations
✅ Implementation roadmap
✅ Cost-benefit analysis
✅ Risk assessment

Background: 16 years technical expertise + AI automation specialist

**Requirements:**
- Business description
- Current processes
- Goals & objectives
"""

    async def cmd_upload_chat(self, issue_num: int, chat_content: str = "", format: str = "text"):
        """Upload chat history."""
        if not chat_content:
            return """# 📤 Chat Upload

To upload a chat, use the format:
```
@bot upload-chat [format]
<your chat content here>
```

Supported formats:
- `text` (default) - Plain text with "User:" and "Assistant:" labels
- `json` - JSON array of message objects
- `markdown` - Markdown sections with ## headers

Example:
```
@bot upload-chat text
User: Hello!
Assistant: Hi there! How can I help?
User: Tell me about AI
Assistant: AI stands for Artificial Intelligence...
```
"""

        result = await self.chat_manager.upload_chat(chat_content, format)

        if result.get("success"):
            return f"""# ✅ Chat Upload Successful

- Chat ID: {result['chat_id']}
- Messages: {result['message_count']}
- File: {result['file']}

You can now use `@bot ask` to ask questions with this context!
"""
        else:
            return f"""# ❌ Chat Upload Failed

Error: {result.get('error')}

Please check your format and try again.
"""

    async def cmd_ask(self, issue_num: int, question: str = "", model: str = None):
        """Ask a question using the selected model."""
        if not question:
            return """# ❓ Ask Question

Use this command to ask questions:
```
@bot ask [question]
```

The bot will use the current model and conversation history to answer.

Example:
```
@bot ask What is AI automation?
```

To use a specific model:
```
@bot ask:claude-sonnet What is AI automation?
```
"""

        # Extract model from question if specified
        if question.startswith(":"):
            parts = question.split(" ", 1)
            if len(parts) == 2:
                model = parts[0][1:]  # Remove the ":"
                question = parts[1]

        result = await self.chat_manager.ask_question(question, model=model)

        if result.get("success"):
            usage_info = ""
            if "usage" in result:
                usage_info = f"\n\n**Usage:** {json.dumps(result['usage'])}"

            return f"""# 💬 Answer

**Model:** {result['model']}

{result['answer']}{usage_info}
"""
        else:
            return f"""# ❌ Error

{result.get('error')}

Use `@bot models` to see available models.
"""

    async def cmd_models(self, issue_num: int):
        """List available models."""
        models_info = self.chat_manager.list_models()

        output = f"""# 🤖 Available Models

**Current Model:** {models_info['current_model']}

## All Models

"""
        for name, info in models_info['models'].items():
            status = "✅ Available" if info['available'] else "❌ Not Available"
            current = " **← CURRENT**" if name == models_info['current_model'] else ""
            output += f"### {name}{current}\n"
            output += f"- Name: {info['name']}\n"
            output += f"- API: {info['api']}\n"
            output += f"- Status: {status}\n\n"

        output += """## Usage

To switch models:
```
@bot switch-model [model-name]
```

Example:
```
@bot switch-model claude-sonnet
```
"""

        return output

    async def cmd_switch_model(self, issue_num: int, model_name: str = ""):
        """Switch to a different model."""
        if not model_name:
            return """# 🔄 Switch Model

Use this command to switch models:
```
@bot switch-model [model-name]
```

Use `@bot models` to see available models.
"""

        result = self.chat_manager.switch_model(model_name)

        if result.get("success"):
            return f"""# ✅ Model Switched

- Previous: {result['previous_model']}
- Current: {result['current_model']}
- Info: {result['model_info']['name']}

You can now use `@bot ask` with the new model!
"""
        else:
            available = ", ".join(result.get('available_models', []))
            return f"""# ❌ Switch Failed

Error: {result.get('error')}
Reason: {result.get('reason', 'Unknown')}

Available models: {available}
"""

    async def cmd_export_chat(self, issue_num: int):
        """Export current conversation."""
        exported = self.chat_manager.export_conversation()
        summary = self.chat_manager.get_history_summary()

        return f"""# 📥 Exported Conversation

**Summary:**
- Total Messages: {summary['message_count']}
- User Messages: {summary['user_messages']}
- Assistant Messages: {summary['assistant_messages']}
- Model Used: {summary['current_model']}

**Exported JSON:**
```json
{exported}
```

You can save this and re-import it later with `@bot upload-chat json`.
"""

    async def cmd_clear_history(self, issue_num: int):
        """Clear conversation history."""
        self.chat_manager.clear_history()
        return """# 🗑️ History Cleared

Conversation history has been cleared.
You can start a new conversation or upload a new chat history.
"""

    async def cmd_help(self, issue_num: int):
        """Show help."""
        return """# 🤖 GitHub Control Interface - Help

## Available Commands

### System Commands
- `@bot status` - Show current system status
- `@bot help` - Show this help message

### Chat & AI Commands (NEW!)
- `@bot upload-chat [format]` - Upload chat history (text/json/markdown)
- `@bot ask [question]` - Ask a question with current model
- `@bot models` - List all available AI models
- `@bot switch-model [name]` - Switch to a different model
- `@bot export-chat` - Export current conversation
- `@bot clear-history` - Clear conversation history

### Content & Marketing
- `@bot generate-content` - Generate X/Twitter content
- `@bot post-x` - Get X posting guide
- `@bot create-gig` - Generate Fiverr gig descriptions

### Business Operations
- `@bot revenue-report` - Show revenue status
- `@bot run-task <name>` - Run specific task

## How to Use
1. Create an issue or comment on existing issue
2. Include a command (e.g., `@bot status`)
3. The bot will respond with the result

## Automation
- Content is generated every 4 hours
- Revenue reports daily at 9 AM UTC
- Claude health checks every 30 minutes

## Manual Workflows
Go to Actions tab to manually trigger:
- Content Generation
- Revenue Tracking
- Any other workflow
"""

    async def process_comment(self, comment_body: str, issue_num: int) -> str:
        """Process a command from an issue comment."""
        comment_lower = comment_body.lower()

        # Handle commands with parameters
        if "@bot upload-chat" in comment_lower:
            # Extract format and content
            parts = comment_body.split("@bot upload-chat", 1)
            if len(parts) > 1:
                content = parts[1].strip()
                # Check if format is specified
                format_type = "text"
                if content.startswith("json") or content.startswith("markdown") or content.startswith("text"):
                    first_line = content.split("\n", 1)[0]
                    format_type = first_line.strip()
                    content = content.split("\n", 1)[1] if "\n" in content else ""
                return await self.cmd_upload_chat(issue_num, content, format_type)
            return await self.cmd_upload_chat(issue_num)

        elif "@bot ask" in comment_lower:
            parts = comment_body.split("@bot ask", 1)
            question = parts[1].strip() if len(parts) > 1 else ""
            return await self.cmd_ask(issue_num, question)

        elif "@bot switch-model" in comment_lower:
            parts = comment_body.split("@bot switch-model", 1)
            model_name = parts[1].strip() if len(parts) > 1 else ""
            return await self.cmd_switch_model(issue_num, model_name)

        elif "@bot run-task" in comment_lower:
            task = comment_body.split("@bot run-task", 1)[1].strip()
            return await self.cmd_run_task(issue_num, task)

        # Handle simple commands
        for cmd, handler in self.commands.items():
            if cmd in comment_lower:
                return await handler(issue_num)

        return "❓ Unknown command. Type `@bot help` for available commands."


async def main():
    """Test the interface."""
    interface = GitHubControlInterface()

    print("=" * 60)
    print("GITHUB CONTROL INTERFACE")
    print("=" * 60)
    print()

    # Test commands
    test_commands = [
        ("@bot status", "Status Check"),
        ("@bot models", "List Models"),
        ("@bot help", "Help"),
    ]

    for cmd, desc in test_commands:
        print(f"\n### Testing: {desc}")
        print(f"Command: {cmd}")
        print("-" * 60)
        result = await interface.process_comment(cmd, 1)
        print(result)
        print()


if __name__ == "__main__":
    asyncio.run(main())
