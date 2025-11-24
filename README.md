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

## 🚀 Future Improvements

### 🎯 Core Functionality Enhancements

#### 1. Multi-Application Support
- [ ] Add support for more web applications:
  - Jira, Trello, Monday.com
  - GitHub Issues, GitLab
  - Confluence, Slack
  - Salesforce, HubSpot
- [ ] Auto-detect application type from URL
- [ ] Dynamic adapter pattern for new applications

#### 2. Advanced Task Understanding
- [ ] Support for conditional logic in tasks
  - "If field X exists, then do Y, else Z"
- [ ] Multi-step workflow dependencies
  - "Complete Task A before starting Task B"
- [ ] Variable substitution
  - "Use today's date + 7 days for due date"
- [ ] Template-based task creation

#### 3. Intelligent Error Recovery
- [ ] Automatic retry with exponential backoff
- [ ] Alternative action suggestions when primary fails
- [ ] Checkpoint/resume functionality for long workflows
- [ ] Graceful degradation for partial task completion

### 🤖 AI & Machine Learning

#### 4. Model Improvements
- [ ] Fine-tune LLM on captured workflow data
- [ ] Train custom UI element detection model
- [ ] Predict optimal action sequences
- [ ] Learn from user corrections and feedback

#### 5. Vision Capabilities
- [ ] OCR for text extraction from screenshots
- [ ] Visual element detection without DOM access
- [ ] Screenshot-based state comparison
- [ ] Anomaly detection in UI states

### 📊 Analytics & Reporting

#### 6. Workflow Analytics
- [ ] Task completion success rate dashboard
- [ ] Average execution time per application
- [ ] Most common failure points analysis
- [ ] Performance metrics visualization

#### 7. Dataset Enhancements
- [ ] Export to common ML formats (TFRecord, Parquet)
- [ ] Automatic data versioning
- [ ] Diff generation between workflow versions
- [ ] Annotation tools for manual labeling

### 🔧 Developer Experience

#### 8. Testing & Validation
- [ ] Unit tests for all modules
- [ ] Integration tests with mock browsers
- [ ] Regression test suite from captured workflows
- [ ] CI/CD pipeline setup

#### 9. Documentation
- [ ] API documentation (Sphinx/MkDocs)
- [ ] Video tutorials for common workflows
- [ ] Troubleshooting guide
- [ ] Contributing guidelines

#### 10. Developer Tools
- [ ] VS Code extension for task authoring
- [ ] Workflow replay functionality
- [ ] Step-by-step debugger
- [ ] Performance profiler

### 🌐 Scalability & Performance

#### 11. Parallel Execution
- [ ] Run multiple tasks concurrently
- [ ] Browser pool management
- [ ] Distributed execution across machines
- [ ] Cloud deployment support (AWS, GCP, Azure)

#### 12. Optimization
- [ ] Reduce screenshot size (compression)
- [ ] Lazy loading of browser components
- [ ] Caching for repeated workflows
- [ ] Headless mode optimizations

### 🔐 Security & Compliance

#### 13. Enhanced Security
- [ ] Encrypted storage for sensitive data
- [ ] Secure credential management (Vault integration)
- [ ] Audit logging for all actions
- [ ] RBAC (Role-Based Access Control)

#### 14. Privacy Features
- [ ] PII detection and redaction in screenshots
- [ ] Configurable data retention policies
- [ ] GDPR compliance tools
- [ ] Anonymization of captured data

### 🎨 User Interface

#### 15. Web Dashboard
- [ ] Web-based UI for task management
- [ ] Real-time execution monitoring
- [ ] Workflow visualization (Gantt charts)
- [ ] Collaborative task editing

#### 16. Notifications
- [ ] Email alerts on task completion/failure
- [ ] Slack/Discord integration
- [ ] Webhook support for custom integrations
- [ ] Progress notifications

### 🔌 Integrations

#### 17. Third-Party Services
- [ ] Zapier integration for workflow triggers
- [ ] REST API for external access
- [ ] GraphQL API for flexible queries
- [ ] Webhook receivers for event-driven execution

#### 18. Data Export
- [ ] Direct export to cloud storage (S3, GCS)
- [ ] Integration with data warehouses (BigQuery, Snowflake)
- [ ] Real-time streaming to Kafka/RabbitMQ
- [ ] Export to test automation frameworks (Selenium, Playwright)

### 📱 Platform Support

#### 19. Cross-Platform
- [ ] Support for Firefox and Safari browsers
- [ ] Mobile app workflow capture (iOS, Android)
- [ ] Desktop application automation (Electron, native apps)
- [ ] API-first applications (non-browser)

#### 20. Deployment Options
- [ ] Docker containerization
- [ ] Kubernetes orchestration
- [ ] Serverless function deployment
- [ ] Edge computing support

### 🎓 Advanced Features

#### 21. Natural Language Generation
- [ ] Auto-generate workflow documentation from captures
- [ ] Create test case descriptions
- [ ] Generate user manuals
- [ ] Produce training materials

#### 22. Workflow Optimization
- [ ] Suggest workflow improvements
- [ ] Identify redundant steps
- [ ] Recommend keyboard shortcuts
- [ ] Batch operation detection

#### 23. Collaboration Features
- [ ] Share workflows with team members
- [ ] Version control for task definitions
- [ ] Commenting on workflow steps
- [ ] Workflow templates marketplace

### 🧪 Experimental

#### 24. Research Directions
- [ ] Self-healing workflows (auto-adapt to UI changes)
- [ ] Zero-shot task execution (no predefined tasks)
- [ ] Multi-modal understanding (text + vision + audio)
- [ ] Predictive task suggestions based on context

#### 25. Innovation
- [ ] Voice-controlled task execution
- [ ] AR/VR workflow visualization
- [ ] Blockchain-based workflow verification
- [ ] Quantum computing for optimization (future-future!)

---

### 🗳️ Contributing Your Ideas

Have suggestions for improvements? 

1. Open an issue on GitHub with the `enhancement` label
2. Join our discussions in the Issues section
3. Submit a PR with your implementation
4. Share your use cases and feedback

**Priority improvements are marked with ⭐ in our roadmap!**

---

**Built with ❤️ using Browser-Use and LangChain**
