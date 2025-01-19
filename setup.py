import os
import json
import argparse
import logging
import sys
from project_detector import scan_for_projects

def display_menu():
    """Display the main menu options."""
    print("\n=== CursorFocus Project Manager ===")
    print("1. Manage Projects")
    print("2. Scan Directory for Projects")
    print("3. Add New Project")
    print("4. Exit")
    print("================================")
    print("Press Ctrl+C to exit at any time")
    print("================================")
    try:
        return input("\nSelect an option (1-4): ").strip()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

def get_user_input(prompt):
    """Get user input with KeyboardInterrupt handling."""
    try:
        user_input = input(prompt).strip()
        # Remove surrounding quotes if present
        if (user_input.startswith('"') and user_input.endswith('"')) or \
           (user_input.startswith("'") and user_input.endswith("'")):
            user_input = user_input[1:-1]
        return user_input
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

def list_and_manage_projects(projects, config_path, config):
    """Display list of configured projects with management options."""
    if not projects:
        print("\n📁 No projects configured.")
        return
        
    while True:
        print("\n=== Project Management ===")
        print("\n📁 Configured projects:")
        for i, project in enumerate(projects, 1):
            print(f"\n  {i}. {project['name']}:")
            print(f"     Path: {project['project_path']}")
            print(f"     Update interval: {project['update_interval']} seconds")
            print(f"     Max depth: {project['max_depth']} levels")
        
        print("\nOptions:")
        print("  r <number> - Remove project")
        print("  ra - Remove all projects")
        print("  b - Back to main menu")
        
        choice = get_user_input("\nEnter option: ").lower()
        
        if choice == 'b':
            break
            
        if choice == 'ra':
            if confirm_action("Remove all projects?"):
                projects.clear()
                save_config(config_path, config)
                print("✅ All projects removed")
                break
            
        elif choice.startswith('r '):
            try:
                idx = int(choice.split()[1]) - 1
                if 0 <= idx < len(projects):
                    removed = projects.pop(idx)
                    save_config(config_path, config)
                    print(f"✅ Removed project: {removed['name']}")
                else:
                    print("❌ Invalid project number")
            except (ValueError, IndexError):
                print("❌ Invalid input. Format: r <number>")
        else:
            print("❌ Invalid option")
        
        get_user_input("\nPress Enter to continue...")

def setup_cursorfocus():
    """Set up CursorFocus for your projects."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    config = load_or_create_config(config_path)
    
    if 'projects' not in config:
        config['projects'] = []

    while True:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            choice = display_menu()
            
            if choice == '1':
                list_and_manage_projects(config['projects'], config_path, config)
                
            elif choice == '2':
                print("\n=== Scan Directory for Projects ===")
                path = get_user_input("Enter directory path (or press Enter for current directory): ")
                scan_path = os.path.abspath(path) if path else os.getcwd()
                print(f"\n🔍 Scanning: {scan_path}")
                
                found_projects = scan_for_projects(scan_path, 3)
                if not found_projects:
                    print("❌ No projects found")
                    get_user_input("\nPress Enter to continue...")
                    continue
                    
                print(f"\nFound {len(found_projects)} projects:")
                for i, project in enumerate(found_projects, 1):
                    print(f"{i}. {project['name']} ({project['type']})")
                    print(f"   Path: {project['path']}")
                    if project.get('language'): print(f"   Language: {project['language']}")
                    if project.get('framework'): print(f"   Framework: {project['framework']}")
                
                print("\nSelect projects to add (numbers/all/q):")
                selection = get_user_input("> ")
                
                if selection.lower() in ['q', 'quit', 'exit']:
                    continue
                    
                if selection.lower() == 'all':
                    indices = range(len(found_projects))
                else:
                    try:
                        indices = [int(i) - 1 for i in selection.split()]
                        if any(i < 0 or i >= len(found_projects) for i in indices):
                            print("❌ Invalid numbers")
                            get_user_input("\nPress Enter to continue...")
                            continue
                    except ValueError:
                        print("❌ Invalid input")
                        get_user_input("\nPress Enter to continue...")
                        continue
                
                added = 0
                for idx in indices:
                    project = found_projects[idx]
                    if not any(p['project_path'] == project['path'] for p in config['projects']):
                        config['projects'].append({
                            'name': project['name'],
                            'project_path': project['path'],
                            'update_interval': 60,
                            'max_depth': 3
                        })
                        added += 1
                
                if added > 0:
                    print(f"✅ Added {added} projects")
                    save_config(config_path, config)
                get_user_input("\nPress Enter to continue...")
                
            elif choice == '3':
                print("\n=== Add New Project ===")
                project_path = get_user_input("Enter project path: ")
                if not project_path:
                    print("❌ Path cannot be empty")
                    get_user_input("\nPress Enter to continue...")
                    continue
                    
                abs_path = os.path.abspath(project_path)
                if not os.path.exists(abs_path):
                    print(f"❌ Path not found: {abs_path}")
                    get_user_input("\nPress Enter to continue...")
                    continue
                    
                project_name = get_user_input("Enter project name (or press Enter for auto-name): ")
                if not project_name:
                    project_name = get_project_name(abs_path)
                    
                project_config = {
                    'name': project_name,
                    'project_path': abs_path,
                    'update_interval': 60,
                    'max_depth': 3
                }
                
                config['projects'].append(project_config)
                save_config(config_path, config)
                print(f"✅ Added project: {project_name}")
                get_user_input("\nPress Enter to continue...")
                
            elif choice == '4':
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\nGoodbye! 👋")
                if config['projects']:
                    print(f"\nTo start monitoring, run: python {os.path.join(script_dir, 'focus.py')}")
                sys.exit(0)
                
            else:
                print("❌ Invalid option")
                get_user_input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nExiting...")
            if config['projects']:
                print(f"\nTo start monitoring, run: python {os.path.join(script_dir, 'focus.py')}")
            sys.exit(0)

def load_or_create_config(config_path):
    """Load existing config or create default one."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return get_default_config()

def get_default_config():
    """Return default configuration."""
    return {
        "projects": [],
        "ignored_directories": [
            "__pycache__",
            "node_modules",
            "venv",
            ".git",
            ".idea",
            ".vscode",
            "dist",
            "build"
        ],
        "ignored_files": [
            ".DS_Store",
            "*.pyc",
            "*.pyo"
        ]
    }

def save_config(config_path, config):
    """Save configuration to file."""
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def get_project_name(project_path):
    """Get project name from directory name, with some cleanup."""
    # Get the base directory name
    base_name = os.path.basename(os.path.normpath(project_path))
    
    # Clean up common suffixes without changing case
    for suffix in ['-main', '-master', '-dev', '-development', '.git']:
        if base_name.lower().endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break
    
    # Replace special characters with spaces while preserving case
    words = base_name.replace('-', ' ').replace('_', ' ').split()
    return ' '.join(words)

def confirm_action(message):
    """Ask for user confirmation."""
    while True:
        try:
            response = get_user_input(f"\n{message} (y/n): ").lower()
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
        except KeyboardInterrupt:
            print("\nCancelled")
            return False

if __name__ == '__main__':
    setup_cursorfocus() 