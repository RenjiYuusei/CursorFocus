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
    'java': {
        'description': 'Java Project',
        'indicators': ['pom.xml', 'build.gradle', 'gradlew', '.gradle/', 'src/main/java/', 'target/', 'META-INF/'],
        'file_patterns': ['*.java', '*.jar', '*.war'],
        'required_files': [],
        'priority': 7,
        'additional_checks': [
            lambda path: any(f.endswith('.java') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'go': {
        'description': 'Go Project',
        'indicators': ['go.mod', 'go.sum', 'main.go', 'pkg/', 'cmd/', 'internal/'],
        'file_patterns': ['*.go'],
        'required_files': [],
        'priority': 7,
        'additional_checks': [
            lambda path: any(f.endswith('.go') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'ruby': {
        'description': 'Ruby Project',
        'indicators': ['Gemfile', 'Rakefile', '.ruby-version', 'config.ru', 'bin/rails', 'app/', 'lib/'],
        'file_patterns': ['*.rb', '*.erb', '*.rake'],
        'required_files': [],
        'priority': 6,
        'additional_checks': [
            lambda path: any(f.endswith('.rb') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'rust': {
        'description': 'Rust Project',
        'indicators': ['Cargo.toml', 'Cargo.lock', 'src/main.rs', 'src/lib.rs', 'target/'],
        'file_patterns': ['*.rs'],
        'required_files': [],
        'priority': 7,
        'additional_checks': [
            lambda path: any(f.endswith('.rs') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'dart': {
        'description': 'Dart/Flutter Project',
        'indicators': ['pubspec.yaml', 'pubspec.lock', '.dart_tool/', 'android/', 'ios/', 'lib/', 'test/'],
        'file_patterns': ['*.dart'],
        'required_files': [],
        'priority': 6,
        'additional_checks': [
            lambda path: any(f.endswith('.dart') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'scala': {
        'description': 'Scala Project',
        'indicators': ['build.sbt', 'project/build.properties', '.scala-build/', 'src/main/scala/'],
        'file_patterns': ['*.scala'],
        'required_files': [],
        'priority': 6,
        'additional_checks': [
            lambda path: any(f.endswith('.scala') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'javascript': {
        'description': 'JavaScript/Node.js Project', 
        'indicators': ['package.json', 'package-lock.json', 'yarn.lock', 'node_modules/', 'webpack.config.js', '.npmrc', '.nvmrc', 'next.config.js'],
        'file_patterns': ['*.js', '*.jsx', '*.mjs', '*.cjs'],
        'required_files': [],
        'priority': 5,
        'additonal_checks': [
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
    'swift': {
        'description': 'Swift Project',
        'indicators': ['Package.swift', '*.xcodeproj', '*.xcworkspace', 'Podfile', 'Cartfile'],
        'file_patterns': ['*.swift'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.swift') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'react': {
        'description': 'React Project',
        'indicators': ['react', 'react-dom', 'jsx', 'tsx', 'src/App.js', 'src/App.jsx', 'src/App.tsx'],
        'file_patterns': ['*.jsx', '*.tsx'],
        'required_files': [],
        'priority': 7,  # Higher than generic javascript
        'additional_checks': [
            lambda path: os.path.exists(os.path.join(path, 'package.json')) and any(
                'react' in line for line in open(os.path.join(path, 'package.json'), 'r').readlines()
            ) if os.path.exists(os.path.join(path, 'package.json')) else False
        ]
    },
    'vue': {
        'description': 'Vue.js Project',
        'indicators': ['vue.config.js', '.vue', 'src/main.js', 'src/App.vue'],
        'file_patterns': ['*.vue'],
        'required_files': [],
        'priority': 7,
        'additional_checks': [
            lambda path: os.path.exists(os.path.join(path, 'package.json')) and any(
                'vue' in line for line in open(os.path.join(path, 'package.json'), 'r').readlines()
            ) if os.path.exists(os.path.join(path, 'package.json')) else False
        ]
    },
    'angular': {
        'description': 'Angular Project',
        'indicators': ['angular.json', '.angular-cli.json', 'src/app/app.module.ts'],
        'file_patterns': ['*.ts', '*.html', '*.scss'],
        'required_files': [],
        'priority': 7,
        'additional_checks': [
            lambda path: os.path.exists(os.path.join(path, 'package.json')) and any(
                '@angular/core' in line for line in open(os.path.join(path, 'package.json'), 'r').readlines()
            ) if os.path.exists(os.path.join(path, 'package.json')) else False
        ]
    },
    'django': {
        'description': 'Django Project',
        'indicators': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py', 'asgi.py'],
        'file_patterns': ['*.py'],
        'required_files': [],
        'priority': 9,
        'additional_checks': [
            lambda path: os.path.exists(os.path.join(path, 'manage.py')) and 'django' in open(os.path.join(path, 'manage.py'), 'r').read() if os.path.exists(os.path.join(path, 'manage.py')) else False
        ]
    },
    'flask': {
        'description': 'Flask Project',
        'indicators': ['app.py', 'wsgi.py', 'requirements.txt'],
        'file_patterns': ['*.py'],
        'required_files': [],
        'priority': 8,
        'additional_checks': [
            lambda path: any(
                os.path.exists(os.path.join(path, f)) and 'flask' in open(os.path.join(path, f), 'r').read().lower()
                for f in os.listdir(path) if f.endswith('.py') and os.path.isfile(os.path.join(path, f))
            )
        ]
    },
    'laravel': {
        'description': 'Laravel Project',
        'indicators': ['artisan', 'app/Http/Controllers', 'app/Models', 'resources/views'],
        'file_patterns': ['*.php'],
        'required_files': [],
        'priority': 8,
        'additional_checks': [
            lambda path: os.path.exists(os.path.join(path, 'artisan')) and os.path.exists(os.path.join(path, 'app'))
        ]
    },
    'dotnet': {
        'description': '.NET Project',
        'indicators': ['*.csproj', '*.vbproj', '*.fsproj', 'Program.cs', 'Startup.cs', 'appsettings.json'],
        'file_patterns': ['*.cs', '*.vb', '*.fs'],
        'required_files': [],
        'priority': 7,
        'additional_checks': [
            lambda path: any(f.endswith(('.csproj', '.vbproj', '.fsproj')) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'unity': {
        'description': 'Unity Project',
        'indicators': ['Assets/', 'ProjectSettings/', 'Packages/manifest.json', 'Library/'],
        'file_patterns': ['*.cs', '*.unity', '*.prefab', '*.asset'],
        'required_files': [],
        'priority': 7,
        'additional_checks': [
            lambda path: os.path.exists(os.path.join(path, 'Assets')) and os.path.exists(os.path.join(path, 'ProjectSettings'))
        ]
    },
    'android': {
        'description': 'Android Project',
        'indicators': ['AndroidManifest.xml', 'build.gradle', 'gradle.properties', 'app/src/main/java', 'res/layout'],
        'file_patterns': ['*.java', '*.kt', '*.xml'],
        'required_files': [],
        'priority': 6,
        'additional_checks': [
            lambda path: os.path.exists(os.path.join(path, 'app')) and (
                os.path.exists(os.path.join(path, 'app/src/main/AndroidManifest.xml')) or
                os.path.exists(os.path.join(path, 'AndroidManifest.xml'))
            )
        ]
    },
    'ios': {
        'description': 'iOS Project',
        'indicators': ['*.xcodeproj', '*.xcworkspace', 'Info.plist', 'AppDelegate.swift', 'AppDelegate.m'],
        'file_patterns': ['*.swift', '*.m', '*.h'],
        'required_files': [],
        'priority': 6,
        'additional_checks': [
            lambda path: any(f.endswith(('.xcodeproj', '.xcworkspace')) for f in os.listdir(path) if os.path.isdir(os.path.join(path, f)))
        ]
    },
    'docker': {
        'description': 'Docker Project',
        'indicators': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', '.dockerignore'],
        'file_patterns': ['Dockerfile*', '*.yml', '*.yaml'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f == 'Dockerfile' or f.startswith('Dockerfile.') or f in ['docker-compose.yml', 'docker-compose.yaml'] for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'terraform': {
        'description': 'Terraform Project',
        'indicators': ['*.tf', '*.tfvars', 'terraform.tfstate', '.terraform/'],
        'file_patterns': ['*.tf', '*.tfvars'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.tf') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        ]
    },
    'dataScience': {
        'description': 'Data Science Project',
        'indicators': ['*.ipynb', 'data/', 'notebooks/', 'models/', 'requirements.txt'],
        'file_patterns': ['*.py', '*.ipynb', '*.r', '*.Rmd'],
        'required_files': [],
        'priority': 5,
        'additional_checks': [
            lambda path: any(f.endswith('.ipynb') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))) or
                        (os.path.exists(os.path.join(path, 'requirements.txt')) and any(
                            pkg in open(os.path.join(path, 'requirements.txt'), 'r').read() 
                            for pkg in ['pandas', 'numpy', 'matplotlib', 'scikit-learn', 'tensorflow', 'pytorch', 'keras']
                        ) if os.path.exists(os.path.join(path, 'requirements.txt')) else False)
        ]
    }
}

# Add cache for scan results with expiration
_scan_cache = {}
CACHE_EXPIRATION = 300  # 5 minutes

# Directories to be ignored during project scanning
IGNORED_DIRECTORIES = {
    # Version control
    '.git',
    '.github',
    '.svn',
    '.hg',
    
    # Python specific
    '__pycache__',
    'venv',
    '.venv',
    'env',
    '.env',
    '.pytest_cache',
    '.mypy_cache',
    
    # Build and distribution
    'dist',
    'build',
    '.egg-info',
    '.eggs',
    
    # JavaScript/Node specific
    'node_modules',
    'bower_components',
    '.next',
    '.nuxt',
    
    # IDE and editor specific
    '.idea',
    '.vscode',
    '.vs',
    
    # OS specific
    '.DS_Store',
    
    # Docker
    '.docker',
    
    # Other common temp/cache dirs
    'tmp',
    '.tmp',
    'cache',
    '.cache'
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
        'python': ['.py', 'requirements.txt', 'setup.py', 'Pipfile', 'pyproject.toml'],
        'javascript': ['.js', '.jsx', '.mjs', '.cjs', 'package.json', 'webpack.config.js', 'next.config.js'],
        'typescript': ['.ts', '.tsx', 'tsconfig.json', 'tslint.json', '.eslintrc'],
        'kotlin': ['.kt', '.kts', 'build.gradle.kts'],
        'php': ['.php', 'composer.json', 'artisan', 'index.php'],
        'swift': ['.swift', 'Package.swift', '.xcodeproj', '.xcworkspace', 'Podfile'],
        'cpp': ['.cpp', '.hpp', '.cc', '.cxx', '.h', '.hxx', 'CMakeLists.txt', 'compile_commands.json'],
        'c': ['.c', '.h', 'makefile', 'Makefile'],
        'csharp': ['.cs', '.csproj', '.sln', 'Program.cs', 'Startup.cs'],
        'java': ['.java', 'pom.xml', 'build.gradle', 'gradlew', '.gradle', 'src/main/java'],
        'go': ['.go', 'go.mod', 'go.sum', 'main.go'],
        'ruby': ['.rb', '.erb', '.rake', 'Gemfile', 'Rakefile', 'config.ru'],
        'rust': ['.rs', 'Cargo.toml', 'Cargo.lock'],
        'dart': ['.dart', 'pubspec.yaml', 'pubspec.lock'],
        'scala': ['.scala', 'build.sbt', '.scala-build'],
        'css': ['.css', '.scss', '.sass', '.less', 'styles.css'],
        'html': ['.html', '.htm', 'index.html'],
        'bash': ['.sh', '.bash'],
        'powershell': ['.ps1', '.psm1', '.psd1'],
        'objc': ['.m', '.mm', '.h'],
        'perl': ['.pl', '.pm'],
        'haskell': ['.hs', '.lhs', '.cabal', 'stack.yaml'],
        'r': ['.r', '.R', '.Rmd', '.Rproj'],
        'lua': ['.lua'],
        'elixir': ['.ex', '.exs', 'mix.exs'],
        'erlang': ['.erl', '.hrl', 'rebar.config'],
        'clojure': ['.clj', '.cljs', '.cljc', 'project.clj'],
        'groovy': ['.groovy', '.gradle'],
        'shell': ['.sh', '.bash', '.zsh'],
        'zig': ['.zig', 'build.zig'],
        'apex': ['.cls', '.apex'],
        'fortran': ['.f', '.f90', '.f95', '.f03', '.f08'],
        'solidity': ['.sol'],
        'julia': ['.jl', 'Project.toml'],
        'terraform': ['.tf', '.tfvars', 'terraform.tfstate'],
        'sql': ['.sql', '.mysql', '.pgsql', '.sqlite'],
    }
    
    # Framework detection based on specific files/directories
    framework_indicators = {
        # Python frameworks
        'django': ['manage.py', 'django', 'wsgi.py', 'asgi.py', 'settings.py', 'urls.py'],
        'flask': ['flask', 'Flask==', 'app.py', '@app.route'],
        'fastapi': ['fastapi', 'FastAPI', '@app.get', '@app.post'],
        'pytorch': ['torch', 'pytorch', 'nn.Module'],
        'tensorflow': ['tensorflow', 'tf.', 'keras'],
        'pandas': ['pandas', 'pd.', 'DataFrame'],
        'scrapy': ['scrapy', 'Spider', 'CrawlSpider'],
        
        # JavaScript/TypeScript frameworks
        'react': ['react', 'React.', 'ReactDOM', '<React.', 'useState', 'useEffect'],
        'vue': ['vue', 'Vue.', 'createApp', '<template>', '<script setup>'],
        'angular': ['@angular/core', 'NgModule', 'Component', '@Component'],
        'svelte': ['svelte', '<script>', '<style>', '<svelte:'],
        'next': ['next', 'Next.js', 'getServerSideProps', 'getStaticProps'],
        'nuxt': ['nuxt', 'Nuxt.js', 'defineNuxtConfig'],
        'express': ['express', 'app.listen', 'app.use('],
        'nest': ['@nestjs/core', 'NestFactory', '@Module'],
        'electron': ['electron', 'app.whenReady', 'BrowserWindow'],
        
        # .NET frameworks
        'aspnet': ['Microsoft.AspNetCore', 'IWebHost', 'Startup', 'IServiceCollection'],
        'blazor': ['Blazor', '@page', '@code', '@inject', 'Microsoft.AspNetCore.Components'],
        'wpf': ['System.Windows', 'Window', 'UserControl', 'XAML'],
        'xamarin': ['Xamarin', 'ContentPage', 'MainActivity'],
        'unity': ['UnityEngine', 'MonoBehaviour', 'GameObject', 'Transform'],
        'maui': ['Microsoft.Maui', '.UseMauiApp'],
        
        # Java/Kotlin frameworks
        'spring': ['org.springframework', 'SpringApplication', '@SpringBootApplication', '@Autowired'],
        'android': ['androidx', 'android.', 'Activity', 'Fragment', 'setContentView'],
        'ktor': ['io.ktor', 'Ktor', 'embeddedServer'],
        'vaadin': ['com.vaadin', 'Vaadin', '@Route'],
        'helidon': ['io.helidon', 'Helidon'],
        'micronaut': ['io.micronaut', 'Micronaut'],
        'quarkus': ['io.quarkus', 'Quarkus'],
        'javafx': ['javafx', 'Application', 'Stage', 'Scene'],
        'jetpackcompose': ['androidx.compose', 'Composable', '@Composable'],
        
        # PHP frameworks
        'laravel': ['laravel', 'Illuminate\\', 'artisan', 'php artisan'],
        'symfony': ['symfony', 'Symfony\\', 'bin/console'],
        'cakephp': ['cakephp', 'CakePHP'],
        'codeigniter': ['codeigniter', 'CI_Controller'],
        'yii': ['yii', 'Yii::'],
        'wordpress': ['wp-', 'wp_', 'get_template_part', 'wp-config.php'],
        
        # Go frameworks
        'gin': ['gin-gonic/gin', 'gin.', 'gin.Engine', 'gin.Context'],
        'echo': ['labstack/echo', 'echo.', 'echo.New('],
        'fiber': ['fiber', 'gofiber', 'app := fiber.New('],
        'buffalo': ['gobuffalo', 'buffalo.New('],
        'gorm': ['gorm.io', 'gorm.', 'db.Model('],
        
        # Swift frameworks
        'swiftui': ['SwiftUI', 'View', '@State', '@Binding'],
        'uikit': ['UIKit', 'UIViewController', 'UIView'],
        'combine': ['Combine', 'Publisher', 'Subscriber'],
        'vapor': ['vapor', 'Vapor', '.configure('],
        
        # Ruby frameworks
        'rails': ['rails', 'Rails', 'ActiveRecord', 'ApplicationController'],
        'sinatra': ['sinatra', 'Sinatra::'],
        'hanami': ['hanami', 'Hanami::', 'bundle exec hanami'],
        
        # C++ frameworks
        'qt': ['Qt.', 'QtCore', 'QObject', 'QApplication'],
        'boost': ['boost::', 'BOOST_'],
        'opencv': ['cv::', 'opencv2/', '#include <opencv'],
        'poco': ['Poco::', '#include "Poco'],
        
        # Rust frameworks
        'rocket': ['rocket', 'rocket::', '#[get('],
        'actix': ['actix-web', 'actix_web::'],
        'axum': ['axum', 'axum::'],
        'yew': ['yew', 'yew::'],
        
        # Mobile
        'flutter': ['flutter', 'Flutter', 'StatelessWidget', 'StatefulWidget'],
        'ionic': ['ionic', 'Ionic', 'IonPage'],
        'reactnative': ['react-native', 'ReactNative', 'StyleSheet.create'],
        
        # Cloud/DevOps
        'docker': ['Dockerfile', 'docker-compose', 'FROM ', 'ENTRYPOINT'],
        'kubernetes': ['apiVersion:', 'kind:', 'metadata:', 'spec:'],
        'awscdk': ['aws-cdk', 'cdk.'],
        'terraform': ['terraform', 'provider "aws"', 'resource "aws_'],
        'pulumi': ['pulumi', '@pulumi/aws'],
        
        # Data Science
        'jupyter': ['.ipynb', 'jupyter'],
        'scikit': ['sklearn', 'scikit-learn'],
        'matplotlib': ['matplotlib', 'pyplot', 'plt.'],
        'numpy': ['numpy', 'np.array', 'ndarray'],
        
        # Database
        'sqlalchemy': ['sqlalchemy', 'SQLAlchemy', 'Base = declarative_base()'],
        'hibernate': ['hibernate', 'Hibernate', '@Entity'],
        'mongoose': ['mongoose', 'Schema', 'model('],
        'sequelize': ['sequelize', 'Sequelize', 'define('],
        'typeorm': ['typeorm', 'TypeORM', '@Entity('],
        'prisma': ['prisma', 'Prisma', 'schema.prisma'],
    }
    
    # Detect language
    detected_language = 'unknown'
    max_matches = 0
    
    for lang, indicators in language_indicators.items():
        matches = 0
        for f in files:
            if any(f.endswith(ind) if ind.startswith('.') else ind in f for ind in indicators):
                matches += 1
                
            # Check for directories that might indicate a language
            if os.path.isdir(os.path.join(project_path, f)):
                if f in ['src', 'lib', 'app', 'test', 'tests']:
                    try:
                        subfiles = os.listdir(os.path.join(project_path, f))
                        for subfile in subfiles:
                            if any(subfile.endswith(ind) if ind.startswith('.') else ind in subfile for ind in indicators):
                                matches += 0.5  # Half point for matches in subdirectories
                    except:
                        pass
                        
        if matches > max_matches:
            max_matches = matches
            detected_language = lang
            
    # Detect framework by checking file contents
    detected_framework = 'none'
    framework_matches = {}
    
    # Check potential framework indicator files
    config_files = ['requirements.txt', 'package.json', 'composer.json', 'build.gradle', 
                    'pom.xml', 'Cargo.toml', 'go.mod', 'pubspec.yaml', 'Gemfile',
                    'CMakeLists.txt', 'Podfile', 'build.sbt', '.csproj', 'project.clj',
                    'mix.exs', 'app.py', 'build.zig', 'pyproject.toml', 'Pipfile']
    
    source_files = []
    for f in files:
        if os.path.isfile(os.path.join(project_path, f)) and (
            f.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.kt', '.php', '.rb', '.go', 
                       '.rs', '.cs', '.swift', '.cpp', '.h', '.dart', '.vue', '.scala'))
        ):
            source_files.append(f)
    
    # Limit to 10 source files for performance
    import random
    if len(source_files) > 10:
        source_files = random.sample(source_files, 10)
    
    # Check config files first
    for f in [f for f in files if f in config_files]:
        try:
            with open(os.path.join(project_path, f), 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read().lower()
                for framework, indicators in framework_indicators.items():
                    matches = sum(1 for ind in indicators if ind.lower() in content)
                    if matches > 0:
                        framework_matches[framework] = framework_matches.get(framework, 0) + matches * 2  # Config files have higher weight
        except:
            pass
    
    # Check source files next
    for f in source_files:
        try:
            with open(os.path.join(project_path, f), 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read().lower()
                for framework, indicators in framework_indicators.items():
                    matches = sum(1 for ind in indicators if ind.lower() in content)
                    if matches > 0:
                        framework_matches[framework] = framework_matches.get(framework, 0) + matches
        except:
            pass
    
    # Check for special directory structures
    special_dirs = {
        'django': ['templates', 'migrations', 'apps.py'],
        'react': ['components', 'containers', 'redux', 'hooks'],
        'unity': ['Assets', 'ProjectSettings'],
        'angular': ['src/app/components', 'src/app/services'],
        'vue': ['src/components', 'src/views'],
        'android': ['app/src/main', 'res/layout'],
        'spring': ['src/main/java', 'src/main/resources'],
        'laravel': ['app/Http/Controllers', 'resources/views'],
        'rails': ['app/controllers', 'app/models', 'app/views'],
    }
    
    for framework, dirs in special_dirs.items():
        matches = sum(1 for d in dirs if os.path.exists(os.path.join(project_path, d)))
        if matches > 0:
            framework_matches[framework] = framework_matches.get(framework, 0) + matches * 1.5
    
    # Select the framework with the most matches
    if framework_matches:
        detected_framework = max(framework_matches.items(), key=lambda x: x[1])[0]
                    
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
        '.csx': ('C# Script', 'C# script file')
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