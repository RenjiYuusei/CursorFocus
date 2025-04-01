import os
import time
from datetime import datetime
from config import load_config, get_default_config
from content_generator import generate_focus_content
from rules_analyzer import RulesAnalyzer
from rules_generator import RulesGenerator
from rules_watcher import ProjectWatcherManager
import logging
from auto_updater import AutoUpdater
from dotenv import load_dotenv, set_key

def retry_generate_rules(project_path, project_name, max_retries=3):
    """Retry generating rules file automatically."""
    retries = 0
    while retries < max_retries:
        try:
            print(f"\n📄 Analyzing: {project_path}")
            analyzer = RulesAnalyzer(project_path)
            project_info = analyzer.analyze_project_for_rules()
            
            # Ask for format preference using numbers
            print("\nSelect format for .cursorrules file:")
            print("1. JSON")
            print("2. Markdown")
            while True:
                try:
                    choice = int(input("Enter selection (1-2): "))
                    if choice in [1, 2]:
                        format_choice = 'json' if choice == 1 else 'markdown'
                        break
                    print("Please enter 1 or 2")
                except ValueError:
                    print("Please enter a number")
            
            rules_generator = RulesGenerator(project_path)
            rules_file = rules_generator.generate_rules_file(project_info, format=format_choice)
            print(f"✓ {os.path.basename(rules_file)}")
            return rules_file
        except Exception as e:
            error_msg = str(e)
            # Check if it's an API key error
            if "GEMINI_API_KEY is required" in error_msg:
                print("\n⚠️ Gemini API Key is not set")
                print("Please enter your API key (get key at https://makersuite.google.com/app/apikey):")
                api_key = input()
                
                if api_key.strip():
                    # Save API key to .env file
                    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
                    if not os.path.exists(env_path):
                        with open(env_path, 'w') as f:
                            f.write(f"GEMINI_API_KEY={api_key}")
                    else:
                        set_key(env_path, "GEMINI_API_KEY", api_key)
                    
                    # Reload environment variables
                    load_dotenv(override=True)
                    print("✓ API key has been saved")
                    continue
                else:
                    print("❌ Invalid API key")
                    raise ValueError("API key is not provided")
            
            retries += 1
            if retries < max_retries:
                wait_time = 2 * (2 ** (retries - 1))  # Exponential backoff
                print(f"\n⚠️ Error occurred, automatically retrying in {wait_time} seconds... (attempt {retries}/{max_retries})")
                print(f"Error details: {str(e)}")
                time.sleep(wait_time)
                continue
            else:
                print(f"\n❌ Failed to generate rules after {max_retries} attempts: {e}")
                raise

def setup_cursor_focus(project_path, project_name=None):
    """Set up CursorFocus for a project by generating necessary files."""
    try:
        # Check for existing rules file
        rules_file = os.path.join(project_path, '.cursorrules')
        
        if os.path.exists(rules_file):
            print(f"\nRules file exists for {project_name or 'project'}")
            response = input("Update rules? (y/n): ").lower()
            if response != 'y':
                return
        
        # Generate/Update .cursorrules file with retry mechanism
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

    # # Check updates
    # print("\n🔄 Checking updates...")
    # updater = AutoUpdater()
    # update_info = updater.check_for_updates()
    
    # if update_info:
    #     print(f"📦 Update available: {update_info['message']}")
    #     print(f"🕒 Date: {update_info['date']}")
    #     print(f"👤 Author: {update_info['author']}")
    #     try:
    #         if input("Update now? (y/n): ").lower() == 'y':
    #             print("⏳ Downloading...")
    #             if updater.update(update_info):
    #                 print("✅ Updated! Please restart")
    #                 return
    #             else:
    #                 print("❌ Update failed")
    #     except KeyboardInterrupt:
    #         print("\n👋 Update canceled")
    #         pass
    # else:
    #     print("✓ Latest version")

    print("\n✓ Automatic updates disabled")

    config = load_config()
    if not config:
        print("No config.json found, using default configuration")
        config = get_default_config()

    if 'projects' not in config:
        config['projects'] = [{
            'name': 'Default Project',
            'project_path': config.get('project_path', os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))),
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
        print("\n👋 Bye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    main() 