# AI Agent - Capture UI States

A multi-agent system that captures UI states and workflows from web applications (Linear and Asana) using AI-powered browser automation.

## 🚀 Installation

### Install uv (if not already installed)

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/tarang1998/ai_agent-capture-ui-states.git
cd ai_agent-capture-ui-states

# Install dependencies using uv
uv sync
```

This will create a virtual environment and install all required packages from `pyproject.toml`.

## ⚙️ Configuration

### Create Environment File

Create a `.env` file in the project root directory:

```bash
# .env file
OPENAI_API_KEY=sk-your-openai-api-key-here
BROWSER_USE_API_KEY=your-browser-use-api-key-here
```

## 🎮 Usage

### Run the Interactive CLI

```bash
uv run python main.py
```

## 🔐 Authentication & Sessions

### Browser Profile Management

The system uses a **persistent browser profile** stored in `browser_profile/` directory to maintain authentication across sessions.

#### How It Works

1. **First Run**:
   - Browser opens in non-headless mode
   - User manually logs into Linear/Asana
   - Credentials are saved in the browser profile
2. **Subsequent Runs**:
   - Browser loads saved profile
   - Already authenticated - no login required
   - Cookies and sessions persist

## 💾 Dataset Storage

### Output Structure

Each task execution generates structured data in the `dataset/` directory:

```
dataset/
├── linear_create_project_20250124_143022/
│   ├── workflow.json                    # Complete workflow data
│   ├── state_0_initial.png             # Initial state screenshot
│   ├── state_1_clicked_new.png         # After clicking "New"
│   ├── state_2_filled_form.png         # After filling form
│   └── state_3_final.png               # Final state
│
└── asana_create_task_20250124_143155/
    ├── workflow.json
    ├── state_0_initial.png
    └── ...
```

### Example Workflow JSON Format

```json
{
  "metadata": {
    "app_name": "Linear",
    "task_name": "create_issue_fix_data_sync_bug",
    "task_description": "Create a new issue with title 'Fix data synchronization bug', add description 'Investigate and resolve data sync issues between services', set priority to 'High', assign project as 'Galactus' and status as 'TODO'",
    "start_url": "https://linear.app",
    "capture_timestamp": "2025-11-23T06:02:59.387844",
    "total_duration_seconds": 41.263404,
    "total_steps": 9,
    "success": true,
    "judgement": {
      "verdict": true,
      "reasoning": "The agent successfully completed all parts of the user's request. It navigated to Linear.app, opened the new issue modal, set the title ('Fix data synchronization bug') and description ('Investigate and resolve data sync issues between services'), set the priority to 'High', and assigned the project to 'Galactus'. The status was implicitly set to 'TODO', which matched the requirement. The agent also took appropriate screenshots at major UI state changes as requested. The execution was efficient and accurate.",
      "failure_reason": "",
      "impossible_task": false,
      "reached_captcha": false
    }
  },
  "steps": [
    {
      "step_number": 0,
      "url": "https://linear.app",
      "title": "Initial Actions",
      "screenshot_path": null,
      "description": "Initial navigation",
      "step_task": "🔗 Navigated to https://linear.app",
      "actions_taken": [
        {
          "action_name": "NavigateActionModel",
          "params": {
            "navigate": {
              "url": "https://linear.app",
              "new_tab": false
            }
          }
        }
      ],
      "errors": [],
      "success": null,
      "is_done": false
    },

    {
      "step_number": 8,
      "url": "https://linear.app/softlight-linear-test/team/SOF/active",
      "title": "Linear",
      "screenshot_path": "dataset\\Linear\\create_issue_fix_data_sync_bug\\step_008.png",
      "description": "The previous step successfully clicked the 'Create issue' button. The current state is the Linear dashboard, and the newly created issue \"Fix data synchronization bug\" (SOF-6) is visible in the 'Todo' section, confirming the creation. The task is complete. I will now issue the `done` action.",
      "step_task": "Successfully created a new Linear issue with title 'Fix data synchronization bug', description 'Investigate and resolve data sync issues between services', priority 'High', project 'Galactus', and status 'TODO'.",
      "actions_taken": [
        {
          "action_name": "DoneActionModel",
          "params": {
            "done": {
              "text": "Successfully created a new Linear issue with title 'Fix data synchronization bug', description 'Investigate and resolve data sync issues between services', priority 'High', project 'Galactus', and status 'TODO'.",
              "success": true
            }
          }
        }
      ],
      "errors": [],
      "success": true,
      "is_done": true,
      "judgement": {
        "verdict": true,
        "reasoning": "The agent successfully completed all parts of the user's request. It navigated to Linear.app, opened the new issue modal, set the title ('Fix data synchronization bug') and description ('Investigate and resolve data sync issues between services'), set the priority to 'High', and assigned the project to 'Galactus'. The status was implicitly set to 'TODO', which matched the requirement. The agent also took appropriate screenshots at major UI state changes as requested. The execution was efficient and accurate.",
        "failure_reason": "",
        "impossible_task": false
      }
    }
  ]
}
```
