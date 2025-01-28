# Instruction for using CursorFocus

## Table of Contents
1. [Installation](#installation)
2. [Setup API Key](#setup-api-key)
3. [Basic Usage](#basic-usage)
4. [Created Files](#created-files)
5. [Feature Detail](#feature-detail)
6. [Feature Advanced](#feature-advanced)
7. [Troubleshooting](#troubleshooting)

## Installation

### System Requirements
- Python 3.10+
- Gemini API Key

### Way 1: Automatic Installation (Recommended)
1. Open PowerShell and run the following command:
```powershell
irm https://raw.githubusercontent.com/RenjiYuusei/CursorFocus/refs/heads/main/install.ps1 | iex
```

### Way 2: Manual Installation
1. Clone repository to your machine
2. Move to project directory:
```bash
cd CursorFocus
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Setup API Key

1. Access [Google AI Studio](https://makersuite.google.com/app/apikey) to get API key
2. Set up API key by one of the following ways:

### Way 1: Use .env file
1. Create `.env` file in the root directory of the project
2. Add the following line to the file:
```
GEMINI_API_KEY=your_api_key_here
```

### Way 2: Set up environment variable
- Windows:
```bash
set GEMINI_API_KEY=your_api_key_here
```
- Mac/Linux:
```bash
export GEMINI_API_KEY=your_api_key_here
```

## Basic Usage

1. Set up project:
```bash
python setup.py --p path/to/your/project
```

2. Run CursorFocus:
```bash
python focus.py
```

## Created Files

### 1. Focus.md
This file contains:
- Summary of project
- Directory structure
- Description of files
- List and description of functions
- Warning about file length

### 2. .cursorrules
This file contains:
- Cursor setup for project
- Auto update when project changes
- Format: JSON or Markdown

## Feature Detail

### 1. Monitor Project Structure
- Auto update every 60 seconds
- Display directory structure as a tree
- Detect changes in project

### 2. Analyze Code
- Identify and describe important functions
- Check file length according to standard
- Detect project type
- Auto add project with name from directory name
### 3. Create Rules Automatically
- Use AI to create rules
- Auto adjust the rules according to the project type
- Up to date when there is a change

## Feature Advanced

### Manage Projects with setup.py

```bash
# List all configured projects
python setup.py --list

# Scan directory for projects
python setup.py --scan [directory_path]

# Remove specific projects
python setup.py --remove project_name_or_index

# Remove all projects
python setup.py --remove all

# Show project details
python setup.py --info project_name_or_index

# Export configuration
python setup.py --export config_backup.json

# Import configuration
python setup.py --import config_backup.json

# Set custom update interval (in seconds)
python setup.py --p project_path --update-interval 120

# Set maximum directory scan depth
python setup.py --p project_path --max-depth 5

# Add project automatically get name from directory name
python setup.py --p project_path

# Add multiple projects with custom names
python setup.py --projects path1 path2 --names "Project1" "Project2"
```

### Advanced Parameters for setup.py

| Parameter | Description |
|---------|--------|
| `--projects`, `-p` | Path to projects to monitor |
| `--names`, `-n` | Custom names for projects |
| `--list`, `-l` | List all configured projects |
| `--remove`, `-r` | Delete project by name/index or all |
| `--scan`, `-s` | Scan directory to find projects |
| `--update-interval`, `-u` | Set update interval (seconds) |
| `--max-depth`, `-d` | Set maximum directory depth for scanning |
| `--info`, `-i` | Show detailed information about a project |
| `--export`, `-e` | Export configuration to a file |
| `--import`, `-m` | Import configuration from a file |

### Example Usage

1. **Scan and Add Projects Automatically**
   ```bash
   # Scan current directory
   python setup.py --scan .
   
   # Scan specific directory
   python setup.py --scan "D:/Projects"
   ```

2. **Manage Multiple Projects**
   ```bash
   # Add multiple projects at once
   python setup.py --projects "path/to/project1" "path/to/project2" --names "Frontend" "Backend"
   
   # View list of projects
   python setup.py --list
   
   # Delete specific project
   python setup.py --remove "CursorFocus"
   ```

3. **Backup and Restore Configuration**
   ```bash
   # Backup configuration
   python setup.py --export backup.json
   
   # Restore configuration
   python setup.py --import backup.json
   ```

4. **Customize Project Configuration**
   ```bash
   # Set update interval to 2 minutes and scan depth to 4 levels
   python setup.py --p "path/to/project" --update-interval 120 --max-depth 4
   ```

## Troubleshooting

### API Key Issue
1. Check if API key is set correctly
2. Ensure API key is still valid
3. Try resetting API key

### Error When Running
1. Check Python version (3.10+)
2. Ensure all dependencies are installed
3. Check directory access

### Update No Work
1. Check internet connection
2. Ensure process is running
3. Check logs for detailed error

---
For further assistance, please join [Discord](https://discord.gg/n6fbdrz8sw).