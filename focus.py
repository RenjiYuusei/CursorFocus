import os
import time
from datetime import datetime
from config import load_config
from content_generator import generate_focus_content
from rules_analyzer import RulesAnalyzer
from rules_generator import RulesGenerator
from rules_watcher import ProjectWatcherManager
import logging
from auto_updater import AutoUpdater

def get_default_config():
    """Get default configuration with parent directory as project path."""
    return {
        'project_path': os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
        'update_interval': 60,
        'max_depth': 3,
        'ignored_directories': [
            '__pycache__',
            'node_modules',
            'venv',
            '.git',
            '.idea',
            '.vscode',
            'dist',
            'build',
            'CursorFocus'
        ],
        'ignored_files': [
            '.DS_Store',
            '*.pyc',
            '*.pyo'
        ],
        'binary_extensions': [
            '.png',
            '.jpg',
            '.jpeg',
            '.gif',
            '.ico',
            '.pdf',
            '.exe',
            '.bin'
        ],
        'file_length_standards': {
            '.js': 300,
            '.jsx': 250,
            '.ts': 300,
            '.tsx': 250,
            '.py': 400,
            '.css': 400,
            '.scss': 400,
            '.less': 400,
            '.sass': 400,
            '.html': 300,
            '.vue': 250,
            '.svelte': 250,
            '.json': 100,
            '.yaml': 100,
            '.yml': 100,
            '.toml': 100,
            '.md': 500,
            '.rst': 500,
            '.php': 400,
            '.phtml': 300,
            '.ctp': 300,
            '.swift': 300,
            '.kt': 300,
            'default': 300
        },
        'file_length_thresholds': {
            'warning': 1.0,
            'critical': 1.5,
            'severe': 2.0
        },
        'project_types': {
            'chrome_extension': {
                'indicators': ['manifest.json'],
                'required_files': [],
                'description': 'Chrome Extension'
            },
            'node_js': {
                'indicators': ['package.json'],
                'required_files': [],
                'description': 'Node.js Project'
            },
            'python': {
                'indicators': ['setup.py', 'pyproject.toml'],
                'required_files': [],
                'description': 'Python Project'
            },
            'react': {
                'indicators': [],
                'required_files': ['src/App.js', 'src/index.js'],
                'description': 'React Application'
            },
            'php': {
                'indicators': ['composer.json', 'index.php'],
                'required_files': [],
                'description': 'PHP Project'
            },
            'laravel': {
                'indicators': ['artisan'],
                'required_files': [],
                'description': 'Laravel Project'
            },
            'wordpress': {
                'indicators': ['wp-config.php'],
                'required_files': [],
                'description': 'WordPress Project'
            }
        }
    }

def retry_generate_rules(project_path, project_name, max_retries=3):
    """Retry generating rules file with user confirmation."""
    retries = 0
    while retries < max_retries:
        try:
            print(f"\n📄 Analyzing: {project_path}")
            analyzer = RulesAnalyzer(project_path)
            project_info = analyzer.analyze_project_for_rules()
            
            rules_generator = RulesGenerator(project_path)
            rules_file = rules_generator.generate_rules_file(project_info)
            print(f"✓ {os.path.basename(rules_file)}")
            return rules_file
        except Exception as e:
            retries += 1
            if retries < max_retries:
                print(f"\n❌ Failed to generate rules (attempt {retries}/{max_retries}): {e}")
                response = input("Try again? (y/n): ").lower()
                if response != 'y':
                    raise
            else:
                print(f"\n❌ Failed to generate rules after {max_retries} attempts: {e}")
                raise

def setup_cursor_focus(project_path, project_name=None):
    """Set up CursorFocus for a project by generating necessary files."""
    try:
        rules_file = os.path.join(project_path, '.cursorrules')
        
        # Check if .cursorrules exists and ask user
        if os.path.exists(rules_file):
            print(f"\n.cursorrules exists for {project_name or 'project'}")
            response = input("Generate new? (y/n): ").lower()
            if response != 'y':
                return
        
        # Generate .cursorrules file with retry mechanism
        rules_file = retry_generate_rules(project_path, project_name)

        # Generate initial Focus.md with default config
        focus_file = os.path.join(project_path, 'Focus.md')
        default_config = get_default_config()
        content = generate_focus_content(project_path, default_config)
        with open(focus_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ {os.path.basename(focus_file)}")

    except Exception as e:
        print(f"❌ Setup error: {e}")
        raise

def monitor_project(project_config, global_config):
    """Monitor a single project."""
    project_path = project_config['project_path']
    project_name = project_config['name']
    print(f"👀 {project_name}")
    
    # Merge project config with global config
    config = {**global_config, **project_config}
    
    focus_file = os.path.join(project_path, 'Focus.md')
    last_content = None
    last_update = 0

    # Start rules watcher for this project
    watcher = ProjectWatcherManager()
    watcher.add_project(project_path, project_name)

    while True:
        current_time = time.time()
        
        if current_time - last_update < config.get('update_interval', 60):
            time.sleep(1)
            continue
            
        content = generate_focus_content(project_path, config)
        
        if content != last_content:
            try:
                with open(focus_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                last_content = content
                print(f"✓ {project_name} ({datetime.now().strftime('%H:%M')})")
            except Exception as e:
                print(f"❌ {project_name}: {e}")
        
        last_update = current_time

def main():
    """Main function to monitor multiple projects."""
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s'
    )

    # Check updates
    print("\n🔄 Checking updates...")
    updater = AutoUpdater()
    update_info = updater.check_for_updates()
    
    if update_info:
        print(f"📦 Update available: {update_info['message']}")
        if input("Update now? (y/n): ").lower() == 'y':
            print("⏳ Downloading...")
            if updater.update(update_info):
                print("✅ Updated! Please restart")
                return
            else:
                print("❌ Update failed")
    else:
        print("✓ Latest version")

    config = load_config()
    if not config:
        print("No config.json found")
        config = get_default_config()

    if 'projects' not in config:
        config['projects'] = [{
            'name': 'Default Project',
            'project_path': config['project_path'],
            'update_interval': config.get('update_interval', 60),
            'max_depth': config.get('max_depth', 3)
        }]

    from threading import Thread
    threads = []
    
    try:
        # Setup projects
        for project in config['projects']:
            if os.path.exists(project['project_path']):
                setup_cursor_focus(project['project_path'], project['name'])
            else:
                print(f"⚠️ Not found: {project['project_path']}")
                continue

        # Start monitoring
        for project in config['projects']:
            if os.path.exists(project['project_path']):
                thread = Thread(
                    target=monitor_project,
                    args=(project, config),
                    daemon=True
                )
                thread.start()
                threads.append(thread)

        if not threads:
            print("❌ No projects to monitor")
            return

        print(f"\n📝 Monitoring {len(threads)} projects (Ctrl+C to stop)")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    main() 