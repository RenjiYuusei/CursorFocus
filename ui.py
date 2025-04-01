#!/usr/bin/env python3
import os
import sys
import time
import shutil
from colorama import init, Fore, Back, Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
import keyboard

# Initialize colorama
init(autoreset=True)

# Rich console for improved output
console = Console()

# Define colors and styles for classic terminal output
class Colors:
    """Color and style definitions for the classic terminal interface."""
    TITLE = Fore.CYAN + Style.BRIGHT
    SUBTITLE = Fore.WHITE + Style.BRIGHT
    PROMPT = Fore.GREEN + Style.BRIGHT
    INFO = Fore.BLUE
    SUCCESS = Fore.GREEN
    WARNING = Fore.YELLOW
    ERROR = Fore.RED
    INPUT = Fore.WHITE + Style.BRIGHT
    MENU_NUM = Fore.CYAN + Style.BRIGHT
    MENU_TEXT = Fore.WHITE
    PATH = Fore.MAGENTA
    HEADER_BG = Back.BLUE + Fore.WHITE + Style.BRIGHT
    ACCENT = Fore.YELLOW + Style.BRIGHT
    KEY = Fore.CYAN
    VALUE = Fore.WHITE
    RESET = Style.RESET_ALL

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_terminal_size():
    """Get terminal dimensions."""
    return shutil.get_terminal_size((80, 20))

# ========== Modern UI Functions (using Rich) ==========

def create_title_panel(title, subtitle=None):
    """Create a stylish title panel."""
    if subtitle:
        content = f"[bold cyan]{title}[/]\n[white]{subtitle}[/]"
    else:
        content = f"[bold cyan]{title}[/]"
    
    return Panel(
        content,
        border_style="blue",
        title="[white on blue] CursorFocus [/]",
        title_align="center",
        subtitle="[dim]AI-Powered Context Generator for Cursor IDE[/]",
        subtitle_align="center",
        padding=(1, 2)
    )

def display_menu(title, options, status=None):
    """Display a beautiful menu with options."""
    clear_screen()
    
    console.print(create_title_panel(title))
    
    if status:
        status_text = Text()
        for key, value in status.items():
            status_text.append(f"{key}: ", style="bold cyan")
            if isinstance(value, tuple):
                text, style = value
                status_text.append(f"{text}", style=style)
            else:
                status_text.append(f"{value}")
            status_text.append(" | ")
        
        console.print(Panel(status_text, border_style="dim", padding=(1, 2)))
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Number", style="cyan")
    table.add_column("Option", style="white")
    table.add_column("Description", style="dim")
    
    for option in options:
        if isinstance(option, str) and option.startswith("---"):
            # This is a category header
            category = option.replace("---", "").strip()
            table.add_row("", f"[bold yellow]{category}[/]", "")
        else:
            number, text, description = option
            table.add_row(f"[bold]{number}[/]", text, description)
    
    console.print(table)
    
    return Prompt.ask("[bold green]Enter your choice[/]")

def display_custom_progress(description="Processing", iterations=100, delay=0.01):
    """Display a custom progress bar with spinner."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[bold cyan]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(f"[cyan]{description}", total=iterations)
        
        for _ in range(iterations):
            time.sleep(delay)
            progress.update(task, advance=1)

def input_with_default(prompt, default=""):
    """Get input with a default value."""
    result = Prompt.ask(
        f"[bold green]{prompt}[/]", 
        default=default,
        show_default=True if default else False
    )
    return result

def confirm_action(question):
    """Confirm an action with yes/no."""
    return Confirm.ask(f"[bold yellow]{question}[/]")

def success_message(message):
    """Display a success message."""
    console.print(f"[bold green]✓ {message}[/]")

def error_message(message):
    """Display an error message."""
    console.print(f"[bold red]❌ {message}[/]")

def warning_message(message):
    """Display a warning message."""
    console.print(f"[bold yellow]⚠️ {message}[/]")

def info_message(message):
    """Display an information message."""
    console.print(f"[blue]ℹ️ {message}[/]")

def wait_for_key():
    """Wait for user to press any key to continue."""
    console.print("\n[bold green]Press Enter to continue...[/]")
    input()

def get_input(prompt_text):
    """Get user input with styled prompt."""
    return input_with_default(prompt_text)

def display_project_list(projects, title="Project List"):
    """Display a list of projects in a table format."""
    console.print(create_title_panel(title))
    
    if not projects:
        warning_message("No projects configured")
        return
    
    table = Table(title="Configured Projects", show_lines=True)
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="bold white")
    table.add_column("Path", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Update Interval", style="blue")
    table.add_column("Max Depth", style="blue")
    
    for i, project in enumerate(projects, 1):
        path_exists = os.path.exists(project['project_path'])
        status = "[green]Active[/]" if path_exists else "[red]Path not found[/]"
        
        table.add_row(
            str(i),
            project['name'],
            project['project_path'],
            status,
            f"{project['update_interval']}s",
            str(project['max_depth'])
        )
    
    console.print(table)
    console.print(f"\n[blue]Total:[/] [bold]{len(projects)}[/] projects configured")

def display_monitoring_screen(project_count):
    """Display a live monitoring screen."""
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    
    # Create header
    layout["header"].update(Panel(
        "[bold cyan]CursorFocus Monitoring[/]",
        border_style="blue",
        padding=(1, 2)
    ))
    
    # Create footer with instructions
    layout["footer"].update(Panel(
        "[bold green]Press Ctrl+C to stop monitoring[/]",
        border_style="green", 
        padding=(1, 0)
    ))
    
    project_table = Table(title=f"Monitoring {project_count} Projects", show_lines=True)
    project_table.add_column("Project", style="bold white")
    project_table.add_column("Status", style="green")
    project_table.add_column("Last Update", style="blue")
    project_table.add_column("Next Update", style="cyan")
    
    # Add sample projects row
    project_table.add_row(
        "Sample Project", 
        "[green]Active[/]", 
        "Just now", 
        "In 60s"
    )
    
    layout["body"].update(project_table)
    
    # Return the layout for use in a Live context
    return layout

def display_scanning_results(found_projects):
    """Display the results of scanning for projects."""
    if not found_projects:
        error_message("No projects found")
        return
    
    console.print(f"\n[bold green]Found {len(found_projects)} projects:[/]")
    
    table = Table(title="Detected Projects", show_lines=True)
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="bold white")
    table.add_column("Type", style="blue")
    table.add_column("Path", style="magenta")
    table.add_column("Language", style="green")
    table.add_column("Framework", style="yellow")
    
    for i, project in enumerate(found_projects, 1):
        table.add_row(
            str(i),
            project['name'],
            project.get('type', ''),
            project['path'],
            project.get('language', ''),
            project.get('framework', '')
        )
    
    console.print(table)

def display_update_info(update_info):
    """
    Display information about an available update and options.
    
    Args:
        update_info (dict): Update information dictionary or None
        
    Returns:
        bool: True if user wants to update, False otherwise
    """
    if not update_info:
        success_message("You are using the latest version")
        return False
    
    console.print(Panel(
        f"[bold green]✨ New update available![/]\n\n"
        f"[cyan]Content:[/] {update_info['message']}\n"
        f"[cyan]Date:[/] {update_info['date']}\n"
        f"[cyan]Author:[/] {update_info['author']}\n"
        f"[cyan]SHA:[/] {update_info['sha'][:8]}",
        title="Update Available",
        border_style="green",
        padding=(1, 2)
    ))
    
    # Ask about backup
    if confirm_action("Update now?"):
        keep_backup = confirm_action("Keep backup after update? (recommended for first update)")
        if keep_backup:
            from core import CursorFocusCore
            CursorFocusCore.configure_updater(keep_backups=True)
            info_message("Backup will be kept after update")
        return True
    
    return False

# Legacy UI functions for compatibility
def print_centered(text, color=None):
    """Print text centered in the terminal."""
    terminal_width = get_terminal_size().columns
    if color:
        print(color + text.center(terminal_width) + Colors.RESET)
    else:
        print(text.center(terminal_width))

def print_header():
    """Print the classic application header."""
    clear_screen()
    terminal_width = get_terminal_size().columns
    
    print(Colors.HEADER_BG + "=" * terminal_width + Colors.RESET)
    print_centered("CURSOR FOCUS CLI", Colors.TITLE)
    print(Colors.HEADER_BG + "=" * terminal_width + Colors.RESET)
    print_centered("Automatically analyze and create context for Cursor AI IDE", Colors.SUBTITLE)
    print(Colors.INFO + "-" * terminal_width + Colors.RESET)

def print_key_value(key, value, indent=0):
    """Print a key-value pair with formatting."""
    indentation = " " * indent
    print(f"{indentation}{Colors.KEY}{key}:{Colors.RESET} {Colors.VALUE}{value}{Colors.RESET}")

def processing_message(message):
    """Display a processing message (legacy)."""
    print(f"{Colors.INFO}⏳ {message}{Colors.RESET}") 