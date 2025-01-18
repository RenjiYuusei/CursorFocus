import os
from datetime import datetime
from analyzers import analyze_file_content, should_ignore_file, is_binary_file
from project_detector import detect_project_type, get_project_description, get_file_type_info
from config import (
    get_file_length_limit, 
    load_config, 
    FUNCTION_PATTERNS,
    IGNORED_KEYWORDS,
    CODE_EXTENSIONS,
    NON_CODE_EXTENSIONS
)
import re
import logging
from typing import Dict, List, Tuple, Set

class ProjectMetrics:
    def __init__(self):
        self.total_files = 0
        self.total_lines = 0
        self.files_by_type = {}
        self.lines_by_type = {}
        self.files_with_functions = []

def get_directory_structure(project_path: str, max_depth: int = 3, current_depth: int = 0, metrics: ProjectMetrics = None) -> Dict:
    """Get the directory structure with file information."""
    if current_depth > max_depth:
        return {}
    
    structure = {}
    try:
        for item in os.listdir(project_path):
            if should_ignore_file(item):
                continue
                
            item_path = os.path.join(project_path, item)
            
            if os.path.isdir(item_path):
                substructure = get_directory_structure(item_path, max_depth, current_depth + 1, metrics)
                if substructure:
                    structure[item] = substructure
            else:
                if is_binary_file(item_path):
                    continue
                    
                ext = os.path.splitext(item)[1].lower()
                if ext not in CODE_EXTENSIONS:
                    continue
                    
                functions, line_count = analyze_file_content(item_path)
                
                if metrics:
                    metrics.total_files += 1
                    metrics.files_by_type[ext] = metrics.files_by_type.get(ext, 0) + 1
                    metrics.lines_by_type[ext] = metrics.lines_by_type.get(ext, 0) + line_count
                    metrics.total_lines += line_count
                    
                    if functions:
                        # Remove duplicates and sort functions
                        unique_functions = list({func[0]: func for func in functions}.values())
                        unique_functions.sort(key=lambda x: x[0].lower())
                        metrics.files_with_functions.append((item_path, unique_functions, line_count))
                
                file_type, file_desc = get_file_type_info(item)
                structure[item] = {
                    'type': 'file',
                    'line_count': line_count,
                    'description': file_desc,
                    'functions': functions
                }
    except Exception as e:
        print(f"Error scanning directory {project_path}: {e}")
    
    return structure

def structure_to_tree(structure: Dict, prefix: str = '', project_path: str = '') -> List[str]:
    """Convert directory structure to tree format with file information."""
    lines = []
    items = sorted(list(structure.items()), key=lambda x: (isinstance(x[1], dict) and x[1].get('type') != 'file', x[0]))
    
    for i, (name, info) in enumerate(items):
        is_last = i == len(items) - 1
        connector = '└─ ' if is_last else '├─ '
        
        if isinstance(info, dict) and info.get('type') == 'file':
            icon = '📄 '
            file_info = f"{name} ({info['line_count']} lines) - {info['description']}"
            lines.append(f"{prefix}{connector}{icon}{file_info}")
        else:
            icon = '📁 '
            lines.append(f"{prefix}{connector}{icon}{name}")
            extension = '   ' if is_last else '│  '
            lines.extend(structure_to_tree(info, prefix + extension, os.path.join(project_path, name)))
    
    return lines

def generate_focus_content(project_path: str, config: Dict) -> str:
    """Generate the Focus file content."""
    metrics = ProjectMetrics()
    
    project_type = detect_project_type(project_path)
    project_info = get_project_description(project_path)
    
    content = [
        f"# Project Focus: {project_info['name']}",
        "",
        f"**Current Goal:** {project_info['description']}",
        "",
        "**Project Context:**",
        f"Type: {project_info['key_features'][1].replace('Type: ', '')}",
        f"Target Users: Users of {project_info['name']}",
        f"Main Functionality: {project_info['description']}",
        "Key Requirements:",
        *[f"- {feature}" for feature in project_info['key_features']],
        "",
        "**Development Guidelines:**",
        "- Keep code modular and reusable",
        "- Follow best practices for the project type",
        "- Maintain clean separation of concerns",
        "",
        "# 📁 Project Structure"
    ]
    
    # Add directory structure with integrated file information
    structure = get_directory_structure(project_path, config['max_depth'], metrics=metrics)
    content.extend(structure_to_tree(structure))
    
    # Add files with functions section
    if metrics.files_with_functions:
        content.extend([
            "",
            "# 🔍 Key Files with Methods"
        ])
        
        # Sort files by name
        metrics.files_with_functions.sort(key=lambda x: os.path.basename(x[0]).lower())
        
        for file_path, functions, line_count in metrics.files_with_functions:
            rel_path = os.path.relpath(file_path, project_path)
            
            # Filter out common Python special methods and built-ins
            filtered_functions = [
                func for func, _ in functions 
                if not (func.startswith('__') or func in ['set', 'get', 'items', 'exists', 'enumerate', 'input', 'int', 'next', 'detection', 'names', 'walk', 'endswith'])
            ]
            
            if filtered_functions:  # Only show files with non-special methods
                content.extend([
                    "",
                    f"`{rel_path}` ({line_count} lines)",
                    "Functions:",
                    *[f"- {func}" for func in sorted(filtered_functions)]
                ])
    
    # Add metrics summary
    file_dist = [f"- {ext}: {count} files ({metrics.lines_by_type[ext]:,} lines)" 
                 for ext, count in sorted(metrics.files_by_type.items())]
    
    content.extend([
        "",
        "# 📊 Project Overview",
        f"**Files:** {metrics.total_files}  |  **Lines:** {metrics.total_lines:,}",
        "",
        "## 📁 File Distribution"
    ] + file_dist + [
        "",
        f"*Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*"
    ])
    
    return '\n'.join(content)

def analyze_file_content(file_path: str) -> Tuple[List[Tuple[str, str]], int]:
    """Analyze file content for functions and metrics."""
    try:
        # Skip binary and non-code files
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in CODE_EXTENSIONS:
            return [], 0
            
        # Skip binary files
        if is_binary_file(file_path):
            return [], 0

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        functions = []
        for pattern_name, pattern in FUNCTION_PATTERNS.items():
            try:
                matches = re.finditer(pattern, content)
                for match in matches:
                    func_name = next(filter(None, match.groups()), None)
                    if func_name and func_name not in IGNORED_KEYWORDS:
                        functions.append((func_name, "Function detected"))
            except re.error as e:
                logging.debug(f"Invalid regex pattern {pattern_name} for {file_path}: {e}")
                continue
            except Exception as e:
                logging.debug(f"Error analyzing pattern {pattern_name} for {file_path}: {e}")
                continue
                
        return functions, len(content.splitlines())
        
    except UnicodeDecodeError:
        logging.debug(f"Unable to read {file_path} as text file")
        return [], 0
    except Exception as e:
        logging.debug(f"Error analyzing file {file_path}: {e}")
        return [], 0 