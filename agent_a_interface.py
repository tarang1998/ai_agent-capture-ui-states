import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import httpx

from agent_b import AgentB
from browser_use.tools.registry.views import ActionModel
from question_parser_agent import QuestionParserAgent

logger = logging.getLogger(__name__)


class AgentAInterface:
    """
    Clean interface for Agent A to ask questions and get workflow captures.
    
    This is an orchestration layer that coordinates multiple specialized agents:
    - QuestionParserAgent: Parses natural language into structured tasks
    - AgentB: Captures workflows by automating web applications
    
    """
    
    def __init__(
        self,
        output_dir: str = "dataset",
        headless: bool = False,
    ):
        """
        Initialize the interface with specialized agents.
        
        Args:
            output_dir: Directory to save workflow captures
            headless: Whether to run browser in headless mode
        """
        # Initialize specialized agents
        self.parser_agent = QuestionParserAgent()
        self.agent_b = AgentB(
            output_base_dir=output_dir,
            headless=headless,
            keep_browser_alive=True,  # Keep browser alive between auth check and workflow capture
        )
        
        logger.info("✅ Agent A Interface initialized")
        logger.info("   • Question Parser Agent: Ready")
        logger.info("   • Agent B (Workflow Capture): Ready")
    
    async def _validate_app_url(self, app_url: str, app_name: str) -> tuple[bool, str]:
        """
        Validate that the app URL is accessible.
        
        This method sends a HEAD request to check if the URL is reachable
        before attempting to automate it with Browser-Use.
        
        Args:
            app_url: The URL to validate
            app_name: Name of the application (for logging)
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if URL is accessible, False otherwise
            - error_message: Empty string if valid, error description if invalid
        """
        logger.info(f"🔍 Validating URL: {app_url}")
        
        try:
            async with httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            ) as client:
                # Try HEAD request first (faster, no body)
                try:
                    response = await client.head(app_url)
                    status_code = response.status_code
                except Exception:
                    # Some servers don't support HEAD, try GET
                    response = await client.get(app_url)
                    status_code = response.status_code
                
                # Check if response is successful (2xx or 3xx)
                if 200 <= status_code < 400:
                    logger.info(f"✅ URL is accessible (status: {status_code})")
                    return True, ""
                else:
                    error_msg = f"URL returned status {status_code}"
                    logger.warning(f"⚠️ {error_msg}")
                    return False, error_msg
                    
        except httpx.TimeoutException:
            error_msg = f"URL validation timed out after 10 seconds. The server might be slow or unreachable."
            logger.error(f"❌ {error_msg}")
            return False, error_msg
            
        except httpx.ConnectError:
            error_msg = f"Could not connect to {app_url}. Please check if the URL is correct and the server is running."
            logger.error(f"❌ {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"URL validation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    async def _check_authentication(self, app_url: str, app_name: str) -> bool:
        """
        Check if user is authenticated using Browser-Use Agent.
        
        This approach:
        - Trusts Browser-Use to handle session persistence (user_data_dir)
        - Uses the agent to verify authenticated state
        - Only succeeds when user can access authenticated content
        
        Args:
            app_url: Application URL to check authentication for
            app_name: Name of the application
            
        Returns:
            True if authenticated, False otherwise
        """
        logger.info(f"🔐 Checking authentication for {app_name}...")
        
        from browser_use import Agent, ChatBrowserUse
        
        max_auth_attempts = 3
        
        for attempt in range(1, max_auth_attempts + 1):
            try:
                logger.info(f"🌐 Authentication check attempt {attempt}/{max_auth_attempts}...")
                
                # Initial actions to navigate to the app before agent starts
                initial_actions = [
                    {'navigate': {'url': app_url}},
                    {'wait': {'seconds': 2}},  # Let page load
                ]

                # Create an agent that verifies authentication by navigating to the app
                # and trying to access authenticated content
                auth_check_agent = Agent(
                    task=f"""You are already on {app_url}. Determine the authentication state.

Your goal: Check if this is a LOGIN PAGE or an AUTHENTICATED PAGE.

If you see a LOGIN PAGE (password fields, "Sign in"/"Log in" buttons, login forms):
- Extract "LOGIN_PAGE_DETECTED"
- Use the 'done' action immediately
- Do NOT attempt to log in

If you see an AUTHENTICATED PAGE (dashboard, workspace, user menu, main app content):
- Extract "AUTHENTICATED_PAGE_DETECTED"
- Use the 'done' action immediately

Observe the current page and report the state.""",
                    llm=ChatBrowserUse(),
                    browser=self.agent_b.browser,  # Reuse Agent B's browser
                    initial_actions=initial_actions,
                )
                
                # Run the authentication check agent
                history = await auth_check_agent.run(max_steps=3)
                
                # Check what the agent extracted
                extracted = history.extracted_content()
                
                logger.info(f"� Agent extracted: {extracted}")
                
                # Check if agent found authentication indicators
                if 'LOGIN_PAGE_DETECTED' in extracted:
                    logger.warning(f"⚠️ Authentication required for {app_name}")
                    logger.warning(f"🔓 User is NOT authenticated (attempt {attempt}/{max_auth_attempts})")
                    
                    # Get current page info for user
                    current_url = await self.agent_b.browser.get_current_page_url()
                    current_title = await self.agent_b.browser.get_current_page_title()
                    
                    # Prompt user to log in
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🔐 AUTHENTICATION REQUIRED FOR {app_name.upper()}")
                    logger.info(f"{'='*60}")
                    logger.info(f"")
                    logger.info(f"📌 Current page:")
                    logger.info(f"   URL: {current_url}")
                    logger.info(f"   Title: {current_title}")
                    logger.info(f"")
                    logger.info(f"Please complete the following steps:")
                    logger.info(f"  1. 🔑 Log in to your {app_name} account in the browser window")
                    logger.info(f"  2. 🛡️  Complete any 2FA/security challenges if prompted")
                    logger.info(f"  3. ⏳ Wait until you see the main app interface (dashboard/workspace)")
                    logger.info(f"  4. ✅ Return here and press Enter to continue")
                    logger.info(f"")
                    logger.info(f"⚠️  IMPORTANT:")
                    logger.info(f"    • DO NOT close the browser window!")
                    logger.info(f"    • The system will verify authentication automatically")
                    logger.info(f"    • Your session will be saved in ./browser_profile/")
                    logger.info(f"")
                    logger.info(f"{'='*60}\n")
                    
                    # Wait for user to complete login
                    input("✅ Press Enter after you've logged in and see the main app interface...")
                    
                    # Give a moment for any final redirects/page loads
                    await asyncio.sleep(3)
                    
                    # Continue to next attempt - agent will re-verify
                    continue
                
                elif 'AUTHENTICATED_PAGE_DETECTED' in extracted:
                    # Agent confirmed we're on authenticated page
                    current_url = await self.agent_b.browser.get_current_page_url()
                    logger.info(f"✅ Authentication verified! User is authenticated to {app_name}")
                    logger.info(f"📍 Current page: {current_url}")
                    logger.info(f"🚀 Proceeding with workflow capture in the same browser...\n")
                    return True
                
                else:
                    # Agent couldn't determine
                    raise Exception("Could not determine authentication state from agent extraction")
                
            except Exception as e:
                logger.error(f"❌ Authentication check error (attempt {attempt}): {e}")
                
                if attempt < max_auth_attempts:
                    logger.info(f"🔄 Retrying authentication check...")
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.warning(f"⚠️ Max authentication attempts reached. Proceeding anyway...")
                    return True  # Proceed to avoid blocking workflow
        
        # If we exhausted all attempts
        logger.error(f"❌ Could not verify authentication after {max_auth_attempts} attempts")
        logger.warning(f"⚠️ Proceeding anyway - workflow may fail if authentication required")
        return True  # Proceed anyway to avoid blocking
    
    async def ask(
        self,
        question: str,
        max_steps: int = 30,
    ) -> dict:
        """
        Ask Agent B how to perform a task.
        This is the main method Agent A would call to get workflow captures.
        
        This method orchestrates multiple agents:
        1. QuestionParserAgent parses the natural language question
        2. Agent B captures the workflow by automating the web app
        
        Args:
            question: Natural language question like:
                     "How do I create a project in Linear?"
                     "How do I filter issues by priority in Linear?"
                     "How do I create a database in Notion?"
            max_steps: Maximum workflow steps to execute
            
        Returns:
            Dictionary with complete workflow capture including:
            - metadata: Task info, duration, success status, LLM judgement
            - steps: List of UI states with screenshots, descriptions, actions
            
        Raises:
            ValueError: If question cannot be parsed
            
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🤔 Agent A asks: {question}")
        logger.info(f"{'='*60}\n")
        
        # Step 1: Parse question with specialized parser agent
        logger.info("📋 Step 1: Parsing question with Question Parser Agent...")
        parsed = await self.parser_agent.parse(question)
        
        if not parsed.is_valid():
            error_msg = (
                "Could not determine which app to use or its URL. "
                "Please provide a clear question mentioning the web application."
            )
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info(f"\n✅ Question parsed successfully:")
        logger.info(f"   App: {parsed.app_name}")
        logger.info(f"   URL: {parsed.app_url}")
        logger.info(f"   Task: {parsed.task}")
        logger.info(f"   Task ID: {parsed.task_name}")
        logger.info(f"   Optimized Description: {parsed.optimized_description}")
        logger.info(f"   Auth Required: {'Yes 🔐' if parsed.auth_required else 'No 🌐'}")
        logger.info(f"   Confidence: {parsed.confidence:.2%}\n")

        # Step 2: Validate app URL is accessible
        logger.info("📋 Step 2: Validating application URL...")
        is_valid, error_msg = await self._validate_app_url(parsed.app_url, parsed.app_name)
        
        if not is_valid:
            error_msg_full = (
                f"Cannot access {parsed.app_name} at {parsed.app_url}. "
                f"Reason: {error_msg}. "
            )
            logger.error(f"❌ {error_msg_full}")
            raise ValueError(error_msg_full)
        
        logger.info(f"✅ URL validation passed\n")

        # Step 3: Check for app authentication (only if required)
        if parsed.auth_required:
            logger.info("📋 Step 3: Checking authentication status (authentication required for this task)...")
            is_authenticated = await self._check_authentication(parsed.app_url, parsed.app_name)
            
            if not is_authenticated:
                error_msg = (
                    f"Authentication to {parsed.app_name} failed. "
                    "Please ensure you can log in successfully and try again."
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
        else:
            logger.info("📋 Step 3: Skipping authentication check (task does not require authentication) ✅\n")

        # Step 4: Capture workflow with Agent B using optimized description
        logger.info("🤖 Step 4: Capturing workflow with Agent B...")
        # Note: Browser is already started and on the right page from auth check
        # Agent B will reuse the same browser session
        workflow = await self.agent_b.capture_task(
            app_url=parsed.app_url,
            task=parsed.task,  # Original task for metadata
            task_name=parsed.task_name,  # LLM-generated task name
            app_name=parsed.app_name,
            max_steps=max_steps,
            optimized_description=parsed.optimized_description,  # Optimized for Browser-Use agent
        )
        
        # Log summary for Agent A
        self._log_result_summary(workflow)
        
        return workflow
    
    def _log_result_summary(self, workflow: dict) -> None:
        """
        Log a summary of the workflow result for Agent A.
        
        Args:
            workflow: Complete workflow capture dictionary
        """
        metadata = workflow['metadata']
        steps = workflow['steps']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RESULT SUMMARY FOR AGENT A")
        logger.info(f"{'='*60}")
        logger.info(f"Success: {'✅ Yes' if metadata['success'] else '❌ No'}")
        logger.info(f"Duration: {metadata['total_duration_seconds']:.1f}s")
        logger.info(f"Total Steps: {metadata['total_steps']}")
        logger.info(f"Screenshots: {sum(1 for s in steps if s['screenshot_path'])}")
        
        # Show judgement if available
        if metadata.get('judgement'):
            judgement = metadata['judgement']
            verdict = "✅ Success" if judgement['verdict'] else "❌ Failed"
            logger.info(f"\n🧑‍⚖️ LLM Judgement: {verdict}")
            if judgement.get('reasoning'):
                logger.info(f"Reasoning: {judgement['reasoning'][:100]}...")
        
        # Show first few steps
        logger.info(f"\n📸 UI States Captured:")
        for step in steps[:3]:
            desc = step.get('description', 'No description')[:60]
            logger.info(f"  • Step {step['step_number']}: {desc}...")
        
        if len(steps) > 3:
            logger.info(f"  ... and {len(steps) - 3} more steps")
        
        logger.info(f"{'='*60}\n")
    
    async def close(self):
        """
        Clean up resources.
        
        Should be called when Agent A is done querying Agent B.
        """
        logger.info("🔒 Closing Agent A Interface...")
        await self.agent_b.close()
        logger.info("✅ Resources cleaned up")


async def demo_agent_a_workflow():
    """
    Demo showing how Agent A would use this interface.
    
    This demonstrates a MULTI-AGENT ARCHITECTURE where Agent A orchestrates:
    1. QuestionParserAgent - Parses natural language into structured tasks
    2. Agent B - Captures workflows by automating web applications
  
    """
    print("\n" + "="*60)
    print("🤖 AGENT A WORKFLOW DEMO - MULTI-AGENT ARCHITECTURE")
    print("="*60)
    print("\nThis demo shows Agent A orchestrating specialized agents:")
    print("  1. Question Parser Agent - Understands user intent")
    print("  2. Agent B - Captures web workflows\n")
    
    # Initialize interface
    interface = AgentAInterface(
        output_dir="dataset",
        headless=False,  # Set to True in production
    )
    
    # Agent A's questions (these would come at runtime in production)
    questions = [
        "How do I create a project in Linear with name 'Galactus', priority 'Urgent', and dates?",
    ]
    
    try:
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*60}")
            print(f"📝 Question {i}/{len(questions)}")
            print(f"{'='*60}")
            print(f"🤔 Agent A asks: {question}\n")
            
            # Get workflow capture from Agent B
            result = await interface.ask(question, max_steps=30)
            
            # Agent A processes the result
            metadata = result['metadata']
            steps = result['steps']
            
            print(f"\n{'='*60}")
            print(f"✅ AGENT A RECEIVED WORKFLOW CAPTURE")
            print(f"{'='*60}")
            print(f"App: {metadata['app_name']}")
            print(f"Task: {metadata['task_description']}")
            print(f"Success: {'✅ Yes' if metadata['success'] else '❌ No'}")
            print(f"Duration: {metadata['total_duration_seconds']:.1f}s")
            print(f"Steps Captured: {len(steps)}")
            
            # Check LLM judgement
            if metadata.get('judgement'):
                judgement = metadata['judgement']
                verdict = "✅ Success" if judgement['verdict'] else "❌ Failed"
                print(f"\n🧑‍⚖️ LLM Judgement: {verdict}")
                if judgement.get('reasoning'):
                    print(f"Reasoning: {judgement['reasoning'][:150]}...")
                if judgement.get('failure_reason'):
                    print(f"Failure Reason: {judgement['failure_reason']}")
            
            # Show captured UI states
            print(f"\n📸 UI States Captured:")
            for step in steps:
                desc = step.get('description', 'No description')[:70]
                actions = len(step.get('actions_taken', []))
                has_screenshot = "📸" if step['screenshot_path'] else "  "
                print(f"  {has_screenshot} Step {step['step_number']:2d} ({actions} action{'s' if actions != 1 else ''}): {desc}...")
            
            # Show where files are saved
            print(f"\n💾 Dataset Location:")
            print(f"   {metadata.get('app_name')}/{metadata.get('task_name')}/")
            print(f"   • workflow.json")
            print(f"   • {sum(1 for s in steps if s['screenshot_path'])} screenshots")
            
            # Agent A can now use this data for:
            print(f"\n🎯 Agent A can now:")
            print(f"   • Display workflow to users as a tutorial")
            print(f"   • Train other agents on this data")
            print(f"   • Generate documentation")
            print(f"   • Replay the workflow")
            print(f"   • Analyze patterns across workflows")
            
            print(f"\n{'='*60}\n")
            
    finally:
        # Clean up
        await interface.close()
        


async def simple_example():
    """
    Minimal example showing the simplest way to use the interface.
    """
    # Initialize
    interface = AgentAInterface()
    
    try:
        # Agent A asks a question
        result = await interface.ask(
            "How do I create a project in Linear with name 'Galactus' and priority 'Urgent'?"
        )
        
        # Agent A uses the result
        if result['metadata']['success']:
            print("✅ Workflow captured successfully!")
            print(f"Total steps: {len(result['steps'])}")
            
            # Access individual steps
            for step in result['steps']:
                print(f"Step {step['step_number']}: {step.get('description', 'No description')[:50]}...")
        else:
            print("❌ Workflow capture failed")
    
    finally:
        # Always clean up
        await interface.close()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the demo
    print("\n🚀 Starting Agent A Interface Demo...\n")
    asyncio.run(demo_agent_a_workflow())
    
    # Uncomment to run simple example instead:
    # asyncio.run(simple_example())
