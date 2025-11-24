"""
Task Definitions for Multi-Agent UI State Capture System

This module contains detailed task definitions for Linear, Notion, and Asana.
"""

import asyncio
import logging
from typing import Dict, List

from agent_a_interface import AgentAInterface

logger = logging.getLogger(__name__)


# ============================================================================
# LINEAR TASKS
# ============================================================================

LINEAR_TASKS = [
    "Create a new project in Linear with name 'Galactus', priority 'High', set start date to today, and target date to 2 weeks from now. Add summary 'Project management system for cosmic scale applications'",
    "Create a new issue in Linear with title 'Implement authentication system', add description 'Need to add OAuth2 support', set priority to 'Urgent',assign project as 'Galactus' and status as 'In Progress'",
    "Create a new issue in Linear with title 'Fix data synchronization bug', add description 'Investigate and resolve data sync issues between services', set priority to 'High', assign project as 'Galactus' and status as 'TODO'",
    "Navigate to Linear issues page and filter issues by status 'In Progress'",
]


# ============================================================================
# ASANA TASKS
# ============================================================================

ASANA_TASKS = [
    "Create a new project in Asana named 'Website Redesign' with layout 'List', add description 'Complete redesign of company website with modern UI/UX', and add 3 tasks: 'Design mockups', 'Frontend implementation', and 'QA testing' ",
    "Create a new task in Asana with title 'Implement dark mode feature', add description 'Add dark mode toggle to user settings with persistent preference storage', and add it to the 'Website Redesign' project",
    "Find the task 'Frontend implementation' under project 'Website Redesign' in Asana and add 3 subtasks: 'Setup React components', 'Implement responsive layouts', and 'Add animations and transitions'",
    "In the 'Website Redesign' project in Asana, move the task 'Design mockups' from 'To Do' section to 'In Progress' section, then add a comment 'Started working on initial wireframes'",
]


# ============================================================================
# TASK EXECUTION FUNCTIONS
# ============================================================================

async def run_linear_tasks(
    tasks: List[int] | None = None,
    headless: bool = False,
    max_steps: int = 30,
) -> Dict[int, dict]:
    """
    Execute Linear workflow tasks and capture UI states.
        
    Args:
        tasks: List of task indices to run (0-based). If None, runs all tasks.
        headless: Whether to run browser in headless mode
        max_steps: Maximum steps per workflow
        
    Returns:
        Dictionary mapping task indices to their captured workflows
        
    Example:
        results = await run_linear_tasks(
            tasks=[0, 1, 2],  # Run first 3 tasks
            headless=False,
            max_steps=30
        )
    """
    logger.info("\n" + "="*70)
    logger.info("🚀 STARTING LINEAR WORKFLOW CAPTURES")
    logger.info("="*70)
    
    # Initialize Agent A interface
    interface = AgentAInterface(
        output_dir="dataset",
        headless=headless,
    )
    
    # Determine which tasks to run
    task_indices = tasks or list(range(len(LINEAR_TASKS)))
    results = {}
    
    try:
        for i, task_idx in enumerate(task_indices, 1):
            if task_idx < 0 or task_idx >= len(LINEAR_TASKS):
                logger.warning(f"⚠️ Invalid task index: {task_idx}, skipping...")
                continue
            
            task_description = LINEAR_TASKS[task_idx]
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📋 LINEAR TASK {i}/{len(task_indices)} (Index: {task_idx})")
            logger.info(f"{'='*70}")
            logger.info(f"Description: {task_description}")
            logger.info(f"{'='*70}\n")
            
            try:
                # Capture workflow
                result = await interface.ask(task_description, max_steps=max_steps)
                results[task_idx] = result
                
                # Log success
                success = result['metadata']['success']
                steps_captured = len(result['steps'])
                logger.info(f"\n{'='*70}")
                logger.info(f"✅ TASK COMPLETED (Index: {task_idx})")
                logger.info(f"{'='*70}")
                logger.info(f"Success: {'✅ Yes' if success else '❌ No'}")
                logger.info(f"Steps Captured: {steps_captured}")
                logger.info(f"{'='*70}\n")
                
            except Exception as e:
                logger.error(f"❌ Task failed (Index: {task_idx})")
                logger.error(f"Error: {e}")
                results[task_idx] = {"error": str(e)}
        
        return results
        
    finally:
        await interface.close()


async def run_asana_tasks(
    tasks: List[int] | None = None,
    headless: bool = False,
    max_steps: int = 30,
) -> Dict[int, dict]:
    """
    Execute Asana workflow tasks and capture UI states.
        
    Args:
        tasks: List of task indices to run (0-based). If None, runs all tasks.
        headless: Whether to run browser in headless mode
        max_steps: Maximum steps per workflow
        
    Returns:
        Dictionary mapping task indices to their captured workflows
        
    Example:
        results = await run_asana_tasks(
            tasks=[0, 1, 2],  # Run first 3 tasks
            headless=False,
            max_steps=30
        )
    """
    logger.info("\n" + "="*70)
    logger.info("✅ STARTING ASANA WORKFLOW CAPTURES")
    logger.info("="*70)
    
    interface = AgentAInterface(
        output_dir="dataset",
        headless=headless,
    )
    
    task_indices = tasks or list(range(len(ASANA_TASKS)))
    results = {}
    
    try:
        for i, task_idx in enumerate(task_indices, 1):
            if task_idx < 0 or task_idx >= len(ASANA_TASKS):
                logger.warning(f"⚠️ Invalid task index: {task_idx}, skipping...")
                continue
            
            task_description = ASANA_TASKS[task_idx]
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📋 ASANA TASK {i}/{len(task_indices)} (Index: {task_idx})")
            logger.info(f"{'='*70}")
            logger.info(f"Description: {task_description}")
            logger.info(f"{'='*70}\n")
            
            try:
                result = await interface.ask(task_description, max_steps=max_steps)
                results[task_idx] = result
                
                success = result['metadata']['success']
                steps_captured = len(result['steps'])
                logger.info(f"\n{'='*70}")
                logger.info(f"✅ TASK COMPLETED (Index: {task_idx})")
                logger.info(f"{'='*70}")
                logger.info(f"Success: {'✅ Yes' if success else '❌ No'}")
                logger.info(f"Steps Captured: {steps_captured}")
                logger.info(f"{'='*70}\n")
                
            except Exception as e:
                logger.error(f"❌ Task failed (Index: {task_idx})")
                logger.error(f"Error: {e}")
                results[task_idx] = {"error": str(e)}
        
        return results
        
    finally:
        await interface.close()


