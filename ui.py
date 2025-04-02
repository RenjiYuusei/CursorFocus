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
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.style import Style as RichStyle
from rich.align import Align
from rich.columns import Columns
from rich import box
import keyboard

# Initialize colorama
init(autoreset=True)

# Rich console for improved output
console = Console()

# Define theme colors for consistent UI
class Theme:
    """Modern theme colors and styles for the application."""
    PRIMARY = "blue"
    SECONDARY = "cyan"
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    INFO = "bright_blue"
    MUTED = "dim"
    ACCENT = "magenta"
    PROMPT = "green"
    
    # Compound styles
    TITLE = f"bold {PRIMARY}"
    SUBTITLE = f"bold {SECONDARY}"
    HEADER = f"bold {PRIMARY}"
    HIGHLIGHT = f"bold {ACCENT}"
    
    # Panel styles
    PANEL_BORDER = PRIMARY
    PANEL_TITLE = f"white on {PRIMARY}"
    
    # Table styles
    TABLE_HEADER = f"bold {SECONDARY}"
    TABLE_BORDER = SECONDARY
    
    # Component styles
    BUTTON = f"bold {PRIMARY}"
    LINK = f"underline {INFO}"
    ICON_SUCCESS = "✓"
    ICON_ERROR = "✗"
    ICON_WARNING = "⚠"
    ICON_INFO = "ℹ"
    ICON_ARROW = "→"
    ICON_BULLET = "•"
    ICON_GEAR = "⚙"
    ICON_STAR = "★"
    ICON_FOLDER = "📁"
    ICON_FILE = "📄"
    ICON_CLOCK = "🕒"
    ICON_SEARCH = "🔍"
    ICON_KEY = "🔑"
    ICON_NET = "🌐"
    ICON_MONITOR = "📡"
    ICON_LOCK = "🔒"

# Legacy colors for backward compatibility
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
    """Create a stylish title panel with modern design."""
    if subtitle:
        content = f"[{Theme.TITLE}]{title}[/]\n[white]{subtitle}[/]"
    else:
        content = f"[{Theme.TITLE}]{title}[/]"
    
    return Panel(
        content,
        border_style=Theme.PANEL_BORDER,
        title=f"[{Theme.PANEL_TITLE}] CursorFocus [/]",
        title_align="center",
        subtitle=f"[{Theme.MUTED}]AI-Powered Context Generator for Cursor IDE[/]",
        subtitle_align="center",
        padding=(1, 2),
        box=box.ROUNDED
    )

def display_menu(title, options, status=None):
    """Display a beautiful menu with options and status information."""
    clear_screen()
    
    console.print(create_title_panel(title))
    
    if status:
        status_items = []
        for key, value in status.items():
            if isinstance(value, tuple):
                text, style = value
                status_items.append(f"[bold {Theme.SECONDARY}]{key}:[/] [{style}]{text}[/]")
            else:
                status_items.append(f"[bold {Theme.SECONDARY}]{key}:[/] {value}")
        
        status_text = Align.center(" | ".join(status_items))
        console.print(Panel(status_text, border_style=Theme.MUTED, padding=(1, 2), box=box.ROUNDED))
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Number", style=Theme.SECONDARY)
    table.add_column("Option", style="white")
    table.add_column("Description", style=Theme.MUTED)
    
    for option in options:
        if isinstance(option, str) and option.startswith("---"):
            # This is a category header
            category = option.replace("---", "").strip()
            table.add_row("", f"[bold {Theme.ACCENT}]{category}[/]", "")
        else:
            number, text, description = option
            table.add_row(f"[bold]{number}[/]", text, f"{Theme.ICON_ARROW} {description}")
    
    console.print(table)
    
    return Prompt.ask(f"[bold {Theme.SUCCESS}]Enter your choice[/]")

def display_custom_progress(description="Processing", iterations=100, delay=0.01):
    """Display a modern progress bar with spinner and detailed statistics."""
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[bold {Theme.PRIMARY}]{{task.description}}"),
        BarColumn(bar_width=40, complete_style=Theme.SUCCESS, finished_style=Theme.SUCCESS),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(f"[{Theme.SECONDARY}]{description}", total=iterations)
        
        for _ in range(iterations):
            time.sleep(delay)
            progress.update(task, advance=1)

def input_with_default(prompt, default=""):
    """Display a rich input prompt with a default value."""
    # Handle Windows backslashes in paths properly
    if isinstance(default, str) and "\\" in default:
        default = default.replace("\\", "\\\\")
    
    response = console.input(f"[{Theme.PROMPT}]{prompt}[/]" + 
                           (f" ([{Theme.ACCENT}]{default}[/])" if default else "") + 
                           ": ")
    return response.strip() or default

def confirm_action(question):
    """Confirm an action with yes/no prompt."""
    return Confirm.ask(f"[bold {Theme.WARNING}]{question}[/]")

def success_message(message):
    """Display a success message."""
    if "\n" in message:
        for line in message.split("\n"):
            console.print(f"[bold {Theme.SUCCESS}]{Theme.ICON_SUCCESS} {line.strip()}[/]")
    else:
        console.print(f"[bold {Theme.SUCCESS}]{Theme.ICON_SUCCESS} {message}[/]")

def error_message(message):
    """Display an error message with icon."""
    console.print(f"[bold {Theme.ERROR}]{Theme.ICON_ERROR} {message}[/]")

def warning_message(message):
    """Display a warning message with icon."""
    console.print(f"[bold {Theme.WARNING}]{Theme.ICON_WARNING} {message}[/]")

def info_message(message):
    """Display an information message with icon."""
    console.print(f"[{Theme.INFO}]{Theme.ICON_INFO} {message}[/]")

def wait_for_key():
    """Wait for user to press any key to continue."""
    console.print(f"\n[bold {Theme.SUCCESS}]Press Enter to continue...[/]")
    input()

def get_input(prompt_text):
    """Get user input with styled prompt."""
    return input_with_default(prompt_text)

def display_project_list(projects, title="Project List"):
    """Display a list of projects in a modern table format."""
    console.print(create_title_panel(title))
    
    if not projects:
        warning_message("No projects configured")
        return
    
    table = Table(
        title=f"{Theme.ICON_FOLDER} Configured Projects",
        show_lines=True,
        box=box.ROUNDED,
        title_style=f"bold {Theme.SECONDARY}",
        border_style=Theme.SECONDARY
    )
    
    table.add_column("#", style=Theme.SECONDARY, justify="right")
    table.add_column("Name", style="bold white")
    table.add_column("Path", style=Theme.ACCENT)
    table.add_column("Status", style=Theme.SUCCESS)
    table.add_column("Update Interval", style=Theme.INFO)
    table.add_column("Max Depth", style=Theme.INFO)
    
    for i, project in enumerate(projects, 1):
        path_exists = os.path.exists(project['project_path'])
        status = f"[{Theme.SUCCESS}]Active[/]" if path_exists else f"[{Theme.ERROR}]Path not found[/]"
        
        table.add_row(
            str(i),
            project['name'],
            project['project_path'],
            status,
            f"{project['update_interval']}s",
            str(project['max_depth'])
        )
    
    console.print(table)
    console.print(f"\n[{Theme.INFO}]Total:[/] [bold]{len(projects)}[/] projects configured")

def display_monitoring_screen(project_count):
    """Display a live monitoring screen with modern layout."""
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    
    # Create header
    layout["header"].update(Panel(
        f"[bold {Theme.PRIMARY}]{Theme.ICON_MONITOR} CursorFocus Monitoring[/]",
        border_style=Theme.PANEL_BORDER,
        box=box.ROUNDED,
        padding=(1, 2)
    ))
    
    # Create footer with instructions
    layout["footer"].update(Panel(
        f"[bold {Theme.SUCCESS}]Press Ctrl+C to stop monitoring[/]",
        border_style=Theme.SUCCESS, 
        box=box.ROUNDED,
        padding=(1, 0)
    ))
    
    project_table = Table(
        title=f"{Theme.ICON_MONITOR} Monitoring {project_count} Projects",
        show_lines=True,
        box=box.ROUNDED,
        title_style=f"bold {Theme.PRIMARY}",
        border_style=Theme.SECONDARY
    )
    
    project_table.add_column("Project", style="bold white")
    project_table.add_column("Status", style=Theme.SUCCESS)
    project_table.add_column("Last Update", style=Theme.INFO)
    project_table.add_column("Next Update", style=Theme.SECONDARY)
    
    # Add sample projects row
    project_table.add_row(
        "Sample Project", 
        f"[{Theme.SUCCESS}]Active[/]", 
        "Just now", 
        "In 60s"
    )
    
    layout["body"].update(project_table)
    
    # Return the layout for use in a Live context
    return layout

def display_scanning_results(found_projects):
    """Display the results of scanning for projects with modern styling."""
    if not found_projects:
        error_message("No projects found")
        return
    
    console.print(f"\n[bold {Theme.SUCCESS}]{Theme.ICON_SEARCH} Found {len(found_projects)} projects:[/]")
    
    table = Table(
        title=f"{Theme.ICON_FOLDER} Detected Projects", 
        show_lines=True,
        box=box.ROUNDED,
        title_style=f"bold {Theme.PRIMARY}",
        border_style=Theme.SECONDARY
    )
    
    table.add_column("#", style=Theme.SECONDARY, justify="right")
    table.add_column("Name", style="bold white")
    table.add_column("Type", style=Theme.INFO)
    table.add_column("Path", style=Theme.ACCENT)
    table.add_column("Language", style=Theme.SUCCESS)
    table.add_column("Framework", style=Theme.WARNING)
    
    for i, project in enumerate(found_projects, 1):
        table.add_row(
            str(i),
            str(project['name']),
            str(project.get('type', '')),
            str(project['path']),
            str(project.get('language', '')),
            str(project.get('framework', ''))
        )
    
    console.print(table)

def display_update_info(update_info):
    """
    Display information about an available update with modern styling.
    
    Args:
        update_info (dict): Update information dictionary or None
        
    Returns:
        bool: True if user wants to update, False otherwise
    """
    if not update_info:
        success_message("You are using the latest version")
        return False
    
    # Display header information
    console.print(Panel(
        f"[bold {Theme.SUCCESS}]{Theme.ICON_STAR} New update available![/]\n\n"
        f"[{Theme.SECONDARY}]Version:[/] {update_info['version']}\n"
        f"[{Theme.SECONDARY}]Date:[/] {update_info['date']}\n"
        f"[{Theme.SECONDARY}]Author:[/] {update_info['author']}\n"
        f"[{Theme.SECONDARY}]Asset:[/] {update_info['asset_name']}",
        title="Update Available",
        border_style=Theme.SUCCESS,
        box=box.ROUNDED,
        padding=(1, 2)
    ))
    
    # Ask about backup
    if confirm_action("Update now?"):
        keep_backup = confirm_action("Keep backup after update? (recommended for first update)")
        if keep_backup:
            from core import CursorFocusCore
            CursorFocusCore.configure_updater(keep_backups=True)
            info_message("Backup will be kept after update")
        else:
            # Warn about potential backup cleanup issues
            import platform
            if platform.system().lower() == 'windows':
                warning_message("Note: On Windows, backup cleanup may show warnings about .git directories")
                info_message("These warnings are normal and won't affect functionality")
        
        # Display additional information about the update process
        info_message("Starting update process - this may take a moment...")
        info_message("The update will download and validate the package before applying it")
        
        # For Windows, show different message based on update type
        import platform
        if platform.system().lower() == 'windows':
            if update_info['asset_name'].lower().endswith('.exe'):
                info_message("Detected .exe update file - will install executable directly")
            else:
                info_message("Note: On Windows, updating may skip .git directories to avoid permission issues")
            
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