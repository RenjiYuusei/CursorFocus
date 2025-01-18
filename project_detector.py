import os
import json
import re
from config import load_config
import time

# Load project types from config at module level
_config = load_config()
PROJECT_TYPES = {
    'python': {
        'description': 'Python Project',
        'indicators': ['setup.py', 'requirements.txt', 'Pipfile', 'pyproject.toml'],
        'required_files': []
    },
    'node_js': {
        'description': 'Node.js Project', 
        'indicators': ['package.json', 'package-lock.json', 'yarn.lock'],
        'required_files': []
    },
    'php': {
        'description': 'PHP Project',
        'indicators': ['composer.json', 'composer.lock', 'artisan'],
        'required_files': []
    },
    'java': {
        'description': 'Java Project',
        'indicators': ['pom.xml', 'build.gradle', 'gradlew'],
        'required_files': []
    },
    'dotnet': {
        'description': '.NET Project',
        'indicators': ['.sln', '.csproj', '.vbproj', '.fsproj'],
        'required_files': []
    },
    'go': {
        'description': 'Go Project',
        'indicators': ['go.mod', 'go.sum'],
        'required_files': []
    },
    'rust': {
        'description': 'Rust Project',
        'indicators': ['Cargo.toml', 'Cargo.lock'],
        'required_files': []
    },
    'flutter': {
        'description': 'Flutter Project',
        'indicators': ['pubspec.yaml', 'pubspec.lock'],
        'required_files': []
    },
    'android': {
        'description': 'Android Project',
        'indicators': ['build.gradle', 'settings.gradle', 'gradlew'],
        'required_files': []
    },
    'ios': {
        'description': 'iOS Project',
        'indicators': ['*.xcodeproj', '*.xcworkspace', 'Podfile'],
        'required_files': []
    },
    'web': {
        'description': 'Web Project',
        'indicators': ['index.html', 'webpack.config.js', 'vite.config.js'],
        'required_files': []
    },
    'docker': {
        'description': 'Docker Project',
        'indicators': ['Dockerfile', 'docker-compose.yml'],
        'required_files': []
    },
    'git': {
        'description': 'Git Repository',
        'indicators': ['.git'],
        'required_files': []
    }
}

# Add cache for scan results
_scan_cache = {}

def detect_project_type(project_path):
    if not os.path.exists(project_path):
        return {
            'type': 'generic',
            'language': 'unknown',
            'framework': 'none'
        }
        
    try:
        files = os.listdir(project_path)
    except (PermissionError, OSError):
        return {
            'type': 'generic',
            'language': 'unknown',
            'framework': 'none'
        }
        
    project_type = 'generic'
    # Check each project type
    for type_name, rules in PROJECT_TYPES.items():
        # Check for indicator files
        for indicator in rules.get('indicators', []):
            # Handle wildcard patterns
            if '*' in indicator:
                pattern = indicator.replace('.', '[.]').replace('*', '.*')
                if any(re.match(pattern, f) for f in files):
                    project_type = type_name
                    break
            # Direct file match
            elif indicator in files:
                project_type = type_name
                break
                
        # Check for required files if specified
        if rules.get('required_files'):
            if all(f in files for f in rules['required_files']):
                project_type = type_name
                break
                
    # Detect language and framework
    language, framework = detect_language_and_framework(project_path)
    
    # Fallback checks for common development files
    if project_type == 'generic':
        common_dev_files = [
            'README.md',
            '.gitignore',
            'LICENSE',
            'CHANGELOG.md',
            'docs/',
            'src/',
            'test/',
            'tests/'
        ]
        
        if any(f in files for f in common_dev_files):
            project_type = 'generic_dev'
    
    return {
        'type': project_type,
        'language': language,
        'framework': framework,
        'description': PROJECT_TYPES.get(project_type, {'description': 'Generic Project'})['description']
    }

def detect_language_and_framework(project_path):
    """Detect primary language and framework of a project."""
    try:
        files = os.listdir(project_path)
    except:
        return 'unknown', 'none'
        
    # Language detection based on file extensions and key files
    language_indicators = {
        'python': ['.py', 'requirements.txt', 'setup.py', 'Pipfile'],
        'typescript': ['.ts', '.tsx', 'tsconfig.json'],
        'javascript': ['.js', '.jsx', 'package.json'],
        'java': ['.java', 'pom.xml', 'build.gradle'],
        'php': ['.php', 'composer.json'],
        'ruby': ['.rb', 'Gemfile'],
        'go': ['.go', 'go.mod'],
        'rust': ['.rs', 'Cargo.toml'],
        'c++': ['.cpp', '.hpp', '.cc', '.cxx'],
        'c#': ['.cs', '.csproj', '.sln'],
        'lua': ['.lua', 'init.lua', 'main.lua', 'config.lua'],
    }
    
    # Framework detection based on specific files/directories
    framework_indicators = {
        'django': ['manage.py', 'django.contrib'],
        'flask': ['flask', 'Flask=='],
        'fastapi': ['fastapi'],
        'react': ['react', 'React.'],
        'vue': ['vue.config.js', 'Vue.'],
        'angular': ['angular.json', '@angular'],
        'laravel': ['artisan', 'Laravel'],
        'spring': ['spring-boot', 'SpringBoot'],
        'express': ['express'],
        'dotnet': ['Microsoft.NET.Sdk']
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

def scan_for_projects(root_path, max_depth=3, ignored_dirs=None, use_cache=True):
    """Scan directory recursively for projects with caching."""
    cache_key = f"{root_path}:{max_depth}"
    
    # Check cache
    if use_cache and cache_key in _scan_cache:
        cache_time, cached_results = _scan_cache[cache_key]
        # Cache is valid for 5 minutes
        if time.time() - cache_time < 300:
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
        
        if project_type == 'chrome_extension':
            manifest_path = os.path.join(project_path, 'manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)
                    result.update({
                        "name": manifest_data.get('name', 'Chrome Extension'),
                        "description": manifest_data.get('description', 'No description available'),
                        "key_features": [
                            f"Version: {manifest_data.get('version', 'unknown')}",
                            f"Type: {PROJECT_TYPES[project_type]['description']}",
                            *[f"Permission: {perm}" for perm in manifest_data.get('permissions', [])[:3]]
                        ]
                    })
                    
        elif project_type == 'node_js':
            package_path = os.path.join(project_path, 'package.json')
            if os.path.exists(package_path):
                with open(package_path, 'r') as f:
                    package_data = json.load(f)
                    result.update({
                        "name": package_data.get('name', 'Node.js Project'),
                        "description": package_data.get('description', 'No description available'),
                        "key_features": [
                            f"Version: {package_data.get('version', 'unknown')}",
                            f"Type: {PROJECT_TYPES[project_type]['description']}",
                            *[f"Dependency: {dep}" for dep in list(package_data.get('dependencies', {}).keys())[:3]]
                        ]
                    })
        
        return result
        
    except Exception as e:
        print(f"Error getting project description: {e}")
        return {
            "name": os.path.basename(project_path),
            "description": "Error reading project information",
            "key_features": ["File and directory tracking"]
        }

def get_file_type_info(filename):
    """Get file type information."""
    ext = os.path.splitext(filename)[1].lower()
    
    type_map = {
        '.py': ('Python Source', 'Python script containing project logic'),
        '.js': ('JavaScript', 'JavaScript file for client-side functionality'),
        '.jsx': ('React Component', 'React component file'),
        '.ts': ('TypeScript', 'TypeScript source file'),
        '.tsx': ('React TypeScript', 'React component with TypeScript'),
        '.html': ('HTML', 'Web page template'),
        '.css': ('CSS', 'Stylesheet for visual styling'),
        '.md': ('Markdown', 'Documentation file'),
        '.json': ('JSON', 'Configuration or data file'),
        '.php': ('PHP Source', 'PHP script for server-side functionality'),
        '.phtml': ('PHP Template', 'PHP template file'),
        '.ctp': ('CakePHP Template', 'CakePHP view template'),
        '.cpp': ('C++ Source', 'C++ implementation file'),
        '.hpp': ('C++ Header', 'C++ header file'),
        '.cc': ('C++ Source', 'C++ implementation file'),
        '.cxx': ('C++ Source', 'C++ implementation file'),
        '.c': ('C Source', 'C implementation file'),
        '.h': ('C/C++ Header', 'Header file'),
        '.cs': ('C# Source', 'C# implementation file'),
        '.cshtml': ('Razor View', 'ASP.NET Core view template'),
        '.swift': ('Swift Source', 'Swift implementation file'),
        '.kt': ('Kotlin Source', 'Kotlin implementation file'),
        '.kts': ('Kotlin Script', 'Kotlin build script file'),
        '.xcodeproj': ('Xcode Project', 'iOS/macOS project configuration'),
        '.xcworkspace': ('Xcode Workspace', 'iOS/macOS workspace configuration'),
        '.gradle': ('Gradle Build', 'Android/Kotlin build configuration'),
        '.podspec': ('CocoaPods Spec', 'iOS dependency specification'),
        '.storyboard': ('iOS Storyboard', 'iOS UI layout file'),
        '.xib': ('iOS XIB', 'iOS UI component file'),
        '.lua': ('Lua Source', 'Lua script file implementing game logic or automation'),
        '.rockspec': ('LuaRocks Spec', 'Lua package specification file'),
    }
    
    return type_map.get(ext, ('Generic', 'Project file')) 

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
            # Skip ignored directories
            if any(ignored in current_path.split(os.path.sep) for ignored in ignored_dirs):
                return
                
            # Scan subdirectories
            for item in os.listdir(current_path):
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
