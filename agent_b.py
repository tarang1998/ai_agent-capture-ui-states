"""
Agent B - UI State Capture System

This agent receives tasks from Agent A and captures UI states during workflow execution.
It automatically navigates web apps and captures screenshots of each UI state, including
non-URL states like modals, popups, and forms.
"""

import asyncio
import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from browser_use import Agent, Browser, ChatBrowserUse, Tools
from browser_use.agent.views import AgentHistoryList
from browser_use.llm import ChatOpenAI

logger = logging.getLogger(__name__)


class AgentB:
    """
    Agent B - Captures UI states for any given task across different web apps.

    """
    
    def __init__(
        self,
        output_base_dir: str = "dataset",
        headless: bool = False,
        keep_browser_alive: bool = False,
    ):
        """
        Initialize Agent B with browser configuration.
        
        Args:
            output_base_dir: Base directory for saving captured workflows
            headless: Whether to run browser in headless mode
            keep_browser_alive: Whether to keep browser alive between tasks
        """
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure browser for optimal UI state capture
        self.browser = Browser(
            headless=headless,
            window_size={'width': 1920, 'height': 1080},
            user_data_dir='./browser_profile',  # Persist login sessions
            # This allows the agent to:
            # 1. Log in once manually or programmatically
            # 2. Reuse authentication for subsequent workflow captures
            # 3. Work with enterprise apps that require authentication
            keep_alive=keep_browser_alive,
            minimum_wait_page_load_time=0.2,  # Reduced from 0.5s - faster page loads
            wait_for_network_idle_page_load_time=0.5,  # Reduced from 1.0s - SPAs load faster
            highlight_elements=False,  # Disable border UI around clickable elements
        )
        
        # Use ChatBrowserUse - optimized for browser automation
        self.llm = ChatBrowserUse()
        
        # Use OpenAI GPT-4o-mini for LLM judgement - better reasoning for success evaluation
        self.judge_llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.0)

        self.tools = Tools()

        @self.tools.action('temp_action')
        async def temp_action(query: str, browser: Browser) -> str:
            """Extract specific data from page using LLM"""
            # Use browser-use extract with custom query
            return ""

        
        self.current_workflow = None
    
    async def capture_task(
        self,
        app_url: str,
        task: str,
        task_name: str,
        app_name: str,
        max_steps: int = 30,
        optimized_description: str | None = None,
    ) -> dict[str, Any]:
        """
        Main entry point for capturing a workflow.
        
        Args:
            app_url: Starting URL for the web app
            task: Natural language description of the task to perform
            task_name: Identifier for this task (e.g., "create_project")
            app_name: Name of the web app (e.g., "linear", "notion")
            max_steps: Maximum number of steps to execute
            optimized_description: Optional optimized task description for Browser-Use agent.
            
        Returns:
            Dictionary containing workflow metadata and captured states
        """        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 Starting Agent B")
        logger.info(f"   App: {app_name}")
        logger.info(f"   Task: {task_name}")
        logger.info(f"   URL: {app_url}")
        if optimized_description:
            logger.info(f"   Original: {task}")
            logger.info(f"   Optimized: {optimized_description}")
        logger.info(f"{'='*60}\n")
        
        # Create output directory for this task
        output_dir = self.output_base_dir / app_name / task_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Enhanced system prompt for UI state capture
        extended_prompt = """
        CRITICAL INSTRUCTIONS FOR UI STATE CAPTURE:

        Your goal is to capture EVERY distinct UI state during this workflow, especially states 
        that don't have URLs (modals, popups, forms, dropdowns).

        1. **Screenshots Are Automatic**:
        - With vision mode enabled, a screenshot is captured at the END of each step
        - You don't need to request screenshots explicitly
        - Focus on describing what you see, not on taking screenshots

        2. **Capture Non-URL States** (CRITICAL):
        When modals, dialogs, dropdown menus, or popups appear:
        - Describe what you see in your next_goal field
        - The automatic screenshot will capture the current state
        - Examples of non-URL states to capture:
            * Modal windows (project creation, settings, etc.)
            * Dropdown menus (filters, selections)
            * Popups and overlays
            * Form wizards and multi-step flows
            * Success/confirmation messages

        3. **Document Every State** (CRITICAL):
        In your next_goal field, describe the CURRENT UI state you're viewing:
        - ✅ GOOD: "Viewing modal titled 'Create Project' with 3 input fields: Name, Description, Team"
        - ✅ GOOD: "Dropdown menu expanded showing 5 priority options: High, Medium, Low, None, Urgent"
        - ✅ GOOD: "Form filled - Project name: 'Marketing', Description entered, ready to submit"
        - ❌ BAD: "Clicking create button" (describes action, not state)
        - ❌ BAD: "Going to projects" (too vague)

        4. **Efficient Execution** (OPTIMIZED):
        - Take MAXIMUM 2 actions per step for better state coverage
        - DO NOT use explicit wait() actions unless absolutely necessary (e.g., animations, slow network)
        - The browser automatically waits for page loads and UI to settle between actions
        - Trust the automatic timing - focus on taking actions and describing states
        - Only use wait() if you see a specific loading indicator that needs time

        5. **Form Filling Strategy**:
        - Fill 2-3 related fields per step, not all at once
        - Example: Step 1: Fill "Name" and "Description", Step 2: Fill "Team" and "Priority"
        - This captures the form in multiple states as it's being filled

        6. **Success/Completion States**:
        - Always capture the final success or confirmation screen
        - Describe what indicates success (green checkmark, "Created successfully" message, etc.)
        - Use `done` action only after capturing the completion state

        7. **Multi-Step Workflows**:
        - For wizards or multi-step forms, capture each step/screen
        - Describe which step you're on (e.g., "Step 2 of 3: Selecting team members")

        REMEMBER: Your goal is to move through the workflow slowly enough that each important 
        UI state (especially modals and popups that have no URL) gets captured in a screenshot.
        Describe what you see clearly, and the automatic screenshots will document everything.
        """
        
        # Create agent with enhanced configuration and LLM judgement
        judge_prompt = f"""Evaluate if the task was completed successfully.

        Task: {task}
        Application: {app_name}

        Success criteria:
        1. All required fields were filled/actions taken as specified in the task
        2. Final state shows task completion (success message, created item visible, confirmation dialog, etc.)
        3. No errors, failures, or blockers occurred (no captchas, no auth failures, no error messages)
        4. The workflow reached its natural completion state

        Examples of SUCCESS indicators:
        - "Created successfully" message
        - "Project created" confirmation
        - New item visible in list/dashboard
        - Success checkmark or notification
        - Redirected to the newly created item's page

        Examples of FAILURE indicators:
        - Stuck on login/authentication page
        - Captcha encountered
        - Error messages displayed
        - Task incomplete (e.g., modal still open, form not submitted)
        - Browser stuck on same page without progress

        Return verdict=True ONLY if the task is FULLY completed with clear success indicators.
        Return verdict=False if task is incomplete, stuck, or encountered errors."""

        agent = Agent(
            task=f"Open  the URL : {app_url}. Perform the task: {task}. Take screenshots at every major UI state change, especially modals, forms, and confirmation screens.",
            llm=self.llm,
            browser=self.browser,
            use_vision=True,  # Enable vision for screenshot analysis
            extend_system_message=extended_prompt,
            max_actions_per_step=2,  # Limit actions for cleaner state capture
            wait_between_actions=0.3,  # Reduced from 1.0s - faster execution while still allowing UI to settle
            # judge_llm=self.judge_llm,  # Use OpenAI GPT-4o-mini for better reasoning
            # judge_prompt=judge_prompt,  # Custom prompt for success evaluation
            # flash_mode=True,
            # tools=self.tools,
            vision_detail_level="high",
        )
        
        # Track start time
        start_time = datetime.now()
        
        # Run agent and capture history
        try:
            history: AgentHistoryList = await agent.run(max_steps=max_steps)
        except Exception as e:
            logger.error(f"❌ Error during workflow execution: {e}")
            raise
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Build workflow data structure
        workflow = await self._build_workflow_data(
            history=history,
            app_name=app_name,
            app_url=app_url,
            task=task,
            task_name=task_name,
            output_dir=output_dir,
            duration=duration,
        )
        
        # Save workflow metadata
        self._save_workflow_metadata(workflow, output_dir)
        
        # Generate summary
        self._print_summary(workflow, output_dir)
        
        return workflow
    
    async def _build_workflow_data(
        self,
        history: AgentHistoryList,
        app_name: str,
        app_url: str,
        task: str,
        task_name: str,
        output_dir: Path,
        duration: float,
    ) -> dict[str, Any]:
        """Build structured workflow data from agent history."""
        
        # Extract judgement information if available
        judgement_data = None
        if history.is_judged():
            judgement_result = history.judgement()
            if judgement_result:
                judgement_data = {
                    "verdict": judgement_result.get("verdict"),
                    "reasoning": judgement_result.get("reasoning"),
                    "failure_reason": judgement_result.get("failure_reason"),
                    "impossible_task": judgement_result.get("impossible_task", False),
                    "reached_captcha": judgement_result.get("reached_captcha", False),
                }
        
        workflow = {
            "metadata": {
                "app_name": app_name,
                "task_name": task_name,
                "task_description": task,
                "start_url": app_url,
                "capture_timestamp": datetime.now().isoformat(),
                "total_duration_seconds": duration,
                "total_steps": len(history.history),
                "success": history.is_successful(),
                "judgement": judgement_data,  # Include LLM judgement of entire workflow
            },
            "steps": [],
        }

        # Process each step in the history
        for i, step in enumerate(history.history):
            step_data = await self._process_step(step, i, output_dir)
            workflow["steps"].append(step_data)
        
        return workflow
    
    async def _process_step(
        self,
        step,
        step_number: int,
        output_dir: Path,
    ) -> dict[str, Any]:
        """Process a single step and extract relevant information."""

        step_data = {
            "step_number": step_number,
            "url": step.state.url if step.state else None,
            "title": step.state.title if step.state else None,
            "screenshot_path": None,
            "description": None,
            "step_task": None,  
            "actions_taken": [],
            "errors": [],  # Track errors for this step
            "success": None,  # Whether this step succeeded
            "is_done": False,  # Whether this step marked the task as done
        }
        
        # Extract description
        if step.model_output:
            if hasattr(step.model_output, 'memory') and step.model_output.memory:
                step_data["description"] = step.model_output.memory
        
        # Extract actions taken
        if step.model_output and step.model_output.action:
            for action in step.model_output.action:
                # Get the root action class name (e.g., ExtractActionModel, ClickActionModel)
                # instead of the wrapper ActionModel class name
                action_name = action.__class__.__name__
                if hasattr(action, 'root') and action.root:
                    action_name = action.root.__class__.__name__
                
                action_dict = {
                    "action_name": action_name,
                    "params": action.model_dump(exclude_unset=True, exclude={'get_screenshot'}),
                }
                step_data["actions_taken"].append(action_dict)
        
        # Extract errors and results from this step
        if step.result:
            result_descriptions = []
            for result in step.result if isinstance(step.result, list) else [step.result]:
                if hasattr(result, 'extracted_content') and result.extracted_content:
                    result_descriptions.append(result.extracted_content)

                # Track errors
                if hasattr(result, 'error') and result.error:
                    step_data["errors"].append(result.error)
                
                # Track success/done status
                if hasattr(result, 'success') and result.success is not None:
                    step_data["success"] = result.success
                
                if hasattr(result, 'is_done') and result.is_done:
                    step_data["is_done"] = True
                    
                    # If this step has judgement, include it
                    if hasattr(result, 'judgement') and result.judgement:
                        step_data["judgement"] = {
                            "verdict": result.judgement.verdict,
                            "reasoning": result.judgement.reasoning,
                            "failure_reason": result.judgement.failure_reason,
                            "impossible_task": result.judgement.impossible_task,
                        }
            if result_descriptions:
                step_data["step_task"] = " | ".join(result_descriptions)
        
        # If there are errors but no explicit success flag, mark as failed
        if step_data["errors"] and step_data["success"] is None:
            step_data["success"] = False
        
        # Save screenshot if available
        if step.state and step.state.screenshot_path:
            screenshot = step.state.get_screenshot()
            if screenshot:
                screenshot_filename = f"step_{step_number:03d}.png"
                screenshot_path = output_dir / screenshot_filename
                
                try:
                    # Decode and save screenshot
                    screenshot_data = base64.b64decode(screenshot)
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot_data)
                    
                    step_data["screenshot_path"] = str(screenshot_path)
                    logger.info(f"  📸 Saved screenshot: {screenshot_filename}")
                except Exception as e:
                    logger.error(f"  ⚠️  Failed to save screenshot for step {step_number}: {e}")
        
        return step_data
    
    
    def _save_workflow_metadata(self, workflow: dict[str, Any], output_dir: Path) -> None:
        """Save workflow metadata to JSON file."""
        metadata_path = output_dir / "workflow.json"
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            logger.info(f"\n✅ Saved workflow metadata: {metadata_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save workflow metadata: {e}")
    
    def _print_summary(self, workflow: dict[str, Any], output_dir: Path) -> None:
        """Print a summary of the captured workflow."""
        metadata = workflow["metadata"]
        steps = workflow["steps"]
        
        print(f"\n{'='*60}")
        print(f"📊 WORKFLOW CAPTURE SUMMARY")
        print(f"{'='*60}")
        print(f"App: {metadata['app_name']}")
        print(f"Task: {metadata['task_name']}")
        print(f"Description: {metadata['task_description']}")
        print(f"Duration: {metadata['total_duration_seconds']:.2f}s")
        print(f"Total Steps: {metadata['total_steps']}")
        print(f"Success: {'✅' if metadata['success'] else '❌'}")
        
        # Display judgement information if available
        if metadata.get('judgement'):
            judgement = metadata['judgement']
            print(f"\n🧑‍⚖️ LLM Judgement:")
            print(f"  Verdict: {'✅ Success' if judgement['verdict'] else '❌ Failed'}")
            if judgement.get('reasoning'):
                print(f"  Reasoning: {judgement['reasoning'][:150]}...")
            if judgement.get('failure_reason'):
                print(f"  Failure Reason: {judgement['failure_reason']}")
            if judgement.get('impossible_task'):
                print(f"  ⚠️  Task marked as impossible")
            if judgement.get('reached_captcha'):
                print(f"  🤖 Captcha encountered")
        
        print(f"\nOutput Directory: {output_dir}")
        
        # Count screenshots
        screenshots_captured = sum(1 for step in steps if step['screenshot_path'])
        print(f"Screenshots Captured: {screenshots_captured}")
        
        print(f"{'='*60}\n")
    
    async def close(self):
        """Clean up resources and close browser."""
        if self.browser:
            try:
                # Close browser - always close after task completion
                await self.browser.kill()
                logger.info("🔒 Browser closed successfully")
            except Exception as e:
                logger.error(f"❌ Error closing browser: {e}")


async def main():
    """Example usage of Agent B."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize Agent B
    agent_b = AgentB(
        output_base_dir="dataset",
        headless=False,  # Set to True for production
    )
    
    try:
        # Example: Capture a comprehensive Linear workflow
        workflow = await agent_b.capture_task(
            app_url="https://linear.app",
            task="""Create a new project with the following details:
            - Project name: 'Galactus'
            - Short summary: 'Enterprise-level resource management platform'
            - Description: 'A comprehensive system for managing cloud resources, tracking costs, and optimizing infrastructure across multiple regions. This project aims to provide real-time monitoring and automated scaling capabilities.'
            - Priority: Change to 'Urgent'
            - Start date: Today's date
            - End date: Tomorrow's date (next day)
            
            Fill out all available fields in the project creation form.""",
            task_name="create_comprehensive_project",
            app_name="linear",
            max_steps=30,  # Increased for more complex workflow
        )
        
        print("\n✅ Workflow captured successfully!")
        print(f"Check the dataset folder for results.")
        
    finally:
        await agent_b.close()


if __name__ == "__main__":
    asyncio.run(main())
