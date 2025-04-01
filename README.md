# CursorFocus

CursorFocus is a tool that automatically analyzes software codebases to generate dynamic context files (`Focus.md`, `.cursorrules`) specifically designed to enhance the code comprehension and code generation capabilities of the Cursor AI IDE.

## Main Features

- **Automatic Analysis**: Identify and analyze software projects
- **Context Optimization**: Generate `.cursorrules` and `Focus.md` files to optimize context for AI
- **Real-time Monitoring**: Track project changes and update context files
- **Google Gemini AI Integration**: Use AI to generate high-quality project context
- **Modern Interface**: Intuitive and user-friendly command-line interface

## Installation
[Install here](https://github.com/RenjiYuusei/CursorFocus/releases)

### Requirements

- Python 3.8 or higher
- Google Gemini API Key (obtained from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Install from source

1. Clone repository:
```
git clone https://github.com/yourusername/cursorfocus.git
cd cursorfocus
```

2. Install the dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
python cli.py
```

## Usage

### Setting up the project

1. From the main menu, select the "Setup new project" option

2. Enter the path to the project folder

3. Enter the project name (or leave it blank to use the folder name)

4. Add the Gemini Google API key when prompted

5. Optionally configure advanced options (update interval, scan depth)

### Scanning projects

1. Select the "Scan for projects" option from the main menu

2. Enter the folder path to scan for projects

3. Select the projects you want to add to the configuration

### Monitoring projects

1. Select the "Start monitoring" option from main menu

2. Select the projects you want to monitor

3. Optionally enable automatic updates when changes are made

4. Press Ctrl+C to stop monitoring

### Batch update

1. Select the "Batch update" option from the main menu

2. Select the projects you want to update

3. Wait for the update to complete

## Using the command line

CursorFocus also supports command line parameters for automated tasks:

```
usage: cli.py [-h] [--setup SETUP] [--monitor] [--scan SCAN] [--update] [--list]
[--batch-update] [--headless]

CursorFocus - Automatically analyze and create context for Cursor AI IDE

optional arguments:

-h, --help show this help message and exit
--setup SETUP, -s SETUP
Setup a project with the given path
--monitor, -m Start monitoring configured projects
--scan SCAN Scan directory for projects
--update, -u Check for updates
--list, -l List configured projects
--batch-update, -b Batch update all projects
--headless Run in headless mode without interactive prompts

```

## Project structure

- `cli.py` - Main command line interface
- `ui.py` - User interface components
- `core.py` - Core application functionality
- `config.py` - Configuration management
- `focus.py` - Creating and monitoring context files
- `analyzers.py` - Analyzing file content
- `rules_generator.py` - Creating .cursorrules files
- `content_generator.py` - Creating Focus.md files
- `project_detector.py` - Detecting project types

## Contribute

Contributing to the project is always welcome! Please create an issue or pull request on the GitHub repository.

## License

This project is distributed under the GPL-3.0 License.