import os
import requests
import json
import shutil
from datetime import datetime, timezone
import logging
import time
import traceback
from typing import Optional, Dict, Any, Tuple
import tempfile
import zipfile

def clear_console():
    """Clear console screen for different OS."""
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Unix/Linux/MacOS
    else:
        os.system('clear')

class AutoUpdater:
    def __init__(self, repo_url: str = "https://github.com/RenjiYuusei/CursorFocus"):
        self.repo_url = repo_url
        self.api_url = repo_url.replace("github.com", "api.github.com/repos")
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.keep_successful_backups = False  # Mặc định là không giữ lại

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check update from latest update with retry mechanism."""
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Check commit latest
                response = requests.get(f"{self.api_url}/commits/main", timeout=10)
                if response.status_code == 404:  
                    response = requests.get(f"{self.api_url}/commits/master", timeout=10)
                
                if response.status_code != 200:
                    logging.warning(f"Failed to get commits, status code: {response.status_code}")
                    retries += 1
                    if retries < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    return None

                latest_commit = response.json()
                current_commit = self._get_current_commit()
                
                if latest_commit['sha'] != current_commit:
                    # Convert UTC time to local time
                    utc_date = datetime.strptime(
                        latest_commit['commit']['author']['date'], 
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    local_date = utc_date.replace(tzinfo=timezone.utc).astimezone(tz=None)
                    formatted_date = local_date.strftime("%B %d, %Y at %I:%M %p")
                    
                    return {
                        'sha': latest_commit['sha'],
                        'message': latest_commit['commit']['message'],
                        'date': formatted_date,
                        'author': latest_commit['commit']['author']['name'],
                        'download_url': f"{self.repo_url}/archive/refs/heads/main.zip"
                    }
                
                return None

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

    def _get_current_commit(self) -> str:
        """Get the SHA of the current commit."""
        try:
            version_file = os.path.join(os.path.dirname(__file__), '.current_commit')
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    return f.read().strip()
            return ''
        except Exception as e:
            logging.warning(f"Failed to read current commit: {e}")
            return ''

    def _create_backup(self, dst_dir: str) -> Tuple[bool, str]:
        """Create a backup of the current project before updating."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(tempfile.gettempdir(), f"cursorfocus_backup_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            for item in os.listdir(dst_dir):
                src = os.path.join(dst_dir, item)
                dst = os.path.join(backup_dir, item)
                
                # Skip the backup directory itself and any temp files
                if os.path.isdir(src) and src == backup_dir:
                    continue
                
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
            
            return True, backup_dir
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            return False, ""

    def _restore_from_backup(self, backup_dir: str, dst_dir: str) -> bool:
        """Restore files from backup in case of update failure."""
        if not os.path.exists(backup_dir):
            logging.error(f"Backup directory does not exist: {backup_dir}")
            return False
            
        try:
            for item in os.listdir(backup_dir):
                src = os.path.join(backup_dir, item)
                dst = os.path.join(dst_dir, item)
                
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
            
            return True
        except Exception as e:
            logging.error(f"Failed to restore from backup: {e}")
            return False

    def _cleanup_backup(self, backup_dir: str) -> bool:
        """Clean up backup directory after successful update.
        
        Args:
            backup_dir: Path to backup directory
            
        Returns:
            bool: True if backup was successfully removed, False otherwise
        """
        if not backup_dir or not os.path.exists(backup_dir):
            logging.warning("No backup directory to clean up")
            return False
            
        try:
            logging.info(f"Removing backup directory at: {backup_dir}")
            shutil.rmtree(backup_dir)
            
            # Verify backup was actually removed
            if not os.path.exists(backup_dir):
                logging.info("Backup directory successfully removed")
                return True
            else:
                logging.warning("Backup directory still exists after removal attempt")
                return False
        except Exception as e:
            logging.warning(f"Failed to remove backup directory: {e}")
            logging.debug(traceback.format_exc())
            return False

    def update(self, update_info: Dict[str, Any]) -> bool:
        """Update from latest commit with backup and improved error handling."""
        temp_dir = None
        backup_dir = ""
        dst_dir = os.path.dirname(__file__)
        backup_created = False
        
        try:
            # Create backup first
            backup_created, backup_dir = self._create_backup(dst_dir)
            if not backup_created:
                logging.warning("Failed to create backup, proceeding without backup")
            
            # Download zip file of branch with retry mechanism
            retries = 0
            response = None
            
            while retries < self.max_retries:
                try:
                    response = requests.get(update_info['download_url'], timeout=30)
                    if response.status_code == 200:
                        break
                    
                    logging.warning(f"Download failed with status code: {response.status_code} (Attempt {retries+1}/{self.max_retries})")
                    retries += 1
                    if retries < self.max_retries:
                        time.sleep(self.retry_delay)
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    logging.warning(f"Connection issue when downloading update (Attempt {retries+1}/{self.max_retries})")
                    retries += 1
                    if retries < self.max_retries:
                        time.sleep(self.retry_delay)
                except Exception as e:
                    logging.error(f"Error downloading update: {e}")
                    raise
            
            if not response or response.status_code != 200:
                raise Exception(f"Failed to download update after {self.max_retries} attempts")

            # Save zip file temporarily
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'update.zip')
            with open(zip_path, 'wb') as f:
                f.write(response.content)

            # Unzip and update
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get root directory name in zip
                root_dir = zip_ref.namelist()[0].split('/')[0]
                zip_ref.extractall(temp_dir)

                # Copy new files
                src_dir = os.path.join(temp_dir, root_dir)
                
                for item in os.listdir(src_dir):
                    s = os.path.join(src_dir, item)
                    d = os.path.join(dst_dir, item)
                    if os.path.isfile(s):
                        shutil.copy2(s, d)
                    elif os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)

            # Save SHA of new commit
            with open(os.path.join(dst_dir, '.current_commit'), 'w') as f:
                f.write(update_info['sha'])

            # Clean up
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Only remove backup after successful update if it exists and if configured to do so
            if backup_created and backup_dir and not self.keep_successful_backups:
                logging.info("Update successful, cleaning up backup...")
                self._cleanup_backup(backup_dir)
            elif backup_created and self.keep_successful_backups:
                logging.info(f"Update successful, keeping backup at: {backup_dir}")
            
            # Clear console after successful update
            clear_console()
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