# AUTOMATIC TASK GENERATION SYSTEM

> Continuously generate work tasks to keep everyone busy for 12+ hours using open source tools

## 🎯 Overview

The Automatic Task Generation System creates diverse, actionable tasks across multiple categories to ensure continuous productivity for the AI Empire team.

## 🚀 Features

- **Automatic Generation**: Tasks are generated every 6 hours via GitHub Actions
- **Diverse Categories**: Content, Research, Code, Business, Optimization
- **High Quality**: Each task has clear objectives, prompts, and acceptance criteria
- **Open Source**: Uses Python, YAML, and open APIs (Kimi/Moonshot)
- **Scalable**: Can generate 25-100+ tasks on demand

## 📊 Task Categories

### Content Tasks (High ROI)
Create engaging content for social media, blogs, and marketing:
- X/Twitter posts and threads
- LinkedIn content calendars
- Blog articles
- Reddit posts
- Newsletter content

### Research Tasks (Intelligence Gathering)
Gather market intelligence and identify opportunities:
- Competitor analysis
- Lead generation
- Market research
- Keyword research
- Partnership opportunities

### Code/Technical Tasks
Build automation and tools:
- API integrations
- Automation scripts
- GitHub Actions workflows
- CLI tools
- Performance optimizations

### Business Tasks (Revenue Focus)
Create revenue-generating assets:
- Digital products (Gumroad)
- Service packages (Fiverr)
- Pricing strategies
- Outreach campaigns
- Consultation offers

### Optimization Tasks (Efficiency)
Improve systems and reduce costs:
- Workflow automation
- Cost reduction
- Performance improvements
- Process optimization

## 🛠️ Usage

### Automatic Generation (Recommended)

Tasks are automatically generated every 6 hours via GitHub Actions. No manual intervention required.

### Manual Generation

#### Via GitHub Actions
1. Go to **Actions** → **Auto Task Generation**
2. Click **Run workflow**
3. Specify number of tasks (default: 25)
4. Wait for PR with new tasks

#### Via Command Line
```bash
# Generate 25 tasks (default)
python3 task_generator.py

# Tasks will be saved to atomic-reactor/tasks/
```

#### Via GitHub Issues
Comment on any issue:
```
@bot generate-tasks
```

The bot will respond with instructions and status.

## 📁 Generated Files

Tasks are saved to `atomic-reactor/tasks/` as YAML files:

```
atomic-reactor/tasks/
├── T-001-lead-research.yaml
├── T-002-content-week.yaml
├── T-003-competitor-analysis.yaml
...
├── T-030-generate-20-x-twitter-posts.yaml
```

Each task file contains:
- **id**: Unique task identifier (T-001, T-002, etc.)
- **title**: Descriptive task name
- **type**: Category (content, research, code, business, optimization)
- **priority**: high, medium, or low
- **model**: AI model to use (kimi, claude, etc.)
- **estimated_time**: Hours needed to complete
- **objective**: What this task achieves
- **prompts**: Detailed instructions for execution
- **acceptance**: Criteria for completion
- **metadata**: Creation date, auto-generated flag, category

## 🔄 Executing Tasks

### Run All Tasks
```bash
cd atomic-reactor
python3 run_tasks.py
```

This will:
1. Load all tasks from `tasks/` directory
2. Execute them using Kimi API
3. Save reports to `reports/` directory
4. Generate summary with costs and results

### Run Specific Task
```bash
# Edit run_tasks.py to filter by task ID or category
```

## 📈 Task Statistics

From the current generation (25 tasks):
- **Total estimated time**: 75 hours
- **High priority**: 15 tasks (60%)
- **Content**: 5 tasks (10 hours)
- **Research**: 5 tasks (14 hours)
- **Code**: 5 tasks (16 hours)
- **Business**: 5 tasks (18 hours)
- **Optimization**: 5 tasks (14 hours)

## 🎨 Task Examples

### High Priority Content Task
```yaml
title: Generate 20 X/Twitter posts about AI automation
type: content
priority: high
estimated_time: 2 hours
objective: Create engaging X/Twitter content that drives engagement
prompts:
  - Generate 20 X/Twitter posts about AI automation. Mix educational,
    controversial, and behind-the-scenes content.
```

### High Priority Business Task
```yaml
title: Create 5 Gumroad digital products
type: business
priority: high
estimated_time: 6 hours
objective: Develop ready-to-sell digital products for immediate revenue
prompts:
  - Design 5 Gumroad products with pricing, outlines, and value props
```

### High Priority Code Task
```yaml
title: Build Telegram bot for GitHub issue notifications
type: code
priority: high
estimated_time: 4 hours
objective: Get real-time notifications for GitHub issues
prompts:
  - Create Python script for Telegram bot with webhooks
```

## ⚙️ Configuration

### Customize Task Definitions

Edit `task_generator.py` and modify the `TASK_DEFINITIONS` list:

```python
TASK_DEFINITIONS = [
    {
        "title": "Your custom task title",
        "type": "content",  # or research, code, business, optimization
        "priority": "high",  # or medium, low
        "time": 2,  # hours
        "objective": "What this task achieves",
        "prompts": ["Detailed instructions"]
    },
    # Add more tasks...
]
```

### Adjust Generation Frequency

Edit `.github/workflows/auto-task-generation.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
  # Change to: '0 */12 * * *' for every 12 hours
  # Change to: '0 0 * * *' for daily
```

## 💰 Cost Optimization

Tasks use Kimi API (Moonshot) for execution:
- **Cost**: ~$0.001 per 1K tokens
- **Average task**: 1000-2000 tokens
- **25 tasks**: ~$0.03-0.05 total
- **Monthly**: ~$5-10 for continuous generation

### Reduce Costs
1. Use Ollama locally (free) for simple tasks
2. Batch similar tasks together
3. Cache results to avoid re-execution
4. Use smaller models for straightforward tasks

## 🔐 Security

- Never commit API keys to the repository
- Use GitHub Secrets for sensitive data
- Review auto-generated PRs before merging
- Monitor API usage and costs

## 📊 Monitoring

### View Task Status
```bash
# List all tasks
ls -l atomic-reactor/tasks/

# Count by category
ls atomic-reactor/tasks/ | grep content | wc -l
```

### View Execution Reports
```bash
# List reports
ls -l atomic-reactor/reports/

# View latest summary
cat atomic-reactor/reports/summary_*.json | jq '.'
```

## 🐛 Troubleshooting

### Tasks Not Generating
1. Check GitHub Actions logs
2. Verify Python dependencies installed
3. Check MOONSHOT_API_KEY secret is set

### Task Execution Fails
1. Check API key and budget
2. Review error logs in reports/
3. Verify task YAML format is valid

### No Tasks in Directory
1. Run `python3 task_generator.py` manually
2. Check write permissions on atomic-reactor/tasks/
3. Look for Python errors in output

## 🎓 Best Practices

1. **Review before execution**: Always review tasks before running them
2. **Prioritize high-value**: Focus on high priority tasks first
3. **Track progress**: Use reports to measure completion and ROI
4. **Iterate**: Add more task templates based on what works
5. **Balance categories**: Keep a good mix of all task types

## 🔄 Workflow Integration

The task generation system integrates with:
- **GitHub Actions**: Automatic generation
- **Atomic Reactor**: Task execution
- **GitHub Issues**: Manual triggering via `@bot`
- **GitHub Control Interface**: Status and monitoring

## 📝 Future Enhancements

Potential improvements:
- [ ] AI-powered task prioritization
- [ ] Task dependencies and prerequisites
- [ ] Parallel task execution
- [ ] Real-time progress dashboard
- [ ] Slack/Telegram notifications
- [ ] Task templates from successful patterns
- [ ] Integration with project management tools

## 📞 Support

For questions or issues:
- Create a GitHub issue
- Comment `@bot help` in any issue
- Check the documentation in `docs/`

---

**Generated by**: AI Empire Automatic Task Generation System
**Version**: 1.0
**Last Updated**: 2026-02-08
