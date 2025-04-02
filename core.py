#!/usr/bin/env python3
import os
import sys
import time
import json
import logging
from threading import Thread
from datetime import datetime
import shutil
import platform

# Import necessary modules from the project
from config import load_config, get_default_config, save_config
from content_generator import generate_focus_content
from rules_analyzer import RulesAnalyzer
from rules_generator import RulesGenerator
from rules_watcher import ProjectWatcherManager
from auto_updater import AutoUpdater
from project_detector import scan_for_projects
from focus import setup_cursor_focus, monitor_project, retry_generate_rules

class CursorFocusCore:
    """Core functionality for CursorFocus application."""
    
    @staticmethod
    def setup_project(project_path, project_name=None, update_interval=60, max_depth=3):
        """
        Set up a new project.
        
        Args:
            project_path (str): Path to the project
            project_name (str, optional): Name of the project. Defaults to the directory name.
            update_interval (int, optional): Update interval in seconds. Defaults to 60.
            max_depth (int, optional): Maximum directory depth. Defaults to 3.
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Convert to absolute path
            project_path = os.path.abspath(project_path)
            
            # Validate path
            if not os.path.exists(project_path):
                return False, f"Path does not exist: {project_path}"
            
            # Get name from directory if not provided
            if not project_name:
                project_name = os.path.basename(os.path.normpath(project_path))
            
            # Setup the project
            setup_cursor_focus(project_path, project_name)
            
            # Update config
            config = load_config()
            if not config:
                config = get_default_config()
            
            if 'projects' not in config:
                config['projects'] = []
                
            # Check if project already exists
            existing_project = next((p for p in config['projects'] if p['project_path'] == project_path), None)
            
            if existing_project:
                # Update existing project
                existing_project.update({
                    'name': project_name,
                    'update_interval': update_interval,
                    'max_depth': max_depth
                })
                
                # Save config
                save_config(config)
                return True, f"Updated existing project: {project_name}"
            else:
                # Add new project
                config['projects'].append({
                    'name': project_name,
                    'project_path': project_path,
                    'update_interval': update_interval,
                    'max_depth': max_depth
                })
                
                # Save config
                save_config(config)
                return True, f"Successfully setup: {project_name}"
                
        except Exception as e:
            return False, f"Error setting up project: {str(e)}"
    
    @staticmethod
    def find_projects(scan_path, max_depth=3):
        """
        Scan for projects in a given path.
        
        Args:
            scan_path (str): Path to scan for projects
            max_depth (int, optional): Maximum scan depth. Defaults to 3.
            
        Returns:
            list: List of found projects
        """
        # Convert to absolute path
        scan_path = os.path.abspath(scan_path)
        
        # Check if path exists
        if not os.path.exists(scan_path):
            return []
        
        # Scan for projects
        return scan_for_projects(scan_path, max_depth)
    
    @staticmethod
    def batch_update_projects(projects, use_progress_callback=None):
        """
        Update multiple projects at once.
        
        Args:
            projects (list): List of project configurations to update
            use_progress_callback (callable, optional): Callback function for progress updates
            
        Returns:
            tuple: (success_count, total_count, errors)
        """
        success_count = 0
        errors = []
        total = len(projects)
        
        for i, project in enumerate(projects, 1):
            try:
                # Update progress if callback provided
                if use_progress_callback:
                    use_progress_callback(i, total, project['name'], "setup")
                
                # Update .cursorrules
                setup_cursor_focus(project['project_path'], project['name'])
                
                # Update progress for Focus.md if callback provided
                if use_progress_callback:
                    use_progress_callback(i, total, project['name'], "generating")
                
                # Update Focus.md
                config = load_config()
                content = generate_focus_content(project['project_path'], config)
                focus_file = os.path.join(project['project_path'], 'Focus.md')
                with open(focus_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                success_count += 1
                
            except Exception as e:
                errors.append((project['name'], str(e)))
        
        return success_count, total, errors
    
    @staticmethod
    def start_monitoring(projects, auto_update=False, 
                         on_update_callback=None, on_error_callback=None):
        """
        Start monitoring projects for changes.
        
        Args:
            projects (list): List of project configurations to monitor
            auto_update (bool, optional): Whether to auto-update on changes. Defaults to False.
            on_update_callback (callable, optional): Callback for update events
            on_error_callback (callable, optional): Callback for error events
            
        Returns:
            tuple: (threads, watchers)
        """
        threads = []
        watchers = []
        config = load_config()
        
        # Setup projects
        for project in projects:
            try:
                setup_cursor_focus(project['project_path'], project['name'])
                
                # Create a monitoring thread
                thread = Thread(
                    target=monitor_project,
                    args=(project, config),
                    daemon=True
                )
                thread.start()
                threads.append((thread, project))
                
                if on_update_callback:
                    on_update_callback(project['name'], "Monitoring started")
                    
            except Exception as e:
                if on_error_callback:
                    on_error_callback(project['name'], str(e))
        
        # Start watching for changes if auto-update enabled
        if auto_update:
            watcher = ProjectWatcherManager()
            for project in projects:
                watcher.add_project(project['project_path'], project['name'])
            watchers.append(watcher)
        
        return threads, watchers
    
    @staticmethod
    def check_for_updates():
        """
        Check for CursorFocus updates.
        
        Returns:
            dict: Update information or None if no updates available
        """
        updater = AutoUpdater()
        return updater.check_for_updates()
    
    @staticmethod
    def apply_update(update_info):
        """
        Apply a CursorFocus update.
        
        Args:
            update_info (dict): Update information
            
        Returns:
            bool: Success status
        """
        try:
            updater = AutoUpdater()
            result = updater.update(update_info)
            
            # Check if this is a Windows .exe update and show additional info
            if platform.system().lower() == 'windows' and update_info['asset_name'].lower().endswith('.exe'):
                user_home = os.path.expanduser("~")
                downloads_dir = os.path.join(user_home, "Downloads")
                exe_path = os.path.join(downloads_dir, update_info['asset_name'])
                
                if os.path.exists(exe_path):
                    logging.info(f"Update executable saved to: {exe_path}")
                    
                    # Check if running from executable
                    if getattr(sys, 'frozen', False):
                        logging.info("Running from frozen executable, cleanup will be handled automatically")
                        # The cleanup is now handled by the batch script in AutoUpdater
                        success_message = "Update successful! The application will restart automatically with the new version."
                    else:
                        # For non-frozen environments
                        logging.info("Not running from executable, showing manual instruction")
                        # This will be shown in terminal mode
                        print(f"\nIMPORTANT: The updated executable has been downloaded to:\n{exe_path}")
                        success_message = f"Update successful! The updated executable has been downloaded to:\n{exe_path}"
            
            if not result:
                # If update failed, get the backup path for possible manual recovery
                backup_path = updater.get_backup_path()
                logging.error(f"Update failed. Backup is available at: {backup_path}" if backup_path else "Update failed and no backup path is available.")
            return result
        except Exception as e:
            import traceback
            logging.error(f"Error during update: {str(e)}")
            logging.debug(traceback.format_exc())
            return False
    
    @staticmethod
    def configure_updater(max_retries=None, retry_delay=None, keep_backups=None):
        """
        Configure the AutoUpdater settings.
        
        Args:
            max_retries (int, optional): Maximum number of retry attempts
            retry_delay (int, optional): Delay between retries in seconds
            keep_backups (bool, optional): Whether to keep successful backups
            
        Returns:
            None
        """
        updater = AutoUpdater()
        updater.configure(max_retries, retry_delay, keep_backups)
    
    @staticmethod
    def setup_gemini_api_key(api_key):
        """
        Save the Gemini API key to .env file.
        
        Args:
            api_key (str): API key
            
        Returns:
            bool: Success status
        """
        from dotenv import set_key, load_dotenv
        
        # Validate API key input
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            logging.error("Invalid API key: Cannot be empty or non-string type")
            return False
        
        # Normalize API key by removing whitespace
        api_key = api_key.strip()
        
        try:
            # Get the path to the .env file
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            
            # Create or update the .env file
            if not os.path.exists(env_path):
                # Create new .env file if it doesn't exist
                logging.info(f"Creating new .env file at {env_path}")
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(f"GEMINI_API_KEY={api_key}")
            else:
                # Update existing .env file
                logging.info("Updating existing .env file with new API key")
                set_key(env_path, "GEMINI_API_KEY", api_key)
            
            # Reload environment variables
            load_dotenv(override=True)
            
            # Set environment variable directly for current session
            os.environ["GEMINI_API_KEY"] = api_key
            
            logging.info("API key successfully saved")
            return True
                
        except IOError as e:
            logging.error(f"IO error saving API key: {str(e)}")
            return False
        except PermissionError as e:
            logging.error(f"Permission error saving API key: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error saving API key: {str(e)}")
            return False
    
    @staticmethod
    def fetch_gemini_models():
        """
        Fetch available Gemini models.
        
        Returns:
            list: List of available Gemini models or None if error occurs
        """
        try:
            import google.generativeai as genai
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv()
            
            # Get API key from environment variable
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key or not api_key.strip():
                logging.error("No valid API key found in environment variables")
                return None
            
            # Configure Gemini API with the API key
            genai.configure(api_key=api_key)
            
            try:
                # Use standard API call without modifying internal client
                models = genai.list_models()
            except Exception as e:
                logging.error(f"Error calling Gemini API: {str(e)}")
                return None
            
            # Filter for Gemini models and sort by name
            gemini_models = [model.name for model in models if 'gemini' in model.name.lower()]
            gemini_models.sort(key=lambda x: x.lower())
            
            # Return empty list if no Gemini models were found
            if not gemini_models:
                logging.warning("No Gemini models found in available models")
                return []
                
            logging.info(f"Successfully fetched {len(gemini_models)} Gemini models")
            return gemini_models
            
        except ImportError as e:
            logging.error(f"Required package not installed: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error fetching Gemini models: {str(e)}")
            return None
    
    @staticmethod
    def set_gemini_model(model_name):
        """
        Set the Gemini model to use.
        
        Args:
            model_name (str): Model name
            
        Returns:
            bool: Success status
        """
        try:
            from dotenv import set_key, load_dotenv
            
            # Validate model name
            if not model_name or not isinstance(model_name, str) or not model_name.strip():
                logging.error("Invalid model name: Cannot be empty or non-string type")
                return False
                
            # Normalize model name
            model_name = model_name.strip()
            
            # Save model name to .env file
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            if not os.path.exists(env_path):
                # Create new .env file if it doesn't exist
                logging.info(f"Creating new .env file at {env_path}")
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(f"GEMINI_MODEL={model_name}")
            else:
                # Update existing .env file
                logging.info(f"Setting Gemini model to: {model_name}")
                set_key(env_path, "GEMINI_MODEL", model_name)
            
            # Reload environment variables
            load_dotenv(override=True)
            
            # Set environment variable directly for current session
            os.environ["GEMINI_MODEL"] = model_name
            
            logging.info("Model successfully saved and loaded")
            return True
                
        except IOError as e:
            logging.error(f"IO error setting Gemini model: {str(e)}")
            return False
        except PermissionError as e:
            logging.error(f"Permission error setting Gemini model: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Error setting Gemini model: {str(e)}")
            return False
    
    @staticmethod
    def update_project_settings(project_index, name=None, path=None, update_interval=None, max_depth=None):
        """
        Update a project's settings.
        
        Args:
            project_index (int): Index of the project in the config
            name (str, optional): New project name
            path (str, optional): New project path
            update_interval (int, optional): New update interval
            max_depth (int, optional): New max depth
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Load config
            config = load_config()
            if not config or 'projects' not in config or project_index >= len(config['projects']):
                return False, "Invalid project"
            
            project = config['projects'][project_index]
            
            # Update fields
            if name:
                project['name'] = name
            
            if path:
                path = os.path.abspath(path)
                project['project_path'] = path
            
            if update_interval is not None:
                project['update_interval'] = max(10, int(update_interval))
            
            if max_depth is not None:
                project['max_depth'] = max(1, int(max_depth))
            
            # Save config
            save_config(config)
            return True, f"Project {project['name']} updated successfully"
            
        except Exception as e:
            return False, f"Error updating project: {str(e)}"
    
    @staticmethod
    def remove_projects(indices=None, remove_all=False):
        """
        Remove projects from the configuration.
        
        Args:
            indices (list, optional): List of project indices to remove
            remove_all (bool, optional): Whether to remove all projects
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Load config
            config = load_config()
            if not config or 'projects' not in config or not config['projects']:
                return False, "No projects configured"
            
            if remove_all:
                removed_count = len(config['projects'])
                config['projects'] = []
                save_config(config)
                return True, f"Removed all {removed_count} projects"
            
            if not indices:
                return False, "No projects selected for removal"
            
            # Validate indices
            if any(i < 0 or i >= len(config['projects']) for i in indices):
                return False, "Invalid project indices"
            
            # Remove selected projects
            removed = []
            remaining = []
            
            for i, project in enumerate(config['projects']):
                if i in indices:
                    removed.append(project['name'])
                else:
                    remaining.append(project)
            
            config['projects'] = remaining
            save_config(config)
            
            return True, f"Removed projects: {', '.join(removed)}"
            
        except Exception as e:
            return False, f"Error removing projects: {str(e)}" 