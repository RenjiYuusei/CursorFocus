import os
import time
import logging
from typing import Dict, Any, List, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rules_generator import RulesGenerator
from rules_analyzer import RulesAnalyzer
from project_detector import detect_project_type
from config import load_config, IGNORED_NAMES

# Load configuration at module level
_config = load_config()

class RulesWatcher(FileSystemEventHandler):
    def __init__(self, project_path: str, project_id: str):
        self.project_path = project_path
        self.project_id = project_id
        self.rules_generator = RulesGenerator(project_path)
        self.rules_analyzer = RulesAnalyzer(project_path)
        self.last_update = 0
        self.update_delay = _config.get('rules_update_delay', 5)  # Seconds to wait before updating to avoid multiple updates
        self.auto_update = False  # Disable auto-update by default
        self.logger = logging.getLogger(__name__)
        
        # Trigger files that should cause rules update
        self.trigger_files = {
            'Focus.md',
            'package.json',
            'requirements.txt',
            'CMakeLists.txt',
            'composer.json',
            'build.gradle',
            'pom.xml',
            'Cargo.toml',
            'pubspec.yaml',
            'setup.py',
            'tsconfig.json',
            'pyproject.toml'
        }
        
        # File extensions that should trigger an update
        self.trigger_extensions = {
            '.csproj',
            '.vcxproj',
            '.sln',
            '.gemspec'
        }

    def on_modified(self, event):
        if event.is_directory or not self.auto_update:  # Skip if auto-update is disabled
            return
            
        # Only process Focus.md changes or project configuration files
        if not self._should_process_file(event.src_path):
            return
            
        current_time = time.time()
        if current_time - self.last_update < self.update_delay:
            return
            
        self.last_update = current_time
        self._update_rules()

    def _should_process_file(self, file_path: str) -> bool:
        """Check if the file change should trigger a rules update."""
        if not self.auto_update:  # Skip if auto-update is disabled
            return False
            
        # Skip files in ignored directories
        for ignored in IGNORED_NAMES:
            if f"/{ignored}/" in file_path or f"\\{ignored}\\" in file_path:
                return False
                
        filename = os.path.basename(file_path)
        
        # Check if filename is in trigger files list
        if filename in self.trigger_files:
            self.logger.debug(f"Trigger file modified: {filename}")
            return True
            
        # Check if file extension should trigger an update
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in self.trigger_extensions:
            self.logger.debug(f"Trigger extension modified: {file_ext}")
            return True
            
        return False

    def _update_rules(self):
        """Update the .cursorrules file."""
        if not self.auto_update:  # Skip if auto-update is disabled
            return
            
        try:
            # Re-detect project type
            project_info = detect_project_type(self.project_path)
            
            # If project_info is missing or incomplete, enhance it with analyzer
            if not project_info.get('language') or project_info.get('language') == 'unknown':
                try:
                    analyzed_info = self.rules_analyzer.analyze_project_for_rules()
                    # Merge info, but keep detect_project_type results as primary
                    for key, value in analyzed_info.items():
                        if not project_info.get(key) or project_info[key] == 'unknown' or project_info[key] == 'none':
                            project_info[key] = value
                except Exception as e:
                    self.logger.warning(f"Error enhancing project info with analyzer: {e}")
            
            # Generate new rules
            rules_file = self.rules_generator.generate_rules_file(project_info)
            self.logger.info(f"Updated .cursorrules for project {self.project_id} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            return rules_file
        except Exception as e:
            self.logger.error(f"Error updating .cursorrules for project {self.project_id}: {e}", exc_info=True)
            return None

    def set_auto_update(self, enabled: bool):
        """Enable or disable auto-update of .cursorrules."""
        self.auto_update = enabled
        status = "enabled" if enabled else "disabled"
        self.logger.info(f"Auto-update of .cursorrules is now {status} for project {self.project_id}")

class ProjectWatcherManager:
    def __init__(self):
        self.observers: dict[str, Observer] = {} # type: ignore
        self.watchers: dict[str, RulesWatcher] = {}
        self.logger = logging.getLogger(__name__)

    def add_project(self, project_path: str, project_id: str = None) -> str:
        """Add a new project to watch.
        
        Args:
            project_path: Path to the project directory
            project_id: Optional identifier for the project (defaults to absolute path)
            
        Returns:
            The project_id used to identify this project
            
        Raises:
            ValueError: If the project path does not exist
        """
        if not os.path.exists(project_path):
            self.logger.error(f"Project path does not exist: {project_path}")
            raise ValueError(f"Project path does not exist: {project_path}")
            
        project_id = project_id or os.path.abspath(project_path)
        
        if project_id in self.observers:
            self.logger.info(f"Project {project_id} is already being watched")
            return project_id
            
        event_handler = RulesWatcher(project_path, project_id)
        observer = Observer()
        observer.schedule(event_handler, project_path, recursive=True)
        
        try:
            observer.start()
            self.observers[project_id] = observer
            self.watchers[project_id] = event_handler
            self.logger.info(f"Started watching project {project_id}")
            return project_id
        except Exception as e:
            self.logger.error(f"Failed to start observer for project {project_id}: {e}", exc_info=True)
            raise

    def remove_project(self, project_id: str) -> bool:
        """Stop watching a project.
        
        Args:
            project_id: The identifier of the project to stop watching
            
        Returns:
            True if project was removed, False if it wasn't being watched
        """
        if project_id not in self.observers:
            self.logger.warning(f"Project {project_id} is not being watched")
            return False
            
        observer = self.observers[project_id]
        try:
            observer.stop()
            observer.join()
            
            del self.observers[project_id]
            del self.watchers[project_id]
            
            self.logger.info(f"Stopped watching project {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping observer for project {project_id}: {e}", exc_info=True)
            return False

    def list_projects(self) -> Dict[str, str]:
        """Return a dictionary of watched projects and their paths."""
        return {pid: watcher.project_path for pid, watcher in self.watchers.items()}

    def stop_all(self):
        """Stop watching all projects."""
        for project_id in list(self.observers.keys()):
            self.remove_project(project_id)
        self.logger.info("Stopped watching all projects")

    def set_auto_update(self, project_id: str, enabled: bool) -> bool:
        """Enable or disable auto-update for a specific project.
        
        Args:
            project_id: The identifier of the project
            enabled: Whether to enable or disable auto-update
            
        Returns:
            True if successful, False if project is not being watched
        """
        if project_id in self.watchers:
            self.watchers[project_id].set_auto_update(enabled)
            return True
        else:
            self.logger.warning(f"Project {project_id} is not being watched")
            return False
    
    def update_project_rules(self, project_id: str) -> bool:
        """Manually trigger rules update for a specific project.
        
        Args:
            project_id: The identifier of the project
            
        Returns:
            True if successful, False if project is not being watched
        """
        if project_id in self.watchers:
            try:
                self.watchers[project_id]._update_rules()
                return True
            except Exception as e:
                self.logger.error(f"Error updating rules for project {project_id}: {e}", exc_info=True)
                return False
        else:
            self.logger.warning(f"Project {project_id} is not being watched")
            return False

def start_watching(project_paths: str | List[str], auto_update: bool = False) -> ProjectWatcherManager:
    """Start watching one or multiple project directories for changes.
    
    Args:
        project_paths: A string or list of paths to project directories
        auto_update: Whether to enable auto-update for the projects
        
    Returns:
        The ProjectWatcherManager instance
    """
    manager = ProjectWatcherManager()
    logger = logging.getLogger(__name__)
    
    if isinstance(project_paths, str):
        project_paths = [project_paths]
        
    for path in project_paths:
        try:
            project_id = manager.add_project(path)
            if auto_update:
                manager.set_auto_update(project_id, True)
        except Exception as e:
            logger.error(f"Failed to set up watcher for {path}: {e}", exc_info=True)
    
    return manager 