#!/usr/bin/env python3
import os
import sys
import time
from threading import Thread
import logging
import json
import argparse
from datetime import datetime
import platform

# Import custom modules
from config import load_config, get_default_config, save_config
from core import CursorFocusCore
from ui import (
    # Rich UI elements
    console, create_title_panel, display_menu, display_custom_progress,
    input_with_default, confirm_action, success_message, error_message,
    warning_message, info_message, wait_for_key, display_project_list,
    display_monitoring_screen, display_scanning_results, display_update_info,
    # Legacy compatibility
    clear_screen, Colors, print_header, print_centered
)
from rich.panel import Panel
from dotenv import load_dotenv
from rich.table import Table

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING, format=f'{Colors.WARNING}%(levelname)s{Colors.RESET}: %(message)s')

def check_and_setup_api_key():
    """Check and set up Gemini API key."""
    if not os.environ.get("GEMINI_API_KEY"):
        warning_message("Gemini API Key is not set")
        api_key = input_with_default("Please enter your API key (get key at https://makersuite.google.com/app/apikey)")
        
        if api_key.strip():
            if CursorFocusCore.setup_gemini_api_key(api_key):
                success_message("API key has been saved")
                return True
            else:
                error_message("Failed to save API key")
                return False
        else:
            error_message("Invalid API key")
            return False
    return True

def setup_new_project_menu():
    """Menu for setting up a new project."""
    clear_screen()
    console.print(create_title_panel("SETUP NEW PROJECT"))
    
    # Request project path
    project_path = input_with_default("Enter project path")
    if not project_path:
        error_message("Project path cannot be empty")
        wait_for_key()
        return
    
    # Check if path exists
    if not os.path.exists(project_path):
        error_message(f"Path does not exist: {project_path}")
        wait_for_key()
        return
    
    # Request project name (optional)
    dir_name = os.path.basename(os.path.normpath(project_path))
    project_name = input_with_default(f"Enter project name", dir_name)
    
    # Request API key if needed
    if not check_and_setup_api_key():
        wait_for_key()
        return
    
    # Advanced options
    use_advanced = confirm_action("Configure advanced options?")
    
    update_interval = 60
    max_depth = 3
    
    if use_advanced:
        console.print("\n[bold]Advanced Options:[/]")
        
        # Update interval
        interval_input = input_with_default("Enter update interval in seconds", "60")
        try:
            if interval_input:
                update_interval = max(10, int(interval_input))
        except ValueError:
            warning_message("Invalid input, using default value")
        
        # Max depth
        depth_input = input_with_default("Enter maximum directory depth to scan", "3")
        try:
            if depth_input:
                max_depth = max(1, int(depth_input))
        except ValueError:
            warning_message("Invalid input, using default value")
    
    info_message(f"Setting up for project: {project_name}")
    
    # Display progress bar for visualization
    display_custom_progress("Analyzing project", 100, 0.02)
    
    # Setup the project
    success, message = CursorFocusCore.setup_project(
        project_path, project_name, update_interval, max_depth
    )
    
    if success:
        success_message(message)
    else:
        error_message(message)
    
    wait_for_key()

def scan_for_projects_menu():
    """Menu for scanning and finding projects."""
    clear_screen()
    console.print(create_title_panel("SCAN FOR PROJECTS"))
    
    # Request scan path
    scan_path = input_with_default("Enter path to scan", os.getcwd())
    
    # Handle Windows paths by normalizing
    scan_path = os.path.normpath(scan_path)
    
    # Check if path exists
    if not os.path.exists(scan_path):
        error_message(f"Path does not exist: {scan_path}")
        wait_for_key()
        return
    
    # Scan depth
    depth_input = input_with_default("Enter scan depth", "3")
    try:
        max_depth = int(depth_input) if depth_input else 3
    except ValueError:
        warning_message("Invalid input, using default value")
        max_depth = 3
    
    info_message(f"Scanning: {scan_path}")
    
    # Display progress bar
    display_custom_progress("Scanning directories", 100, 0.02)
    
    # Scan for projects
    found_projects = CursorFocusCore.find_projects(scan_path, max_depth)
    
    if not found_projects:
        error_message("No projects found")
        wait_for_key()
        return
    
    # Display results using the modern UI
    display_scanning_results(found_projects)
    
    # Project selection
    selection = input_with_default("Select projects to add (enter numbers/all/q)")
    if selection in ['q', 'quit', 'exit']:
        return
    
    # Load config
    config = load_config()
    if not config:
        config = get_default_config()
    
    if 'projects' not in config:
        config['projects'] = []
    
    # Process selection
    if selection == 'all':
        indices = range(len(found_projects))
    else:
        try:
            indices = [int(i) - 1 for i in selection.split()]
            if any(i < 0 or i >= len(found_projects) for i in indices):
                error_message("Invalid number")
                wait_for_key()
                return
        except ValueError:
            error_message("Invalid input")
            wait_for_key()
            return
    
    # Request API key if needed
    if not check_and_setup_api_key():
        wait_for_key()
        return
    
    # Add projects
    added = 0
    total = len(indices)
    
    for idx_pos, idx in enumerate(indices):
        project = found_projects[idx]
        project_path = project['path']
        
        # Show progress
        info_message(f"Processing {idx_pos+1}/{total}: {project['name']}")
        
        # Check if project already exists
        if not any(p['project_path'] == project_path for p in config['projects']):
            # Display progress bar
            display_custom_progress(f"Setting up {project['name']}", 100, 0.01)
            
            # Setup project
            success, _ = CursorFocusCore.setup_project(
                project_path, project['name'], 60, 3
            )
            
            if success:
                added += 1
                success_message(f"Added: {project['name']}")
            else:
                error_message(f"Failed to add: {project['name']}")
        else:
            info_message(f"Project already exists: {project['name']}")
    
    # Final message
    if added > 0:
        success_message(f"Added {added} projects")
    else:
        warning_message("No projects added")
    
    wait_for_key()

def list_projects_menu():
    """Display the list of projects."""
    # Load config
    config = load_config()
    if not config or 'projects' not in config or not config['projects']:
        warning_message("No projects configured")
        wait_for_key()
        return
    
    # Display project list using the modern UI
    display_project_list(config['projects'], "PROJECT LIST")
    
    wait_for_key()

def edit_project_menu():
    """Menu for editing project settings."""
    clear_screen()
    console.print(create_title_panel("EDIT PROJECT"))
    
    # Load config
    config = load_config()
    if not config or 'projects' not in config or not config['projects']:
        warning_message("No projects configured")
        wait_for_key()
        return
    
    # Display list using the modern UI
    display_project_list(config['projects'], "Select a project to edit")
    
    # Project selection
    selection = input_with_default("Enter project number or q to cancel")
    if selection in ['q', 'quit', 'exit']:
        return
    
    try:
        idx = int(selection) - 1
        if idx < 0 or idx >= len(config['projects']):
            error_message("Invalid project number")
            wait_for_key()
            return
        
        project = config['projects'][idx]
        
        console.print(f"\n[bold]Editing project:[/] [cyan]{project['name']}[/]")
        
        # Edit name
        new_name = input_with_default("Enter new name", project['name'])
        
        # Edit path
        new_path = input_with_default("Enter new path", project['project_path'])
        if new_path != project['project_path']:
            if not os.path.exists(new_path):
                warning_message(f"Warning: Path does not exist: {new_path}")
                if not confirm_action("Use this path anyway?"):
                    new_path = project['project_path']
        
        # Edit update interval
        interval_str = input_with_default("Enter new update interval in seconds", str(project['update_interval']))
        try:
            new_interval = max(10, int(interval_str))
        except ValueError:
            warning_message("Invalid value, keeping current setting")
            new_interval = None
        
        # Edit max depth
        depth_str = input_with_default("Enter new max depth", str(project['max_depth']))
        try:
            new_depth = max(1, int(depth_str))
        except ValueError:
            warning_message("Invalid value, keeping current setting")
            new_depth = None
        
        # Update the project
        success, message = CursorFocusCore.update_project_settings(
            idx, new_name, new_path, new_interval, new_depth
        )
        
        if success:
            success_message(message)
        else:
            error_message(message)
        
    except Exception as e:
        error_message(f"Error updating project: {str(e)}")
    
    wait_for_key()

def remove_project_menu():
    """Menu for removing projects."""
    clear_screen()
    console.print(create_title_panel("REMOVE PROJECT"))
    
    # Load config
    config = load_config()
    if not config or 'projects' not in config or not config['projects']:
        warning_message("No projects configured")
        wait_for_key()
        return
    
    # Display project list
    display_project_list(config['projects'])
    
    # Project selection
    selection = input_with_default("Select project to remove (enter numbers/all/q)")
    if selection in ['q', 'quit', 'exit']:
        return
    
    # Process selection
    if selection == 'all':
        # Confirm removing all
        if confirm_action("Are you sure you want to remove ALL projects?"):
            success, message = CursorFocusCore.remove_projects(remove_all=True)
            if success:
                success_message(message)
            else:
                error_message(message)
        else:
            warning_message("Cancelled")
    else:
        try:
            indices = [int(i) - 1 for i in selection.split()]
            if any(i < 0 or i >= len(config['projects']) for i in indices):
                error_message("Invalid number")
                wait_for_key()
                return
            
            # Remove selected projects
            success, message = CursorFocusCore.remove_projects(indices=indices)
            if success:
                success_message(message)
            else:
                error_message(message)
            
        except ValueError:
            error_message("Invalid input")
    
    wait_for_key()

def batch_update_menu():
    """Menu for batch updating multiple project files."""
    clear_screen()
    console.print(create_title_panel("BATCH UPDATE"))
    
    # Load config
    config = load_config()
    if not config or 'projects' not in config or not config['projects']:
        warning_message("No projects configured")
        wait_for_key()
        return
    
    # Get valid projects
    valid_projects = [p for p in config['projects'] if os.path.exists(p['project_path'])]
    
    if not valid_projects:
        error_message("No valid projects found")
        wait_for_key()
        return
    
    # Display project list
    display_project_list(valid_projects, "Projects available for update")
    
    # Project selection
    selection = input_with_default("Select projects to update (enter numbers/all/q)")
    if selection in ['q', 'quit', 'exit']:
        return
    
    # Process selection
    projects_to_update = []
    if selection == 'all':
        projects_to_update = valid_projects
    else:
        try:
            indices = [int(i) - 1 for i in selection.split()]
            if any(i < 0 or i >= len(valid_projects) for i in indices):
                error_message("Invalid number")
                wait_for_key()
                return
            
            projects_to_update = [valid_projects[i] for i in indices]
            
        except ValueError:
            error_message("Invalid input")
            wait_for_key()
            return
    
    if not projects_to_update:
        warning_message("No projects selected")
        wait_for_key()
        return
    
    # Request API key if needed
    if not check_and_setup_api_key():
        wait_for_key()
        return
    
    # Define a progress callback to show progress in UI
    def update_progress(current, total, name, stage):
        stage_text = "Setting up" if stage == "setup" else "Generating Focus.md"
        console.print(f"[blue]Updating {current}/{total}: [cyan]{name}[/] - {stage_text}")
    
    # Update projects
    success_count, total, errors = CursorFocusCore.batch_update_projects(
        projects_to_update, update_progress
    )
    
    # Show errors if any
    if errors:
        console.print("\n[bold red]Errors:[/]")
        for project_name, error_msg in errors:
            console.print(f"[red]❌ {project_name}:[/] {error_msg}")
    
    console.print(f"\n[bold green]✓ Successfully updated {success_count}/{total} projects[/]")
    
    wait_for_key()

def monitoring_progress_callback(project_name, status):
    """Callback for monitoring progress updates."""
    console.print(f"[blue]📡 {project_name}:[/] {status}")

def monitoring_error_callback(project_name, error):
    """Callback for monitoring errors."""
    console.print(f"[red]❌ {project_name}:[/] {error}")

def start_monitoring():
    """Start monitoring projects."""
    clear_screen()
    console.print(create_title_panel("START MONITORING"))
    
    # Load config
    config = load_config()
    if not config or 'projects' not in config or not config['projects']:
        warning_message("No projects configured")
        wait_for_key()
        return
    
    # Check for updates
    info_message("Checking for updates...")
    display_custom_progress("Checking for updates", 100, 0.01)
    
    update_info = CursorFocusCore.check_for_updates()
    
    if update_info:
        if display_update_info(update_info):
            display_custom_progress("Downloading update", 100, 0.05)
            
            if CursorFocusCore.apply_update(update_info):
                success_message("Updated! Please restart the application")
                wait_for_key()
                return
            else:
                error_message("Update failed")
    
    # Get valid projects
    valid_projects = [p for p in config['projects'] if os.path.exists(p['project_path'])]
    
    if not valid_projects:
        error_message("No valid projects to monitor")
        wait_for_key()
        return
    
    # Display project list
    display_project_list(valid_projects, "Projects to monitor")
    
    # Advanced options
    use_advanced = confirm_action("Configure monitoring options?")
    
    monitor_all = True
    selected_projects = valid_projects
    auto_update = False
    
    if use_advanced:
        # Project selection
        monitor_all = confirm_action("Monitor all projects?")
        
        if not monitor_all:
            selection = input_with_default("Select projects to monitor (enter numbers)")
            try:
                indices = [int(i) - 1 for i in selection.split()]
                if any(i < 0 or i >= len(valid_projects) for i in indices):
                    error_message("Invalid number, monitoring all projects")
                else:
                    selected_projects = [valid_projects[i] for i in indices]
            except ValueError:
                warning_message("Invalid input, monitoring all projects")
        
        # Auto-update option
        auto_update = confirm_action("Automatically update rules on changes?")
    
    # Confirmation
    if not confirm_action(f"Start monitoring {len(selected_projects)} projects?"):
        return
    
    # Request API key if needed
    if not check_and_setup_api_key():
        wait_for_key()
        return
    
    # Start monitoring
    try:
        # Setup and start monitoring
        info_message("Preparing projects for monitoring...")
        
        for project in selected_projects:
            info_message(f"Setting up: {project['name']}")
            CursorFocusCore.setup_project(project['project_path'], project['name'])
        
        threads, watchers = CursorFocusCore.start_monitoring(
            selected_projects, 
            auto_update=auto_update,
            on_update_callback=monitoring_progress_callback,
            on_error_callback=monitoring_error_callback
        )
        
        if auto_update:
            info_message("Automatic rule updates enabled for file changes")
        
        success_message(f"Monitoring {len(threads)} projects (Ctrl+C to stop)")
        
        # Create a monitoring screen
        layout = display_monitoring_screen(len(threads))
        
        try:
            with console.status("[cyan]Press Ctrl+C to stop monitoring[/]"):
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            console.print("[green]👋 Stopped monitoring![/]")
            
    except KeyboardInterrupt:
        console.print("[green]👋 Stopped monitoring![/]")
    except Exception as e:
        error_message(f"Error: {str(e)}")
    
    wait_for_key()

def check_updates_menu():
    """Check for and install updates."""
    clear_screen()
    console.print(create_title_panel("CHECK FOR UPDATES"))
    
    # Get current version from config
    config = load_config()
    current_version = config.get('version', '1.0.0')
    
    # Display current version and system info
    console.print(f"\n[bold]Current version:[/] [cyan]{current_version}[/]")
    system = platform.system()
    machine = platform.machine()
    console.print(f"[bold]System:[/] [cyan]{system} {machine}[/]")
    
    info_message("Checking for updates...")
    display_custom_progress("Checking", 100, 0.02)
    
    update_info = CursorFocusCore.check_for_updates()
    
    if update_info:
        # Use display_update_info to handle the update process
        if display_update_info(update_info):
            display_custom_progress("Downloading update", 100, 0.05)
            
            if CursorFocusCore.apply_update(update_info):
                success_message("Update successful! Please restart the application")
                # Update version in config
                config['version'] = update_info['version']
                save_config(config)
            else:
                error_message("Update failed")
    else:
        success_message("You are using the latest version")
    
    wait_for_key()

def settings_menu():
    """Application settings menu."""
    clear_screen()
    console.print(create_title_panel("SETTINGS"))
    
    # Load config
    config = load_config()
    if not config:
        config = get_default_config()
    
    # Display current settings
    console.print("[bold]Current settings:[/]")
    
    # Display ignored directories
    console.print("\n[bold cyan]Ignored directories:[/]")
    for i, dir_name in enumerate(config.get('ignored_directories', []), 1):
        console.print(f"  {i}. [blue]{dir_name}[/]")
    
    # Display ignored files
    console.print("\n[bold cyan]Ignored files:[/]")
    for i, file_pattern in enumerate(config.get('ignored_files', []), 1):
        console.print(f"  {i}. [blue]{file_pattern}[/]")
    
    # Settings options
    options = [
        ("1", "Add ignored directory", "Add a directory name to the ignore list"),
        ("2", "Remove ignored directory", "Remove a directory from the ignore list"),
        ("3", "Add ignored file pattern", "Add a file pattern to the ignore list"),
        ("4", "Remove ignored file pattern", "Remove a file pattern from the ignore list"),
        ("5", "Configure auto-updater", "Set options for automatic updates"),
        ("6", "Reset to defaults", "Reset settings to default values"),
        ("0", "Back to main menu", "Return to the main menu")
    ]
    
    # Display options
    console.print("\n[bold]Options:[/]")
    for number, text, description in options:
        console.print(f"[cyan]{number}.[/] [white]{text}[/] - [dim]{description}[/]")
    
    choice = input_with_default("Enter your choice (0-6)")
    
    if choice == '1':
        # Add ignored directory
        dir_name = input_with_default("Enter directory name to ignore")
        if dir_name:
            if 'ignored_directories' not in config:
                config['ignored_directories'] = []
            if dir_name not in config['ignored_directories']:
                config['ignored_directories'].append(dir_name)
                save_config(config)
                success_message(f"Added ignored directory: {dir_name}")
            else:
                warning_message(f"Directory already in ignore list: {dir_name}")
        else:
            error_message("Directory name cannot be empty")
    
    elif choice == '2':
        # Remove ignored directory
        if not config.get('ignored_directories'):
            warning_message("No ignored directories to remove")
        else:
            try:
                idx = int(input_with_default("Enter number of directory to remove")) - 1
                if 0 <= idx < len(config['ignored_directories']):
                    removed = config['ignored_directories'].pop(idx)
                    save_config(config)
                    success_message(f"Removed ignored directory: {removed}")
                else:
                    error_message("Invalid number")
            except ValueError:
                error_message("Invalid input")
    
    elif choice == '3':
        # Add ignored file pattern
        file_pattern = input_with_default("Enter file pattern to ignore (e.g., *.log)")
        if file_pattern:
            if 'ignored_files' not in config:
                config['ignored_files'] = []
            if file_pattern not in config['ignored_files']:
                config['ignored_files'].append(file_pattern)
                save_config(config)
                success_message(f"Added ignored file pattern: {file_pattern}")
            else:
                warning_message(f"Pattern already in ignore list: {file_pattern}")
        else:
            error_message("File pattern cannot be empty")
    
    elif choice == '4':
        # Remove ignored file pattern
        if not config.get('ignored_files'):
            warning_message("No ignored file patterns to remove")
        else:
            try:
                idx = int(input_with_default("Enter number of file pattern to remove")) - 1
                if 0 <= idx < len(config['ignored_files']):
                    removed = config['ignored_files'].pop(idx)
                    save_config(config)
                    success_message(f"Removed ignored file pattern: {removed}")
                else:
                    error_message("Invalid number")
            except ValueError:
                error_message("Invalid input")
    
    elif choice == '5':
        # Configure auto-updater
        clear_screen()
        console.print(create_title_panel("AUTO-UPDATER SETTINGS"))
        
        from core import CursorFocusCore
        
        # Get updater settings from new instance to show current settings
        # Default values from AutoUpdater
        max_retries_default = 3
        retry_delay_default = 2
        keep_backups_default = False
        
        console.print("\n[bold]Current Auto-Updater Settings:[/]")
        console.print(f"  [cyan]Max retries:[/] {max_retries_default}")
        console.print(f"  [cyan]Retry delay:[/] {retry_delay_default} seconds")
        console.print(f"  [cyan]Keep backups:[/] {'Yes' if keep_backups_default else 'No'}")
        
        console.print("\n[bold]Configure Settings:[/]")
        
        # Max retries
        max_retries_input = input_with_default("Enter maximum retry attempts (3-10)", str(max_retries_default))
        try:
            max_retries = int(max_retries_input) if max_retries_input else max_retries_default
            max_retries = max(3, min(10, max_retries))  # Clamp between 3-10
        except ValueError:
            warning_message("Invalid input, using default value")
            max_retries = max_retries_default
        
        # Retry delay
        retry_delay_input = input_with_default("Enter retry delay in seconds (1-10)", str(retry_delay_default))
        try:
            retry_delay = int(retry_delay_input) if retry_delay_input else retry_delay_default
            retry_delay = max(1, min(10, retry_delay))  # Clamp between 1-10
        except ValueError:
            warning_message("Invalid input, using default value")
            retry_delay = retry_delay_default
        
        # Keep backups
        keep_backups = confirm_action("Keep backups after successful updates?")
        
        # Save settings
        CursorFocusCore.configure_updater(max_retries, retry_delay, keep_backups)
        success_message("Auto-updater settings saved")
    
    elif choice == '6':
        # Reset to defaults
        if confirm_action("Are you sure you want to reset settings to defaults?"):
            default_config = get_default_config()
            config['ignored_directories'] = default_config.get('ignored_directories', [])
            config['ignored_files'] = default_config.get('ignored_files', [])
            save_config(config)
            success_message("Settings reset to defaults")
    
    wait_for_key()

def about_menu():
    """Display information about the application."""
    clear_screen()
    console.print(create_title_panel("ABOUT CURSORFOCUS"))
    
    # Get current version and system info
    config = load_config()
    current_version = config.get('version', '1.0.0')
    system = platform.system()
    machine = platform.machine()
    
    about_text = f"""
    [bold cyan]CursorFocus[/] is a tool that automatically analyzes software
    codebases to generate dynamic context files specifically tailored
    for enhancing the [bold]Cursor AI IDE's[/] understanding and code
    generation capabilities.

    [bold]Version:[/] [blue]{current_version}[/]
    [bold]System:[/] [blue]{system} {machine}[/]
    [bold]License:[/] GPL-3.0

    [bold]Features:[/]
    • Automatic project analysis and detection
    • Generation of [magenta].cursorrules[/] and [magenta]Focus.md[/] files
    • Real-time monitoring of project changes
    • Integration with [blue]Google Gemini AI[/] for enhanced context generation
    """
    
    console.print(Panel(about_text, border_style="cyan", padding=(1, 2)))
    
    wait_for_key()

def gemini_settings_menu():
    """Unified menu for managing Gemini API key and model settings."""
    clear_screen()
    console.print(create_title_panel("GEMINI AI SETTINGS"))
    
    # Check current API key status
    current_key = os.environ.get("GEMINI_API_KEY", "")
    has_api_key = bool(current_key.strip())
    
    # Get current model
    current_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro-exp-03-25")
    
    # Display current settings
    api_status = Panel(
        f"[bold]API Key Status:[/] [{'green' if has_api_key else 'red'}]{'✓ Configured' if has_api_key else '✗ Not Configured'}[/]\n"
        f"[bold]Current Model:[/] [cyan]{current_model}[/]",
        title="Current Settings",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(api_status)
    
    # Display configuration options
    options = [
        ("1", "Configure API Key", "Set up or change your Gemini API key"),
        ("2", "Select Gemini Model", "Choose which Gemini AI model to use"),
        ("3", "Test Connection", "Verify your API key and model configuration"),
        ("0", "Back to main menu", "Return to the main menu")
    ]
    
    # Display options as a table
    table = Table(show_header=False, box=None, padding=(0, 2), title="Options")
    table.add_column("Number", style="cyan")
    table.add_column("Option", style="white")
    table.add_column("Description", style="dim")
    
    for number, text, description in options:
        table.add_row(f"[bold]{number}[/]", text, description)
    
    console.print(table)
    
    # Get user choice
    choice = input_with_default("Enter your choice (0-3)")
    
    if choice == '1':
        # Configure API Key
        if has_api_key:
            masked_key = f"{current_key[:5]}...{current_key[-5:]}" if len(current_key) > 10 else "********"
            console.print(f"\n[blue]Current key:[/] [magenta]{masked_key}[/]")
            
            if not confirm_action("Do you want to change the API key?"):
                wait_for_key()
                return
        
        # Show API key instructions
        console.print(Panel(
            "To get your API key:\n"
            "1. Visit [link=https://makersuite.google.com/app/apikey]https://makersuite.google.com/app/apikey[/link]\n"
            "2. Sign in with your Google account\n"
            "3. Create a new API key or copy an existing one",
            title="API Key Instructions",
            border_style="green",
            padding=(1, 2)
        ))
        
        api_key = input_with_default("Enter Gemini API key")
        
        if api_key.strip():
            if CursorFocusCore.setup_gemini_api_key(api_key):
                success_message("API key has been saved successfully")
                info_message("New API key will be used for future operations")
            else:
                error_message("Failed to save API key")
        else:
            error_message("Invalid API key")
        
    elif choice == '2':
        # Select Gemini Model
        if not has_api_key:
            error_message("API key is not set. Please configure your API key first.")
            wait_for_key()
            return
        
        # Show fetching message and progress
        info_message("Fetching available Gemini models...")
        display_custom_progress("Connecting to Gemini API", 100, 0.02)
        
        available_models = CursorFocusCore.fetch_gemini_models()
        
        if not available_models:
            error_message("Failed to fetch models. Please check your API key.")
            wait_for_key()
            return
        
        # Display available models in a table
        model_table = Table(title="Available Gemini Models", show_lines=True)
        model_table.add_column("#", style="cyan", justify="right")
        model_table.add_column("Model Name", style="white")
        model_table.add_column("Status", style="green")
        
        for i, model in enumerate(available_models, 1):
            is_current = model == current_model
            status = "[green]Current[/]" if is_current else ""
            model_table.add_row(str(i), model, status)
        
        console.print(model_table)
        
        # Get model selection
        selection = input_with_default("Select model number or enter custom model name")
        
        try:
            # Check if selection is a number
            if selection and selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(available_models):
                    selected_model = available_models[idx]
                else:
                    error_message("Invalid selection")
                    wait_for_key()
                    return
            # If not a number and not empty, use as custom model name
            elif selection:
                selected_model = selection.strip()
            else:
                warning_message("No selection made")
                wait_for_key()
                return
            
            # Display progress during model configuration
            display_custom_progress("Configuring model", 100, 0.01)
            
            # Set the model
            if CursorFocusCore.set_gemini_model(selected_model):
                success_message(f"Gemini model set to: {selected_model}")
            else:
                error_message("Failed to set model")
        except Exception as e:
            error_message(f"Error: {str(e)}")
    
    elif choice == '3':
        # Test Connection
        if not has_api_key:
            error_message("API key is not set. Please configure your API key first.")
            wait_for_key()
            return
        
        # Show testing message and progress bar
        info_message("Testing connection to Gemini AI...")
        display_custom_progress("Testing API connection", 100, 0.02)
        
        # Check if we can fetch models (simple test)
        if CursorFocusCore.fetch_gemini_models():
            success_message("Connection successful! Your Gemini AI configuration is working.")
        else:
            error_message("Connection failed. Please check your API key and try again.")
    
    wait_for_key()

def main_menu():
    """Display main menu and handle selection."""
    while True:
        # Get API key status
        has_api_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())
        api_status = ("Set", "green") if has_api_key else ("Not Set", "red")
        
        # Get Gemini model
        current_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro-exp-03-25")
        model_name = current_model.replace("gemini-", "").replace("-exp-03-25", "")
        
        # Get project count and version
        config = load_config()
        project_count = len(config.get('projects', [])) if config else 0
        current_version = config.get('version', '1.0.0')
        
        # Status info for the menu
        status = {
            "API Key": api_status,
            "Gemini Model": model_name,
            "Projects": project_count,
            "Version": current_version
        }
        
        # Define menu options with categories
        options = [
            "--- Project Management",
            ("1", "Setup new project", "Add a new project to monitor"),
            ("2", "Scan for projects", "Automatically detect projects in a directory"),
            ("3", "View project list", "See all configured projects"),
            ("4", "Edit project", "Modify an existing project's settings"),
            ("5", "Remove project", "Delete projects from configuration"),
            
            "--- Monitoring & Updates",
            ("6", "Start monitoring", "Begin monitoring and updating project files"),
            ("7", "Batch update", "Update multiple projects at once"),
            ("8", "Check for updates", "Check and install CursorFocus updates"),
            
            "--- Configuration",
            ("9", "Gemini AI Settings", "Configure Gemini API key and model"),
            ("S", "Settings", "Configure application settings"),
            ("A", "About", "Information about CursorFocus"),
            ("Q", "Quit", "Exit the application")
        ]
        
        # Display menu and get choice
        choice = display_menu("CURSOR FOCUS CLI", options, status)
        
        if choice == '1':
            setup_new_project_menu()
        elif choice == '2':
            scan_for_projects_menu()
        elif choice == '3':
            list_projects_menu()
        elif choice == '4':
            edit_project_menu()
        elif choice == '5':
            remove_project_menu()
        elif choice == '6':
            start_monitoring()
        elif choice == '7':
            batch_update_menu()
        elif choice == '8':
            check_updates_menu()
        elif choice == '9':
            gemini_settings_menu()
        elif choice.lower() in ['s', '10']:
            settings_menu()
        elif choice.lower() in ['a', '11']:
            about_menu()
        elif choice.lower() in ['q', '0', 'quit', 'exit']:
            console.print("\n[bold green]👋 Thank you for using CursorFocus![/]")
            time.sleep(1)
            sys.exit(0)
        else:
            error_message("Invalid choice, please try again")
            time.sleep(1)

def handle_command_line():
    """Handle command line arguments for CLI operation."""
    parser = argparse.ArgumentParser(description='CursorFocus - Automatically analyze and create context for Cursor AI IDE')
    
    # Add arguments
    parser.add_argument('--setup', '-s', help='Setup a project with the given path')
    parser.add_argument('--monitor', '-m', action='store_true', help='Start monitoring configured projects')
    parser.add_argument('--scan', help='Scan directory for projects')
    parser.add_argument('--update', '-u', action='store_true', help='Check for updates')
    parser.add_argument('--list', '-l', action='store_true', help='List configured projects')
    parser.add_argument('--batch-update', '-b', action='store_true', help='Batch update all projects')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode without interactive prompts')
    
    args = parser.parse_args()
    
    # Handle command line operation
    if len(sys.argv) > 1:
        if args.setup:
            # Setup project
            if os.path.exists(args.setup):
                project_name = os.path.basename(os.path.normpath(args.setup))
                print(f"Setting up project: {project_name}")
                
                success, message = CursorFocusCore.setup_project(args.setup, project_name)
                print(message)
                return success
            else:
                print(f"Error: Path does not exist: {args.setup}")
                return False
        
        elif args.monitor:
            # Start monitoring in headless mode
            config = load_config()
            if not config or 'projects' not in config or not config['projects']:
                print("No projects configured")
                return False
            
            valid_projects = [p for p in config['projects'] if os.path.exists(p['project_path'])]
            if not valid_projects:
                print("No valid projects to monitor")
                return False
            
            print(f"Starting monitoring for {len(valid_projects)} projects...")
            try:
                # Setup and start monitoring
                for project in valid_projects:
                    print(f"Setting up: {project['name']}")
                    CursorFocusCore.setup_project(project['project_path'], project['name'])
                
                threads, watchers = CursorFocusCore.start_monitoring(
                    valid_projects,
                    auto_update=False
                )
                
                print(f"Monitoring {len(threads)} projects. Press Ctrl+C to stop...")
                
                while True:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\nStopped monitoring")
                return True
            except Exception as e:
                print(f"Error during monitoring: {e}")
                return False
                
        elif args.scan:
            # Scan for projects
            if not os.path.exists(args.scan):
                print(f"Error: Path does not exist: {args.scan}")
                return False
                
            print(f"Scanning for projects in: {args.scan}")
            found_projects = CursorFocusCore.find_projects(args.scan, 3)
            
            if not found_projects:
                print("No projects found")
                return False
                
            print(f"Found {len(found_projects)} projects:")
            for i, project in enumerate(found_projects, 1):
                print(f"{i}. {project['name']} ({project['type']})")
                print(f"   Path: {project['path']}")
                if project.get('language'): print(f"   Language: {project['language']}")
                if project.get('framework'): print(f"   Framework: {project['framework']}")
                
            return True
            
        elif args.update:
            # Check for updates
            print("Checking for updates...")
            update_info = CursorFocusCore.check_for_updates()
            
            if update_info:
                print(f"New update available: {update_info['message']}")
                print(f"Date: {update_info['date']}")
                print(f"Author: {update_info['author']}")
                
                if not args.headless and input("Update now? (y/n): ").lower() == 'y':
                    print("Downloading...")
                    if CursorFocusCore.apply_update(update_info):
                        print("Updated! Please restart the application")
                        return True
                    else:
                        print("Update failed")
                        return False
                return True
            else:
                print("You are using the latest version")
                return True
                
        elif args.list:
            # List projects
            config = load_config()
            if not config or 'projects' not in config or not config['projects']:
                print("No projects configured")
                return False
                
            print("Configured projects:")
            for i, project in enumerate(config['projects'], 1):
                path_exists = os.path.exists(project['project_path'])
                status = "OK" if path_exists else "Path not found"
                print(f"{i}. {project['name']}")
                print(f"   Path: {project['project_path']} ({status})")
                print(f"   Update interval: {project['update_interval']}s")
                print(f"   Max depth: {project['max_depth']} levels")
                
            return True
            
        elif args.batch_update:
            # Batch update all projects
            config = load_config()
            if not config or 'projects' not in config or not config['projects']:
                print("No projects configured")
                return False
                
            valid_projects = [p for p in config['projects'] if os.path.exists(p['project_path'])]
            if not valid_projects:
                print("No valid projects to update")
                return False
                
            print(f"Updating {len(valid_projects)} projects...")
            success_count, total, errors = CursorFocusCore.batch_update_projects(valid_projects)
            
            # Show errors if any
            if errors:
                print("\nErrors:")
                for project_name, error_msg in errors:
                    print(f"✗ {project_name}: {error_msg}")
            
            print(f"Successfully updated {success_count}/{total} projects")
            return success_count > 0
            
        return True  # Command line operation handled
        
    return False  # No command line arguments, continue to interactive mode

if __name__ == '__main__':
    try:
        # Check if running with command line arguments
        if not handle_command_line():
            # Start interactive menu
            main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[bold green]👋 Thank you for using CursorFocus![/]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n\n[bold red]❌ An error occurred: {str(e)}[/]")
        console.print("[red]Please try again later[/]")
        sys.exit(1) 