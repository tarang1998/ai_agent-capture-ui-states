"""
Question Parser Agent - Specialized agent for intent understanding.

This agent is responsible for parsing natural language questions into structured
task specifications. It acts as the "intent understanding" layer in the multi-agent
system, translating human questions into machine-actionable parameters.

Key Responsibilities:
- Extract web application name from natural language
- Identify application URLs
- Parse task descriptions, task_name, optimized task description
- Determine if authentication is required

"""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ParsedQuestionSchema(BaseModel):
    """
    Pydantic schema for structured LLM output.
    
    This schema is used by the LLM to return validated, type-safe data
    without manual JSON parsing. The LLM will automatically return an
    instance of this class with all fields validated.
    """
    app_name: str = Field(
        description="Name of the web application (e.g., 'Linear', 'GitHub', 'Notion')"
    )
    app_url: str = Field(
        description="Full URL to the application, must start with https. (e.g., 'https://linear.app', 'https://github.com')"
    )
    task: str = Field(
        description="Clean task description. Should be specific, actionable, and include all relevant details. ** IMP : do not remove any specifications from the prompt"
    )
    task_name: str = Field(
        description="Filesystem-safe task identifier in snake_case (e.g., 'create_project_urgent', 'filter_issues_by_priority'). Max 5 words, lowercase, underscores only."
    )
    optimized_description: str = Field(
        description="Clear, imperative description optimized for Browser-Use agent. Should be specific, actionable, and include all relevant details. Use imperative mood (e.g., 'Create a new project named Galactus with Urgent priority and set start/end dates'). Include specific values, field names, and expected outcomes."
    )
    auth_required: bool = Field(
        description="Whether authentication is required to perform this task. Examples: Creating/editing content requires auth (Linear project, GitHub PR, Notion page). Viewing public content does NOT require auth (GitHub stars, public repos, public pages). Return True if task involves creating, editing, or accessing private data. Return False if task only involves viewing public information."
    )

logger = logging.getLogger(__name__)


class ParsedQuestion:
    """
    Structured representation of a parsed question.
    
    This data class holds the extracted information from a natural language
    question, making it easy to pass between agents and validate outputs.
    """
    
    def __init__(
        self,
        app_name: str,
        app_url: str,
        task: str,
        task_name: str,
        optimized_description: str,
        auth_required: bool,
        confidence: float = 1.0,
        raw_question: Optional[str] = None,
    ):
        """
        Initialize parsed question result.
        
        Args:
            app_name: Name of the web application (e.g., "Linear", "GitHub")
            app_url: Full URL to the application (e.g., "https://linear.app")
            task: Clean task description without app name
            task_name: Filesystem-safe task identifier (snake_case)
            optimized_description: Clear, imperative description for Browser-Use agent
            auth_required: Whether authentication is required to perform this task
            confidence: Confidence score for the parsing (0.0-1.0)
            raw_question: Original question that was parsed
        """
        self.app_name = app_name.strip()
        self.app_url = app_url.strip()
        self.task = task.strip()
        self.task_name = task_name.strip()
        self.optimized_description = optimized_description.strip()
        self.auth_required = auth_required
        self.confidence = confidence
        self.raw_question = raw_question
        
    
    def is_valid(self) -> bool:
        """Check if all required fields are present."""
        return bool(self.app_name and self.app_url and self.task)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'app_name': self.app_name,
            'app_url': self.app_url,
            'task': self.task,
            'task_name': self.task_name,
            'optimized_description': self.optimized_description,
            'auth_required': self.auth_required,
            'confidence': self.confidence,
            'raw_question': self.raw_question,
        }
    
    def __repr__(self) -> str:
        return f"ParsedQuestion(app={self.app_name}, task={self.task[:30]}...)"


class QuestionParserAgent:
    """
    Specialized agent for parsing natural language questions into structured tasks.
    
    This agent uses LLM reasoning to understand user intent and extract:
    - Which web application to interact with
    - The URL of that application
    - What specific task needs to be performed
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        enable_cache: bool = False,
    ):
        """
        Initialize the Question Parser Agent with structured output.
        
        Args:
            llm: Language model for parsing. If None, uses ChatOpenAI with gpt-4o-mini
            enable_cache: Whether to cache parsing results (useful in production)
        """
        # Initialize base LLM
        base_llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        
        # Configure for structured output - LLM will return ParsedQuestionSchema objects
        self.llm = base_llm.with_structured_output(ParsedQuestionSchema)
        
        self.enable_cache = enable_cache
        self._cache: dict[str, ParsedQuestion] = {}
        
        logger.info("✅ Question Parser Agent initialized (using OpenAI with structured output)")
    
    async def parse(self, question: str) -> ParsedQuestion:
        """
        Parse a natural language question into structured task information.
        
        This is the main entry point for the agent. It analyzes the question
        and extracts structured information about which app to use and what
        task to perform.
        
        Args:
            question: Natural language question from user or Agent A
                     Examples:
                     - "How do I create a project in Linear?"
                     - "Show me how to filter issues by priority in Linear"
                     - "How can I create a database in Notion?"
                     - "How do I star a repository on GitHub?"
        
        Returns:
            ParsedQuestion object with extracted information
            
        Raises:
            ValueError: If question cannot be parsed or is invalid
        """
        logger.info(f"🔍 Parsing question: {question[:100]}...")
        
        # Check cache first
        if self.enable_cache and question in self._cache:
            logger.info("💾 Cache hit - returning cached result")
            return self._cache[question]
        
        # Parse with LLM
        result = await self._parse_with_llm(question)
        
        # Validate result
        if not result.is_valid():
            raise ValueError(
                f"Parsing failed - missing required fields. "
                f"Got: app_name={result.app_name}, app_url={result.app_url}, task={result.task}"
            )
        
        # Log result
        logger.info(f"✅ Parsed successfully:")
        logger.info(f"   App: {result.app_name}")
        logger.info(f"   URL: {result.app_url}")
        logger.info(f"   Task: {result.task}")
        logger.info(f"   Task Name: {result.task_name}")
        logger.info(f"   Optimized Description: {result.optimized_description[:80]}...")
        logger.info(f"   Auth Required: {'Yes 🔐' if result.auth_required else 'No 🌐'}")
        logger.info(f"   Confidence: {result.confidence:.2f}")
        
        # Cache result
        if self.enable_cache:
            self._cache[question] = result
        
        return result
    
    async def _parse_with_llm(self, question: str) -> ParsedQuestion:
        """
        Use LLM with structured output to parse the question.
        
     
        
        Args:
            question: Natural language question
            
        Returns:
            ParsedQuestion with extracted information
            
        Raises:
            ValueError: If LLM parsing fails or returns invalid data
        """
        # Enhanced prompt with all required fields and validation instructions
        parsing_prompt = f"""Extract structured information from this question about web applications.

Question: "{question}"

IMPORTANT: If the question does NOT mention a specific web application/page or task, you MUST return:
- app_name: "UNKNOWN"
- app_url: "UNKNOWN"
- task: "UNKNOWN"
- task_name: "unknown"
- optimized_description: "UNKNOWN"

Only extract real information if the question is clearly about a web application task.

Extract these fields:

1. **app_name**: The web application name (Linear, Notion, GitHub, Asana, Jira, etc.)
   - Must be a real web application mentioned in the question
   - Return "UNKNOWN" if no web app is mentioned

2. **app_url**: The main URL (https://linear.app, https://notion.so, https://github.com, etc.)
   - IMP : Make sure the URL starts with https://
   - Must be the correct URL for the identified app
   - Return "UNKNOWN" if app cannot be identified

3. **task**: What the user wants to do, WITHOUT including the app name
   - Must be a clear action or workflow
   - Return "UNKNOWN" if no task is described

4. **task_name**: A filesystem-safe identifier in snake_case format:
   - Use lowercase letters, numbers, and underscores only
   - Maximum 5 words
   - Example: "create_project_urgent", "filter_issues_by_priority"
   - Return "unknown" if no valid task

5. **optimized_description**: A clear, imperative description for a Browser-Use automation agent:
   - Use imperative mood (command form)
   - Do not add any additional context
   - Return "UNKNOWN" if no valid task

6. **auth_required**: Boolean indicating if user authentication is needed:
   - True: Creating, editing, deleting, or accessing private/user-specific content
     Examples: Creating Linear projects, starring GitHub repos (requires login), creating Notion pages, posting comments
   - False: Viewing public content, browsing public pages, reading public repos
     Examples: Viewing public GitHub repos, reading public documentation, browsing public websites
   - Return True by default unless the task is clearly read-only public content

Examples of INVALID questions that should return UNKNOWN:
- "What's the weather today?"
- "Tell me a joke"
- "How are you?"
- "Random text without meaning"
- "Hello world"

Examples of VALID questions with auth_required:
- "How do I create a project in Linear?" → auth_required=True (creating content)
- "How do I star a repository on GitHub?" → auth_required=True (requires login to star)
- "Show me the stars on torvalds/linux GitHub repo" → auth_required=False (viewing public data)
- "Create a database in Notion with title 'Customers'" → auth_required=True (creating content)
- "How do I view issues in a public GitHub repository?" → auth_required=False (public read-only)

Be precise and extract exact information from the question."""

        try:
           
            result = await self.llm.ainvoke(parsing_prompt)
            
            # Validate that we got real data, not UNKNOWN placeholders
            if (result.app_name == "UNKNOWN" or 
                result.app_url == "UNKNOWN" or  
                result.task == "UNKNOWN"):  
                raise ValueError(
                    f"Cannot extract web application information from question: '{question}'. "
                    "Please provide a question about a specific web application task. "
                    "Example: 'How do I create a project in Linear?'"
                )
            
            # Additional validation: Check if app_name and app_url are sensible
            if not result.app_name or len(result.app_name.strip()) < 2:  
                raise ValueError(
                    f"Invalid app_name extracted: '{result.app_name}'. " 
                    "Please mention a specific web application in your question."
                )
            
            if not result.app_url or not result.app_url.startswith(('https://')): 
                raise ValueError(
                    f"Invalid app_url extracted: '{result.app_url}'. "  
                    "Could not determine the application URL."
                )
            
            if not result.task or len(result.task.strip()) < 3: 
                raise ValueError(
                    f"Invalid task extracted: '{result.task}'. "
                    "Please describe what you want to do in the application."
                )
            
            # Convert the Pydantic schema to our ParsedQuestion class
            # The result is guaranteed to be a ParsedQuestionSchema due to with_structured_output()
            return ParsedQuestion(
                app_name=result.app_name,  
                app_url=result.app_url,  
                task=result.task,  
                task_name=result.task_name,  
                optimized_description=result.optimized_description,  
                auth_required=result.auth_required,  
                confidence=0.95,  # High confidence for successful structured output
                raw_question=question,
            )
            
        except ValueError:
            # Re-raise ValueError with our custom message
            raise
        except Exception as e:
            logger.error(f"❌ LLM parsing failed: {e}")
            raise ValueError(f"Question parsing failed: {e}")
    
    def clear_cache(self) -> None:
        """Clear the parsing cache."""
        self._cache.clear()
        logger.info("🗑️ Cache cleared")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            'enabled': self.enable_cache,
            'size': len(self._cache),
            'questions': list(self._cache.keys()),
        }


# Example usage and testing
async def test_parser_agent():
    """Test the Question Parser Agent with various questions."""
    print("\n" + "="*60)
    print("🧪 TESTING QUESTION PARSER AGENT")
    print("="*60 + "\n")
    
    parser = QuestionParserAgent()
    
    # Valid test questions
    test_questions = [
        "How do I create a project in Linear?",
        "Show me how to filter issues by priority in Linear with status 'Done'",
        "How can I create a database in Notion?",
        "How do I star a repository on GitHub?",
        "Create a new task in Asana with high priority",
        "Get me number of stars on GitHub project torvalds/linux",
        "Get me price of Nvidia stock from Yahoo Finance",

    ]
    
    # Invalid test questions (should throw errors)
    invalid_questions = [
        "What's the weather today?",
        "Tell me a joke",
        "How are you?",
        "Random text without meaning",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_questions)}")
        print(f"{'='*60}")
        print(f"Question: {question}\n")
        
        try:
            result = await parser.parse(question)
            
            print(f"✅ Parsing successful:")
            print(f"   App Name:   {result.app_name}")
            print(f"   App URL:    {result.app_url}")
            print(f"   Task:       {result.task}")
            print(f"   Task Name:  {result.task_name}")
            print(f"   Optimized:  {result.optimized_description}")
            print(f"   Auth Req:   {'Yes 🔐' if result.auth_required else 'No 🌐'}")
            print(f"   Confidence: {result.confidence:.2%}")
            print(f"   Valid:      {result.is_valid()}")
            
        except Exception as e:
            print(f"❌ Parsing failed: {e}")
    
    # Test invalid questions (should fail gracefully)
    print(f"\n{'='*60}")
    print("🧪 TESTING INVALID QUESTIONS (Expected to fail)")
    print("="*60 + "\n")
    
    for i, question in enumerate(invalid_questions, 1):
        print(f"\n{'='*60}")
        print(f"Invalid Test {i}/{len(invalid_questions)}")
        print(f"{'='*60}")
        print(f"Question: {question}\n")
        
        try:
            result = await parser.parse(question)
            print(f"⚠️ WARNING: Should have failed but succeeded!")
            print(f"   Got: {result.to_dict()}")
            
        except ValueError as e:
            print(f"✅ Correctly rejected invalid question:")
            print(f"   Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ ALL TESTS COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configure logging 
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    asyncio.run(test_parser_agent())
