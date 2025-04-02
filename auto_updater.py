import os
import requests
import json
import shutil
from datetime import datetime, timezone
import logging
import time
import traceback
from typing import Optional, Dict, Any, Tuple, List
import tempfile
import zipfile
import platform
import re
import sys

def clear_console():
    """Clear console screen for different OS."""
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Unix/Linux/MacOS
    else:
        os.system('clear')

class AutoUpdater:
    """
    Auto-updater for CursorFocus project.
    Handles checking for updates, downloading, and applying them with backup support.
    """
    def __init__(self, repo_url: str = "https://github.com/RenjiYuusei/CursorFocus"):
        self.repo_url = repo_url
        self.api_url = repo_url.replace("github.com", "api.github.com/repos")
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.keep_successful_backups = False
        self.backup_dir = ""
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.current_version = self._get_current_version()
        self.system_info = self._get_system_info()

    def _get_current_version(self) -> str:
        """Get current version from config file or default."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('version', '1.0.0')
            return "1.0.0"  # Default version
        except Exception as e:
            logging.warning(f"Failed to read current version: {e}")
            return "1.0.0"

    def _save_version(self, version: str) -> bool:
        """Save version to config file."""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['version'] = version
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Failed to save version to config: {e}")
            return False

    def _update_version_file(self, version: str) -> bool:
        """Update version in .version file."""
        try:
            version_file = os.path.join(os.path.dirname(__file__), '.version')
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(version)
            return True
        except Exception as e:
            logging.error(f"Failed to update .version file: {e}")
            return False

    def _get_system_info(self) -> Dict[str, str]:
        """Get system information for update matching."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map system and architecture to GitHub release asset names
        system_map = {
            'windows': 'windows',
            'darwin': 'mac',
            'linux': 'linux'
        }
        
        arch_map = {
            'x86_64': 'x64',
            'arm64': 'arm64',
            'aarch64': 'arm64'
        }
        
        return {
            'system': system_map.get(system, system),
            'arch': arch_map.get(machine, machine)
        }

    def _parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """Parse version string into tuple of integers."""
        try:
            match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', version_str)
            if match:
                return tuple(map(int, match.groups()))
            return (0, 0, 0)
        except Exception:
            return (0, 0, 0)

    def _compare_versions(self, current: str, latest: str) -> bool:
        """Compare version strings, return True if latest is newer."""
        current_parts = self._parse_version(current)
        latest_parts = self._parse_version(latest)
        return latest_parts > current_parts

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        Check for updates from latest release with retry mechanism.
        
        Returns:
            Optional[Dict[str, Any]]: Update information or None if no updates available
        """
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Get latest release
                response = requests.get(f"{self.api_url}/releases/latest", timeout=10)
                
                if response.status_code != 200:
                    logging.warning(f"Failed to get latest release, status code: {response.status_code}")
                    retries += 1
                    if retries < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    return None

                release_info = response.json()
                latest_version = release_info['tag_name'].lstrip('v')
                
                # Check if update is needed
                if not self._compare_versions(self.current_version, latest_version):
                    logging.info("Current version is up to date")
                    return None
                
                # Find matching asset for current system
                system = self.system_info['system']
                arch = self.system_info['arch']
                
                # Base asset name pattern
                asset_name_base = f"CursorFocus_{latest_version}_{system}"
                
                matching_asset = None
                for asset in release_info['assets']:
                    # For Windows, the file might be named without arch or with .exe extension
                    if system == 'windows' and (asset['name'].startswith(asset_name_base) or 
                                               asset['name'] == f"CursorFocus_{latest_version}_windows.exe"):
                        matching_asset = asset
                        break
                    # For other platforms, match with architecture
                    elif asset['name'].startswith(f"{asset_name_base}_{arch}"):
                        matching_asset = asset
                        break
                
                if not matching_asset:
                    logging.warning(f"No matching asset found for {asset_name_base}")
                    return None
                
                # Convert UTC time to local time
                utc_date = datetime.strptime(
                    release_info['published_at'], 
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                local_date = utc_date.replace(tzinfo=timezone.utc).astimezone(tz=None)
                formatted_date = local_date.strftime("%B %d, %Y at %I:%M %p")
                
                # Create update info dictionary
                return {
                    'version': latest_version,
                    'message': release_info['body'],
                    'date': formatted_date,
                    'author': release_info['author']['login'],
                    'download_url': matching_asset['browser_download_url'],
                    'asset_name': matching_asset['name']
                }

            except requests.exceptions.Timeout:
                logging.warning(f"Timeout when checking for updates (Attempt {retries+1}/{self.max_retries})")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
            except requests.exceptions.ConnectionError:
                logging.warning(f"Connection error when checking for updates (Attempt {retries+1}/{self.max_retries})")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
            except Exception as e:
                logging.error(f"Error checking for updates: {e}")
                logging.debug(traceback.format_exc())
                return None
        
        logging.error("Failed to check for updates after multiple attempts")
        return None

    def _create_backup(self, dst_dir: str) -> Tuple[bool, str]:
        """
        Create a backup of the current project before updating.
        
        Args:
            dst_dir (str): Destination directory to back up
            
        Returns:
            Tuple[bool, str]: (success, backup_directory_path)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(tempfile.gettempdir(), f"cursorfocus_backup_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            for item in os.listdir(dst_dir):
                src = os.path.join(dst_dir, item)
                dst = os.path.join(backup_dir, item)
                
                # Skip the backup directory itself and temp files
                if os.path.isdir(src) and src == backup_dir:
                    continue
                
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
            
            self.backup_dir = backup_dir
            return True, backup_dir
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            return False, ""

    def _validate_zip_file(self, zip_path: str) -> bool:
        """
        Validate that the downloaded file is a proper zip file.
        
        Args:
            zip_path (str): Path to the downloaded zip file
            
        Returns:
            bool: True if file is a valid zip, False otherwise
        """
        try:
            if not os.path.exists(zip_path):
                logging.error("Zip file does not exist")
                return False
                
            # For Windows, we might get an .exe file directly, so check the file extension
            if platform.system().lower() == 'windows' and zip_path.lower().endswith('.exe'):
                logging.info("Downloaded file is an .exe executable, validation skipped")
                return True
                
            if not zipfile.is_zipfile(zip_path):
                logging.error("File is not a valid zip file")
                return False
                
            # Try opening the zip file to validate its contents
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check that zip has contents
                if len(zip_ref.namelist()) == 0:
                    logging.error("Zip file is empty")
                    return False
                    
                # Basic validation passed
                return True
        except zipfile.BadZipFile:
            logging.error("Downloaded file is not a valid zip archive")
            return False
        except Exception as e:
            logging.error(f"Error validating zip file: {e}")
            return False

    def _restore_from_backup(self, backup_dir: str, dst_dir: str) -> bool:
        """
        Restore files from backup in case of update failure.
        
        Args:
            backup_dir (str): Path to backup directory
            dst_dir (str): Destination directory to restore to
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(backup_dir):
            logging.error(f"Backup directory does not exist: {backup_dir}")
            return False
            
        try:
            failed_files = []
            
            for item in os.listdir(backup_dir):
                src = os.path.join(backup_dir, item)
                dst = os.path.join(dst_dir, item)
                
                try:
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                    elif os.path.isdir(src):
                        # Skip .git directory during restore if problems occur
                        if item == '.git':
                            try:
                                shutil.copytree(src, dst, dirs_exist_ok=True)
                            except Exception as git_error:
                                logging.warning(f"Failed to restore .git directory: {git_error}")
                                continue
                        else:
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                except Exception as copy_error:
                    failed_files.append((src, dst, str(copy_error)))
                    continue
            
            if failed_files:
                logging.error(f"Failed to restore from backup: {failed_files}")
                return False
            
            return True
        except Exception as e:
            logging.error(f"Failed to restore from backup: {e}")
            return False

    def _cleanup_backup(self, backup_dir: str) -> bool:
        """
        Clean up backup directory after successful update.
        
        Args:
            backup_dir (str): Path to backup directory
            
        Returns:
            bool: True if backup was successfully removed, False otherwise
        """
        if not backup_dir or not os.path.exists(backup_dir):
            logging.warning("No backup directory to clean up")
            return False
            
        try:
            logging.info(f"Removing backup directory at: {backup_dir}")
            
            # First attempt: try to handle .git directory separately on Windows
            if platform.system().lower() == 'windows':
                git_dir = os.path.join(backup_dir, '.git')
                if os.path.exists(git_dir):
                    logging.info("Handling .git directory separately on Windows")
                    try:
                        # Try removing read-only flags from .git directory
                        for root, dirs, files in os.walk(git_dir):
                            for file in files:
                                try:
                                    file_path = os.path.join(root, file)
                                    os.chmod(file_path, 0o777)  # Grant all permissions
                                except Exception:
                                    pass
                        
                        # Use a more robust method to remove .git directory on Windows
                        import subprocess
                        subprocess.run(['rmdir', '/S', '/Q', git_dir], shell=True, check=False)
                    except Exception as git_error:
                        logging.warning(f"Failed to remove .git directory: {git_error}")
                        # Continue with the rest of the cleanup even if .git removal fails
            
            # Second attempt: try removing the whole directory
            try:
                shutil.rmtree(backup_dir, ignore_errors=True)
            except Exception as e:
                logging.warning(f"Standard cleanup failed: {e}")
                
                # Final attempt: use OS-specific commands for stubborn directories
                if platform.system().lower() == 'windows':
                    try:
                        import subprocess
                        subprocess.run(['rmdir', '/S', '/Q', backup_dir], shell=True, check=False)
                    except Exception as cmd_error:
                        logging.warning(f"Command line cleanup failed: {cmd_error}")
                else:
                    try:
                        import subprocess
                        subprocess.run(['rm', '-rf', backup_dir], shell=True, check=False)
                    except Exception as cmd_error:
                        logging.warning(f"Command line cleanup failed: {cmd_error}")
            
            # Verify backup was actually removed
            if not os.path.exists(backup_dir):
                logging.info("Backup directory successfully removed")
                return True
            else:
                # If directory still exists but most content was removed, consider it a partial success
                remaining_items = len(os.listdir(backup_dir))
                if remaining_items == 0:
                    logging.info("Backup directory appears empty but not removed")
                    return True
                elif remaining_items <= 5:  # If only a few items remain
                    logging.warning(f"Backup directory partially removed ({remaining_items} items remain)")
                    return True
                else:
                    logging.warning(f"Backup directory still exists after removal attempt with {remaining_items} items")
                    return False
        except Exception as e:
            logging.warning(f"Failed to remove backup directory: {e}")
            logging.debug(traceback.format_exc())
            return False

    def _download_update(self, url: str, timeout: int = 30) -> Optional[bytes]:
        """
        Download update package with retry mechanism.
        
        Args:
            url (str): Download URL
            timeout (int): Connection timeout in seconds
            
        Returns:
            Optional[bytes]: Downloaded content or None on failure
        """
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    return response.content
                
                logging.warning(f"Download failed with status code: {response.status_code} (Attempt {retries+1}/{self.max_retries})")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logging.warning(f"Connection issue when downloading: {e} (Attempt {retries+1}/{self.max_retries})")
            
            retries += 1
            if retries < self.max_retries:
                time.sleep(self.retry_delay)
                
        return None

    def update(self, update_info: Dict[str, Any]) -> bool:
        """
        Update from latest release with backup and improved error handling.
        
        Args:
            update_info (Dict[str, Any]): Update information dictionary
            
        Returns:
            bool: Success status
        """
        temp_dir = None
        backup_dir = ""
        dst_dir = os.path.dirname(__file__)
        backup_created = False
        is_exe_update = False
        current_exe_path = None
        
        try:
            # Get current executable path if running from .exe
            if platform.system().lower() == 'windows' and getattr(sys, 'frozen', False):
                current_exe_path = sys.executable
                logging.info(f"Current executable path: {current_exe_path}")
            
            # Check if this is an .exe update for Windows
            if platform.system().lower() == 'windows' and update_info['asset_name'].lower().endswith('.exe'):
                is_exe_update = True
                logging.info("Detected executable update for Windows")
            
            # Create backup first
            backup_created, backup_dir = self._create_backup(dst_dir)
            if not backup_created:
                logging.warning("Failed to create backup, proceeding without backup")
            
            # Download update package
            content = self._download_update(update_info['download_url'])
            if not content:
                raise Exception(f"Failed to download update after {self.max_retries} attempts")

            # Save file temporarily
            temp_dir = tempfile.mkdtemp()
            
            # For .exe files, handle differently on Windows
            if is_exe_update:
                exe_path = os.path.join(temp_dir, update_info['asset_name'])
                with open(exe_path, 'wb') as f:
                    f.write(content)
                
                # For executable updates, we need to copy to a user-accessible location
                user_home = os.path.expanduser("~")
                downloads_dir = os.path.join(user_home, "Downloads")
                
                # Create destination path - ensure it exists
                if not os.path.exists(downloads_dir):
                    try:
                        os.makedirs(downloads_dir)
                    except:
                        downloads_dir = user_home  # Fallback to user home if downloads dir can't be created
                
                # Save executable to downloads folder
                dst_exe = os.path.join(downloads_dir, update_info['asset_name'])
                shutil.copy2(exe_path, dst_exe)
                
                # Log the destination path so user knows where to find it
                logging.info(f"New executable saved to: {dst_exe}")
                print(f"\nUpdate downloaded successfully!\nNew executable saved to: {dst_exe}")
                
                # Give execution permissions
                try:
                    os.chmod(dst_exe, 0o755)  # rwxr-xr-x
                except Exception as e:
                    logging.warning(f"Failed to set executable permission: {e}")

                # Create batch script to launch new version and delete old version
                if current_exe_path and os.path.exists(current_exe_path):
                    # Create batch file for starting new exe and removing old one
                    batch_file = os.path.join(downloads_dir, "update_and_clean.bat")
                    with open(batch_file, 'w') as f:
                        f.write('@echo off\n')
                        f.write('echo Cleaning up old version and starting new version...\n')
                        f.write(f'timeout /t 3 /nobreak > nul\n')  # Wait a bit for current process to exit
                        f.write(f'start "" "{dst_exe}"\n')  # Start new version
                        f.write(f'timeout /t 2 /nobreak > nul\n')  # Small delay
                        f.write(f'if exist "{current_exe_path}" del "{current_exe_path}"\n')  # Delete old version
                        f.write('exit\n')
                    
                    # Set executable permissions
                    try:
                        os.chmod(batch_file, 0o755)
                    except Exception as e:
                        logging.warning(f"Failed to set batch file permissions: {e}")
                    
                    # Start the batch file to handle cleanup after this process exits
                    import subprocess
                    subprocess.Popen(['start', 'cmd', '/c', batch_file], shell=True, close_fds=True)
                    print(f"\nRestarting with new version...")
                    
                    # Signal that we will auto-restart
                    logging.info("Auto-restart scheduled")
                    print("The application will restart automatically with the new version...")
                else:
                    # If we can't get current executable path, suggest manual restart
                    print(f"Please close this application and start the new version manually.")
                
                # Save new version to config file and .version file
                version_saved = self._save_version(update_info['version'])
                version_file_updated = self._update_version_file(update_info['version'])
                
                if not version_saved or not version_file_updated:
                    logging.warning("Failed to update one or more version files")
            else:
                # Standard zip handling
                zip_path = os.path.join(temp_dir, 'update.zip')
                with open(zip_path, 'wb') as f:
                    f.write(content)

                # Validate the downloaded zip file
                if not self._validate_zip_file(zip_path):
                    raise Exception("File is not a valid file for update")

                # Extract and update files
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Get root directory name in zip
                    root_dir = None
                    if len(zip_ref.namelist()) > 0:
                        first_item = zip_ref.namelist()[0]
                        # Handle both directory and file at root
                        if '/' in first_item:
                            root_dir = first_item.split('/')[0]
                    
                    zip_ref.extractall(temp_dir)

                    # Copy new files
                    src_dir = temp_dir
                    if root_dir:
                        src_dir = os.path.join(temp_dir, root_dir)
                    
                    # Check if source directory exists after extraction
                    if not os.path.exists(src_dir):
                        raise Exception(f"Extracted directory not found: {src_dir}")
                    
                    for item in os.listdir(src_dir):
                        s = os.path.join(src_dir, item)
                        d = os.path.join(dst_dir, item)
                        
                        # Skip .git directory during update
                        if item == '.git':
                            logging.info("Skipping .git directory during update")
                            continue
                            
                        if os.path.isfile(s):
                            shutil.copy2(s, d)
                        elif os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)

                # Save new version to config file and .version file
                version_saved = self._save_version(update_info['version'])
                version_file_updated = self._update_version_file(update_info['version'])
                
                if not version_saved or not version_file_updated:
                    logging.warning("Failed to update one or more version files")

            # Clean up temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Handle backup directory based on configuration
            if backup_created and backup_dir:
                if not self.keep_successful_backups:
                    logging.info("Update successful, cleaning up backup...")
                    self._cleanup_backup(backup_dir)
                else:
                    logging.info(f"Update successful, keeping backup at: {backup_dir}")
            
            return True

        except Exception as e:
            logging.error(f"Error updating: {e}")
            logging.debug(traceback.format_exc())
            
            # Attempt to restore from backup if it was created
            if backup_created and backup_dir:
                logging.info("Attempting to restore from backup...")
                if self._restore_from_backup(backup_dir, dst_dir):
                    logging.info("Successfully restored from backup")
                else:
                    logging.error("Failed to restore from backup")
            
            # Clean up temp directory if it exists
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    logging.warning(f"Failed to clean up temp directory: {cleanup_error}")
            
            return False
            
    def get_backup_path(self) -> str:
        """
        Get the path to the current backup directory.
        
        Returns:
            str: Path to backup directory
        """
        return self.backup_dir
        
    def configure(self, 
                  max_retries: Optional[int] = None, 
                  retry_delay: Optional[int] = None,
                  keep_backups: Optional[bool] = None) -> None:
        """
        Configure the updater settings.
        
        Args:
            max_retries (Optional[int]): Maximum number of retry attempts
            retry_delay (Optional[int]): Delay between retries in seconds
            keep_backups (Optional[bool]): Whether to keep successful backups
        """
        if max_retries is not None and max_retries > 0:
            self.max_retries = max_retries
            
        if retry_delay is not None and retry_delay > 0:
            self.retry_delay = retry_delay
            
        if keep_backups is not None:
            self.keep_successful_backups = keep_backups 