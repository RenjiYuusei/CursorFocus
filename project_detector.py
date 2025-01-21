import os
import json
import re
from config import load_config
import time
from typing import List, Dict, Any

# Load project types from config at module level
_config = load_config()

# Project type definitions with improved structure
PROJECT_TYPES = {
    'python': {
        'description': 'Python Project',
        'indicators': ['setup.py', 'requirements.txt', 'Pipfile', 'pyproject.toml', 'poetry.lock', 'venv/', '.venv/'],
        'file_patterns': ['*.py'],
        'required_files': [],
        'priority': 10,
        'additional_checks': [
            lambda path: any(f.endswith('.py') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'javascript': {
        'description': 'JavaScript/Node.js Project', 
        'indicators': ['package.json', 'package-lock.json', 'yarn.lock', 'node_modules/', 'webpack.config.js', '.npmrc', '.nvmrc', 'next.config.js'],
        'file_patterns': ['*.js', '*.jsx', '*.mjs', '*.cjs'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith(('.js', '.jsx', '.mjs', '.cjs')) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'typescript': {
        'description': 'TypeScript Project',
        'indicators': ['tsconfig.json', 'tslint.json', 'typescript.json', '.ts', '.tsx', '.eslintrc'],
        'file_patterns': ['*.ts', '*.tsx'],
        'required_files': [],
        'priority': 6,  # Higher than JS because TS projects often have JS files too
        'additional_checks': [
            lambda path: any(f.endswith(('.ts', '.tsx')) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'web': {
        'description': 'Web Project',
        'indicators': ['index.html', 'styles.css', '.html', '.css', 'public/', 'assets/', 'images/'],
        'file_patterns': ['*.html', '*.css', '*.scss', '*.sass', '*.less', '*.svg'],
        'required_files': [],
        'priority': 3
    },
    'php': {
        'description': 'PHP Project',
        'indicators': ['composer.json', 'composer.lock', 'artisan', '.php', 'vendor/'],
        'file_patterns': ['*.php'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.php') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'cpp': {
        'description': 'C++ Project',
        'indicators': ['CMakeLists.txt', 'makefile', 'Makefile', '.sln', '.vcxproj', 'compile_commands.json'],
        'file_patterns': ['*.cpp', '*.hpp', '*.cc', '*.h', '*.cxx', '*.hxx'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith(('.cpp', '.hpp', '.cc', '.cxx', '.h', '.hxx')) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'java': {
        'description': 'Java Project',
        'indicators': ['pom.xml', 'build.gradle', 'settings.gradle', 'gradlew', 'mvnw', '.classpath', '.project'],
        'file_patterns': ['*.java', '*.jar'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.java') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'csharp': {
        'description': 'C# Project',
        'indicators': ['.sln', '.csproj', '.cs', 'packages.config', 'NuGet.Config', 'bin/Debug/', 'bin/Release/'],
        'file_patterns': ['*.cs'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.cs') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'go': {
        'description': 'Go Project',
        'indicators': ['go.mod', 'go.sum', 'go.work', 'vendor/'],
        'file_patterns': ['*.go'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.go') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'rust': {
        'description': 'Rust Project',
        'indicators': ['Cargo.toml', 'Cargo.lock', 'rust-toolchain.toml', 'target/'],
        'file_patterns': ['*.rs'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.rs') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'swift': {
        'description': 'Swift Project',
        'indicators': ['Package.swift', '*.xcodeproj', '*.xcworkspace', '*.pbxproj', 'Pods/'],
        'file_patterns': ['*.swift'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.swift') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'ruby': {
        'description': 'Ruby Project',
        'indicators': ['Gemfile', 'Rakefile', '*.rb', '.ruby-version', 'config.ru'],
        'file_patterns': ['*.rb', '*.erb'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith(('.rb', '.erb')) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'kotlin': {
        'description': 'Kotlin Project',
        'indicators': ['*.kt', 'build.gradle.kts', '.kt'],
        'file_patterns': ['*.kt', '*.kts'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith(('.kt', '.kts')) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'zig': {
        'description': 'Zig Project',
        'indicators': ['build.zig', 'zig.mod'],
        'required_files': [],
        'priority': 5
    },
    'rush': {
        'description': 'Rush Project',
        'indicators': ['rush.json', '.rush'],
        'required_files': [],
        'priority': 5
    },
    'perl': {
        'description': 'Perl Project',
        'indicators': ['*.pl', '*.pm', 'cpanfile'],
        'required_files': [],
        'priority': 5
    },
    'groovy': {
        'description': 'Groovy Project',
        'indicators': ['*.groovy', 'build.gradle', 'settings.gradle'],
        'required_files': [],
        'priority': 5
    },
    'lua': {
        'description': 'Lua Project',
        'indicators': ['*.lua', 'init.lua', 'main.lua', 'rockspec'],
        'required_files': [],
        'priority': 5
    }
}

# Add cache for scan results with expiration
_scan_cache = {}
CACHE_EXPIRATION = 300  # 5 minutes

IGNORED_DIRECTORIES = {
    '.git',
    '.github', 
    '__pycache__',
    'node_modules',
    'venv',
    '.venv',
    'env',
    '.env',
    'dist',
    'build',
    '.idea',
    '.vscode'
}

def detect_project_type(project_path):
    """Detect project type with improved accuracy."""
    if not os.path.exists(project_path):
        return _get_generic_result()
        
    try:
        files = os.listdir(project_path)
        files_set = set(files)  # For faster lookups
    except (PermissionError, OSError):
        return _get_generic_result()

    # Get all files recursively up to depth 2 for better detection
    all_files = _get_files_recursive(project_path, max_depth=2)
    
    project_type = 'generic'
    max_priority = -1
    matched_files = []
    
    # Check each project type
    for type_name, rules in PROJECT_TYPES.items():
        priority = rules.get('priority', 0)
        matched = False
        type_matched_files = []
        
        # Check direct indicators (files/folders that strongly indicate a project type)
        for indicator in rules.get('indicators', []):
            if _check_indicator(indicator, files_set, all_files):
                matched = True
                type_matched_files.append(indicator)
                
        # Check file patterns if no direct indicators found
        if not matched and 'file_patterns' in rules:
            for pattern in rules['file_patterns']:
                matching_files = _find_matching_files(pattern, all_files)
                if matching_files:
                    matched = True
                    type_matched_files.extend(matching_files)
                    
        # Check required files if specified
        if rules.get('required_files'):
            if not all(f in files_set for f in rules['required_files']):
                matched = False
                
        # Run additional checks if specified
        if matched and rules.get('additional_checks'):
            try:
                matched = all(check(project_path) for check in rules['additional_checks'])
            except Exception:
                matched = False
                
        # Update project type if this match has higher priority
        if matched and priority > max_priority:
            project_type = type_name
            max_priority = priority
            matched_files = type_matched_files

    # Detect language and framework
    language, framework = detect_language_and_framework(project_path)
    
    # If no specific type detected, check for common development patterns
    if project_type == 'generic':
        project_type = _detect_generic_project_type(files_set, all_files)
    
    result = {
        'type': project_type,
        'language': language,
        'framework': framework,
        'description': PROJECT_TYPES.get(project_type, {'description': 'Generic Project'})['description'],
        'matched_files': matched_files,
        'path': project_path
    }
    
    return result

def _get_generic_result():
    """Return a generic project result."""
    return {
        'type': 'generic',
        'language': 'unknown',
        'framework': 'none',
        'description': 'Generic Project',
        'matched_files': [],
        'path': ''
    }

def _get_files_recursive(path, max_depth=2, current_depth=0):
    """Get all files recursively up to max_depth."""
    if current_depth > max_depth:
        return set()
        
    try:
        files = set()
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    files.add(entry.name)
                elif entry.is_dir() and not entry.name.startswith('.'):
                    subfiles = _get_files_recursive(entry.path, max_depth, current_depth + 1)
                    files.update(f"{entry.name}/{f}" for f in subfiles)
        return files
    except (PermissionError, OSError):
        return set()

def _check_indicator(indicator, files_set, all_files):
    """Check if an indicator matches any files."""
    if '*' in indicator:
        pattern = indicator.replace('.', '[.]').replace('*', '.*')
        return any(re.match(pattern + '$', f) for f in all_files)
    return indicator in files_set

def _find_matching_files(pattern, files):
    """Find files matching a pattern."""
    if '*' in pattern:
        pattern = pattern.replace('.', '[.]').replace('*', '.*')
        return [f for f in files if re.match(pattern + '$', f)]
    return [f for f in files if f == pattern]

def _detect_generic_project_type(files_set, all_files):
    """Detect if a generic project has any development patterns."""
    dev_indicators = {
        'docs': ['README.md', 'CONTRIBUTING.md', 'docs/', 'documentation/'],
        'vcs': ['.git/', '.svn/', '.hg/'],
        'tests': ['test/', 'tests/', 'spec/', 'specs/'],
        'config': ['.env', 'config/', 'settings/'],
        'build': ['build/', 'dist/', 'target/']
    }
    
    matched_categories = set()
    
    for category, indicators in dev_indicators.items():
        if any(ind in files_set or any(f.startswith(ind) for f in all_files) for ind in indicators):
            matched_categories.add(category)
            
    return 'generic_dev' if matched_categories else 'generic'

def detect_language_and_framework(project_path):
    """Detect primary language and framework of a project."""
    try:
        files = os.listdir(project_path)
    except:
        return 'unknown', 'none'
        
    # Language detection based on file extensions and key files
    language_indicators = {
        'python': ['.py', 'requirements.txt', 'setup.py', 'Pipfile'],
        'javascript': ['.js', 'package.json'],
        'typescript': ['.ts', '.tsx', 'tsconfig.json'],
        'kotlin': ['.kt', 'build.gradle.kts'],
        'php': ['.php', 'composer.json'],
        'swift': ['.swift', 'Package.swift'],
        'cpp': ['.cpp', '.hpp', '.cc', '.cxx'],
        'c': ['.c', '.h'],
        'csharp': ['.cs', '.csproj', '.sln'],
        'ruby': ['.rb', 'Gemfile'],
        'go': ['.go', 'go.mod'],
        'zig': ['.zig', 'build.zig'],
        'rush': ['.rush', 'rush.json'],
        'perl': ['.pl', '.pm', 'cpanfile'],
        'matlab': ['.m', '.mat', '.mlx'],
        'groovy': ['.groovy', 'build.gradle'],
        'lua': ['.lua', 'init.lua', 'main.lua']
    }
    
    # Framework detection based on specific files/directories
    framework_indicators = {
        'django': ['manage.py', 'django.contrib'],
        'flask': ['flask', 'Flask=='],
        'fastapi': ['fastapi'],
        'react': ['react', 'React.'],
        'express': ['express'],
        'dotnet': ['Microsoft.NET.Sdk'],
        'qt': ['Qt.', 'QtCore'],
        'gtk': ['gtk', 'Gtk'],
        'unity': ['UnityEngine'],
        'unreal': ['UE4', 'UE5'],
        'pytorch': ['torch', 'pytorch'],
        'tensorflow': ['tensorflow'],
        'rails': ['rails', 'Rails'],
        'spring': ['spring-boot', 'SpringBoot'],
        'laravel': ['laravel', 'Laravel'],
        'gin': ['gin-gonic/gin'],
        'love2d': ['love.'],
        'corona': ['corona.']
    }
    
    # Detect language
    detected_language = 'unknown'
    max_matches = 0
    
    for lang, indicators in language_indicators.items():
        matches = 0
        for f in files:
            if any(f.endswith(ind) if ind.startswith('.') else ind in f for ind in indicators):
                matches += 1
        if matches > max_matches:
            max_matches = matches
            detected_language = lang
            
    # Detect framework by checking file contents
    detected_framework = 'none'
    for framework, indicators in framework_indicators.items():
        for f in files:
            if f in ['requirements.txt', 'package.json', 'composer.json']:
                try:
                    with open(os.path.join(project_path, f), 'r') as file:
                        content = file.read().lower()
                        if any(ind.lower() in content for ind in indicators):
                            detected_framework = framework
                            break
                except:
                    continue
                    
    return detected_language, detected_framework

def get_file_type_info(filename):
    """Get file type information."""
    ext = os.path.splitext(filename)[1].lower()
    
    type_map = {
        '.py': ('Python Source', 'Python script containing project logic'),
        '.js': ('JavaScript', 'JavaScript file for client-side functionality'),
        '.ts': ('TypeScript', 'TypeScript source file'),
        '.tsx': ('TypeScript/React', 'React component with TypeScript'),
        '.kt': ('Kotlin Source', 'Kotlin implementation file'),
        '.php': ('PHP Source', 'PHP script for server-side functionality'),
        '.swift': ('Swift Source', 'Swift implementation file'),
        '.cpp': ('C++ Source', 'C++ implementation file'),
        '.hpp': ('C++ Header', 'C++ header file'),
        '.c': ('C Source', 'C implementation file'),
        '.h': ('C/C++ Header', 'Header file'),
        '.cs': ('C# Source', 'C# implementation file'),
        '.csx': ('C# Script', 'C# script file'),
        '.rb': ('Ruby Source', 'Ruby implementation file'),
        '.go': ('Go Source', 'Go implementation file'),
        '.zig': ('Zig Source', 'Zig implementation file'),
        '.rush': ('Rush Source', 'Rush implementation file'),
        '.perl': ('Perl Source', 'Perl script file'),
        '.matlab': ('MATLAB Source', 'MATLAB script file'),
        '.groovy': ('Groovy Source', 'Groovy implementation file'),
        '.lua': ('Lua Source', 'Lua script file')
    }
    
    return type_map.get(ext, ('Generic', 'Project file'))

def scan_for_projects(root_path, max_depth=3, ignored_dirs=None, use_cache=True):
    """Scan directory recursively for projects with caching."""
    cache_key = f"{root_path}:{max_depth}"
    
    # Check cache
    if use_cache and cache_key in _scan_cache:
        cache_time, cached_results = _scan_cache[cache_key]
        # Cache is valid for 5 minutes
        if time.time() - cache_time < CACHE_EXPIRATION:
            return cached_results
    
    # Perform scan as usual
    results = _do_scan(root_path, max_depth, ignored_dirs)
    
    # Save to cache
    if use_cache:
        _scan_cache[cache_key] = (time.time(), results)
    
    return results

def get_project_description(project_path):
    """Get project description and key features using standardized approach."""
    try:
        project_info = detect_project_type(project_path)
        project_type = project_info['type']
        
        result = {
            "name": os.path.basename(project_path),
            "description": "Project directory structure and information",
            "key_features": [
                f"Type: {PROJECT_TYPES.get(project_type, {'description': 'Generic Project'})['description']}",
                f"Language: {project_info['language']}",
                f"Framework: {project_info['framework']}",
                "File and directory tracking",
                "Automatic updates"
            ]
        }
        
        return result
        
    except Exception as e:
        print(f"Error getting project description: {e}")
        return {
            "name": os.path.basename(project_path),
            "description": "Error reading project information",
            "key_features": ["File and directory tracking"]
        }

def _do_scan(root_path, max_depth=3, ignored_dirs=None):
    """Perform a scan of the directory to find projects."""
    if ignored_dirs is None:
        ignored_dirs = _config.get('ignored_directories', [])
    
    projects = []
    root_path = os.path.abspath(root_path or '.')
    
    # Check the root directory first
    project_type = detect_project_type(root_path)
    if project_type != 'generic':
        # Analyze project information
        project_info = get_project_description(root_path)
        language, framework = detect_language_and_framework(root_path)
        projects.append({
            'path': root_path,
            'type': project_type,
            'name': project_info.get('name', os.path.basename(root_path)),
            'description': project_info.get('description', 'No description available'),
            'language': language,
            'framework': framework
        })
    
    def _scan_directory(current_path, current_depth):
        if current_depth > max_depth:
            return
            
        try:
            # Scan subdirectories
            for item in os.listdir(current_path):
                # Skip ignored directories immediately
                if item in IGNORED_DIRECTORIES:
                    continue
                    
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    # Check each subdirectory
                    project_type = detect_project_type(item_path)
                    if project_type != 'generic':
                        # Analyze project information
                        project_info = get_project_description(item_path)
                        language, framework = detect_language_and_framework(item_path)
                        projects.append({
                            'path': item_path,
                            'type': project_type,
                            'name': project_info.get('name', item),
                            'description': project_info.get('description', 'No description available'),
                            'language': language,
                            'framework': framework
                        })
                    else:
                        # If not a project, scan further
                        _scan_directory(item_path, current_depth + 1)
                    
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
            
    # Start scanning from the root directory
    _scan_directory(root_path, 0)
    return projects 