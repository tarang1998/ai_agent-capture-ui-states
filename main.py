"""
Main Entry Point for AI Multi-Agent UI State Capture System

This module provides an interactive CLI for running workflow capture tasks
across Linear, Notion, and Asana applications.
"""

import asyncio
import logging
import sys

from task_definitions import (
    ASANA_TASKS,
    LINEAR_TASKS,
    run_asana_tasks,
    run_linear_tasks,
)
from agent_a_interface import AgentAInterface


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('workflow_captures.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_header():
    """Print application header."""
    print("\n" + "="*70)
    print("🤖 AI MULTI-AGENT UI STATE CAPTURE SYSTEM")
    print("="*70)
    print("\nThis system demonstrates Agent B's ability to capture UI states")
    print("for any task across different web applications")
    print("="*70 + "\n")


def print_task_summary():
    """Print summary of available tasks."""
    print("📊 AVAILABLE TASKS:")
    print(f"  • Linear: {len(LINEAR_TASKS)} tasks")
    print(f"  • Asana: {len(ASANA_TASKS)} tasks")
    print(f"  • Total: {len(LINEAR_TASKS) + len(ASANA_TASKS)} tasks")
    print()


def print_menu():
    """Print interactive menu."""
    print("🎯 SELECT EXECUTION MODE:\n")
    print("  1. Run specific Linear tasks (custom selection)")
    print("  2. Run specific Asana tasks (custom selection)")
    print("  3. Enter a custom task")
    print("  0. Exit")
    print()


def print_task_list(tasks: list, app_name: str):
    """Print list of tasks for selection."""
    print(f"\n📋 {app_name.upper()} TASKS:\n")
    for i, task_description in enumerate(tasks, 1):
        print(f"  {i}. {task_description}")
        print()


async def run_custom_tasks(app_name: str, all_tasks: list, run_function):
    """Run custom selected tasks for an application."""
    print_task_list(all_tasks, app_name)
    print("Enter task numbers to run (comma-separated, e.g., 1,2,3):")
    print("Or press Enter to run all tasks")
    
    selection = input("Your selection: ").strip()
    
    if not selection:
        # Run all tasks
        await run_function(headless=False, max_steps=30)
    else:
        # Parse selection
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]  # Convert to 0-based indices
            valid_indices = [idx for idx in indices if 0 <= idx < len(all_tasks)]
            
            if valid_indices:
                print(f"\n✅ Running {len(valid_indices)} selected tasks...")
                await run_function(tasks=valid_indices, headless=False, max_steps=30)
            else:
                print("❌ Invalid selection")
        except (ValueError, IndexError):
            print("❌ Invalid input format")


async def run_custom_task():
    """Run a custom user-defined task."""
    print("\n" + "="*70)
    print("✏️  CUSTOM TASK ENTRY")
    print("="*70)
    print("\nEnter your custom task description:")
    print("(The task should include the application name and detailed instructions)")
    print("\nExample: Create a new project in Linear with name 'MyProject', priority 'High'")
    print()
    
    task_description = input("Task: ").strip()
    
    if not task_description:
        print("❌ Task description cannot be empty")
        return
    
    print(f"\n✅ Running custom task...")
    print(f"Description: {task_description}\n")
    
    # Initialize Agent A interface
    interface = AgentAInterface(
        output_dir="dataset",
        headless=False,
    )
    
    try:
        result = await interface.ask(task_description, max_steps=30)
        
        success = result['metadata']['success']
        steps_captured = len(result['steps'])
        
        print(f"\n{'='*70}")
        print(f"✅ CUSTOM TASK COMPLETED")
        print(f"{'='*70}")
        print(f"Success: {'✅ Yes' if success else '❌ No'}")
        print(f"Steps Captured: {steps_captured}")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Task failed: {e}")
    finally:
        await interface.close()


async def main():
    """Main entry point with interactive CLI."""
    setup_logging()
    print_header()
    print_task_summary()
    
    while True:
        print_menu()
        choice = input("Enter your choice (0-3): ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
            
        elif choice == '1':
            await run_custom_tasks("Linear", LINEAR_TASKS, run_linear_tasks)
            
        elif choice == '2':
            await run_custom_tasks("Asana", ASANA_TASKS, run_asana_tasks)
            
        elif choice == '3':
            await run_custom_task()
            
        else:
            print("❌ Invalid choice. Please enter 0-3.")
        
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
