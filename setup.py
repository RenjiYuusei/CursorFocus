#!/usr/bin/env python3
import os
import json
import argparse
import logging
from project_detector import scan_for_projects

def setup_cursorfocus():
    """Set up CursorFocus for your projects."""
    parser = argparse.ArgumentParser(description='Set up CursorFocus for your projects')
    parser.add_argument('--projects', '-p', nargs='+', help='Paths to projects to monitor')
    parser.add_argument('--names', '-n', nargs='+', help='Names for the projects (optional)')
    parser.add_argument('--list', '-l', action='store_true', help='List all configured projects')
    parser.add_argument('--remove', '-r', nargs='+', help='Remove projects by name/index, or use "all" to remove all projects')
    parser.add_argument('--scan', '-s', nargs='?', const='.', help='Scan directory for projects')
    
    args = parser.parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    config = load_or_create_config(config_path)
    
    if 'projects' not in config:
        config['projects'] = []

    if args.list:
        list_projects(config['projects'])
        return

    if args.remove:
        if 'all' in args.remove:
            if confirm_action("Remove all projects?"):
                config['projects'] = []
                save_config(config_path, config)
                print("✅ All projects removed")
        else:
            remove_projects(config, args.remove)
            save_config(config_path, config)
        return

    # Handle scan option
    if args.scan is not None:
        scan_path = os.path.abspath(args.scan) if args.scan else os.getcwd()
        print(f"🔍 Scanning: {scan_path}")
        found_projects = scan_for_projects(scan_path, 3)
        
        if not found_projects:
            print("❌ No projects found")
            return
            
        print(f"\nFound {len(found_projects)} projects:")
        for i, project in enumerate(found_projects, 1):
            print(f"{i}. {project['name']} ({project['type']})")
            print(f"   Path: {project['path']}")
            if project.get('language'): print(f"   Language: {project['language']}")
            if project.get('framework'): print(f"   Framework: {project['framework']}")
        
        print("\nSelect projects (numbers/all/q):")
        try:
            selection = input("> ").strip().lower()
            if selection in ['q', 'quit', 'exit']:
                return
                
            if selection == 'all':
                indices = range(len(found_projects))
            else:
                try:
                    indices = [int(i) - 1 for i in selection.split()]
                    if any(i < 0 or i >= len(found_projects) for i in indices):
                        print("❌ Invalid numbers")
                        return
                except ValueError:
                    print("❌ Invalid input")
                    return
            
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
                
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return
        
        if config['projects']:
            save_config(config_path, config)
        return

    # Add/update projects
    if args.projects:
        valid_projects = []
        for i, project_path in enumerate(args.projects):
            abs_path = os.path.abspath(project_path)
            if not os.path.exists(abs_path):
                print(f"⚠️ Path not found: {abs_path}")
                continue
                
            project_name = args.names[i] if args.names and i < len(args.names) else get_project_name(abs_path)
            project_config = {
                'name': project_name,
                'project_path': abs_path,
                'update_interval': 60,
                'max_depth': 3
            }
            valid_projects.append(project_config)
            
        names = [p['name'] for p in valid_projects]
        if len(names) != len(set(names)):
            name_counts = {}
            for project in valid_projects:
                base_name = project['name']
                if base_name in name_counts:
                    name_counts[base_name] += 1
                    project['name'] = f"{base_name} ({name_counts[base_name]})"
                else:
                    name_counts[base_name] = 1
        
        for project in valid_projects:
            existing = next((p for p in config['projects'] if p['project_path'] == project['project_path']), None)
            if existing:
                existing.update(project)
            else:
                config['projects'].append(project)

    save_config(config_path, config)
    print("\n📁 Projects:")
    for project in config['projects']:
        print(f"\n• {project['name']}")
        print(f"  Path: {project['project_path']}")
        print(f"  Update: {project['update_interval']}s")
        print(f"  Depth: {project['max_depth']}")
    
    print(f"\nRun: python {os.path.join(script_dir, 'focus.py')}")

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

def list_projects(projects):
    """Display list of configured projects."""
    if not projects:
        print("\n📁 No projects configured.")
        return
        
    print("\n📁 Configured projects:")
    for i, project in enumerate(projects, 1):
        print(f"\n  {i}. {project['name']}:")
        print(f"     Path: {project['project_path']}")
        print(f"     Update interval: {project['update_interval']} seconds")
        print(f"     Max depth: {project['max_depth']} levels")

def remove_projects(config, targets):
    """Remove specific projects by name or index."""
    if not config['projects']:
        print("\n⚠️ No projects configured.")
        return
        
    remaining_projects = []
    removed = []
    
    for project in config['projects']:
        should_keep = True
        
        for target in targets:
            # Check if target is an index
            try:
                idx = int(target)
                if idx == config['projects'].index(project) + 1:
                    should_keep = False
                    removed.append(project['name'])
                    break
            except ValueError:
                # Target is a name
                if project['name'].lower() == target.lower():
                    should_keep = False
                    removed.append(project['name'])
                    break
                    
        if should_keep:
            remaining_projects.append(project)
    
    if removed:
        config['projects'] = remaining_projects
        print(f"\n✅ Removed projects: {', '.join(removed)}")
    else:
        print("\n⚠️ No matching projects found.")

def confirm_action(message):
    """Ask for user confirmation."""
    while True:
        response = input(f"\n{message} (y/n): ").lower()
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False

def get_project_name(project_path):
    """Get project name from directory name, with some cleanup."""
    # Get the base directory name
    base_name = os.path.basename(os.path.normpath(project_path))
    
    # Clean up common suffixes
    name = base_name.lower()
    for suffix in ['-main', '-master', '-dev', '-development', '.git']:
        if name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break
    
    # Convert to title case and replace special characters
    words = base_name.replace('-', ' ').replace('_', ' ').split()
    return ' '.join(word.capitalize() for word in words)

if __name__ == '__main__':
    setup_cursorfocus() 