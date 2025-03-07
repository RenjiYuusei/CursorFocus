import os
import json
import logging
from typing import Dict, Any, Optional

class RulesAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.logger = logging.getLogger(__name__)

    def analyze_project_for_rules(self) -> Dict[str, Any]:
        """Analyze the project and return project information for rules generation."""
        project_info = {
            'name': self._detect_project_name(),
            'version': '1.0.0',
            'language': self._detect_main_language(),
            'framework': self._detect_framework(),
            'type': self._detect_project_type()
        }
        return project_info

    def _detect_project_name(self) -> str:
        """Detect the project name from package files or directory name.
        
        Checks common project definition files in priority order and falls back
        to the directory name if no project files are found or readable.
        
        Returns:
            str: The detected project name
        """
        # Define project file checkers in order of priority
        project_files = [
            self._get_name_from_package_json,
            self._get_name_from_setup_py,
            self._get_name_from_pom_xml,
            self._get_name_from_gradle,
            self._get_name_from_cargo_toml,
            self._get_name_from_gemspec,
            self._get_name_from_csproj,
        ]
        
        # Try each project file type
        for get_name_func in project_files:
            name = get_name_func()
            if name:
                return name
                
        # Fallback to directory name
        dir_name = os.path.basename(os.path.abspath(self.project_path))
        self.logger.info(f"No project files found with name information, using directory name: {dir_name}")
        return dir_name
    
    def _get_name_from_package_json(self) -> Optional[str]:
        """Extract project name from package.json file."""
        package_json_path = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('name'):
                        self.logger.debug(f"Found project name in package.json: {data['name']}")
                        return data['name']
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing package.json: {str(e)}")
            except IOError as e:
                self.logger.error(f"Error reading package.json: {str(e)}")
        return None
    
    def _get_name_from_setup_py(self) -> Optional[str]:
        """Extract project name from setup.py file."""
        setup_py_path = os.path.join(self.project_path, 'setup.py')
        if os.path.exists(setup_py_path):
            try:
                with open(setup_py_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for name parameter in setup() function
                    import re
                    name_match = re.search(r"name=['\"]([^'\"]+)['\"]", content)
                    if name_match:
                        name = name_match.group(1)
                        self.logger.debug(f"Found project name in setup.py: {name}")
                        return name
            except IOError as e:
                self.logger.error(f"Error reading setup.py: {str(e)}")
        return None
    
    def _get_name_from_pom_xml(self) -> Optional[str]:
        """Extract project name from Maven pom.xml file."""
        pom_path = os.path.join(self.project_path, 'pom.xml')
        if os.path.exists(pom_path):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(pom_path)
                root = tree.getroot()
                
                # Handle potential namespace in XML
                ns = {'': root.tag.split('}')[0].strip('{') if '}' in root.tag else ''}
                
                # Try artifactId first, then name if available
                artifact_id = root.find('./artifactId', ns)
                name_elem = root.find('./name', ns)
                
                if name_elem is not None and name_elem.text:
                    self.logger.debug(f"Found project name in pom.xml <name>: {name_elem.text}")
                    return name_elem.text
                elif artifact_id is not None and artifact_id.text:
                    self.logger.debug(f"Found project name in pom.xml <artifactId>: {artifact_id.text}")
                    return artifact_id.text
            except Exception as e:
                self.logger.error(f"Error parsing pom.xml: {str(e)}")
        return None
    
    def _get_name_from_gradle(self) -> Optional[str]:
        """Extract project name from build.gradle file."""
        gradle_path = os.path.join(self.project_path, 'build.gradle')
        if os.path.exists(gradle_path):
            try:
                with open(gradle_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for project name in various gradle configurations
                    import re
                    # Try rootProject.name or project.name
                    name_match = re.search(r"(?:rootProject|project)\.name\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if name_match:
                        name = name_match.group(1)
                        self.logger.debug(f"Found project name in build.gradle: {name}")
                        return name
                    
                    # Try looking for archivesBaseName
                    archive_match = re.search(r"archivesBaseName\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if archive_match:
                        name = archive_match.group(1)
                        self.logger.debug(f"Found project name in build.gradle (archivesBaseName): {name}")
                        return name
            except IOError as e:
                self.logger.error(f"Error reading build.gradle: {str(e)}")
        return None
    
    def _get_name_from_cargo_toml(self) -> Optional[str]:
        """Extract project name from Cargo.toml file (Rust)."""
        cargo_path = os.path.join(self.project_path, 'Cargo.toml')
        if os.path.exists(cargo_path):
            try:
                # Try to use toml parser if available
                try:
                    import toml
                    with open(cargo_path, 'r', encoding='utf-8') as f:
                        data = toml.load(f)
                        if data.get('package', {}).get('name'):
                            name = data['package']['name']
                            self.logger.debug(f"Found project name in Cargo.toml: {name}")
                            return name
                except ImportError:
                    # Fallback to regex if toml module is not available
                    with open(cargo_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        import re
                        name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", content)
                        if name_match:
                            name = name_match.group(1)
                            self.logger.debug(f"Found project name in Cargo.toml (regex): {name}")
                            return name
            except Exception as e:
                self.logger.error(f"Error reading Cargo.toml: {str(e)}")
        return None
    
    def _get_name_from_gemspec(self) -> Optional[str]:
        """Extract project name from .gemspec files (Ruby)."""
        # Find any .gemspec file in the project root
        gemspec_files = [f for f in os.listdir(self.project_path) 
                        if f.endswith('.gemspec') and os.path.isfile(os.path.join(self.project_path, f))]
        
        if gemspec_files:
            gemspec_path = os.path.join(self.project_path, gemspec_files[0])
            try:
                with open(gemspec_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    import re
                    # Look for gem name definition
                    name_match = re.search(r"\.name\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if name_match:
                        name = name_match.group(1)
                        self.logger.debug(f"Found project name in {gemspec_files[0]}: {name}")
                        return name
            except IOError as e:
                self.logger.error(f"Error reading {gemspec_files[0]}: {str(e)}")
        return None
    
    def _get_name_from_csproj(self) -> Optional[str]:
        """Extract project name from .csproj files (.NET)."""
        # Find any .csproj file in the project root
        csproj_files = [f for f in os.listdir(self.project_path) 
                       if f.endswith('.csproj') and os.path.isfile(os.path.join(self.project_path, f))]
        
        if csproj_files:
            csproj_path = os.path.join(self.project_path, csproj_files[0])
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(csproj_path)
                root = tree.getroot()
                
                # Look for AssemblyName or first PropertyGroup/RootNamespace
                assembly_name = root.find(".//AssemblyName")
                if assembly_name is not None and assembly_name.text:
                    self.logger.debug(f"Found project name in {csproj_files[0]} <AssemblyName>: {assembly_name.text}")
                    return assembly_name.text
                
                root_namespace = root.find(".//RootNamespace")
                if root_namespace is not None and root_namespace.text:
                    self.logger.debug(f"Found project name in {csproj_files[0]} <RootNamespace>: {root_namespace.text}")
                    return root_namespace.text
                
                # If all else fails, use the file name without extension
                project_name = os.path.splitext(csproj_files[0])[0]
                self.logger.debug(f"Using .csproj filename as project name: {project_name}")
                return project_name
            except Exception as e:
                self.logger.error(f"Error parsing {csproj_files[0]}: {str(e)}")
        return None

    def _detect_main_language(self) -> str:
        """Detect the main programming language used in the project."""
        extensions = {}
        
        for root, _, files in os.walk(self.project_path):
            if 'node_modules' in root or 'venv' in root or '.git' in root:
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

        # Map extensions to languages
        FILE_EXTENSIONS = {
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.py': 'python',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.kts': 'kotlin',
            '.json': 'json',
            '.md': 'markdown',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.vue': 'vue',
            '.svelte': 'svelte'
        }

        # Find the most common language
        max_count = 0
        main_language = 'javascript'  # default
        
        for ext, count in extensions.items():
            if ext in FILE_EXTENSIONS and count > max_count:
                max_count = count
                main_language = FILE_EXTENSIONS[ext]

        return main_language

    def _detect_framework(self) -> str:
        """Detect the framework used in the project."""
        # Check package.json for JS/TS frameworks
        package_json_path = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    if 'react' in deps:
                        return 'react'
                    if 'vue' in deps:
                        return 'vue'
                    if '@angular/core' in deps:
                        return 'angular'
                    if 'next' in deps:
                        return 'next.js'
                    if 'express' in deps:
                        return 'express'
            except:
                pass

        # Check requirements.txt for Python frameworks
        requirements_path = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, 'r') as f:
                    content = f.read().lower()
                    if 'django' in content:
                        return 'django'
                    if 'flask' in content:
                        return 'flask'
                    if 'fastapi' in content:
                        return 'fastapi'
            except:
                pass

        # Check composer.json for PHP frameworks
        composer_path = os.path.join(self.project_path, 'composer.json')
        if os.path.exists(composer_path):
            try:
                with open(composer_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('require', {}), **data.get('require-dev', {})}
                    
                    if 'laravel/framework' in deps:
                        return 'laravel'
                    if 'symfony/symfony' in deps:
                        return 'symfony'
                    if 'cakephp/cakephp' in deps:
                        return 'cakephp'
                    if 'codeigniter/framework' in deps:
                        return 'codeigniter'
                    if 'yiisoft/yii2' in deps:
                        return 'yii2'
            except:
                pass

        # Check for WordPress
        if os.path.exists(os.path.join(self.project_path, 'wp-config.php')):
            return 'wordpress'

        # Check for C++ frameworks
        cmake_path = os.path.join(self.project_path, 'CMakeLists.txt')
        if os.path.exists(cmake_path):
            try:
                with open(cmake_path, 'r') as f:
                    content = f.read().lower()
                    if 'qt' in content:
                        return 'qt'
                    if 'boost' in content:
                        return 'boost'
                    if 'opencv' in content:
                        return 'opencv'
            except:
                pass

        # Check for C# frameworks
        csproj_files = [f for f in os.listdir(self.project_path) if f.endswith('.csproj')]
        for csproj in csproj_files:
            try:
                with open(os.path.join(self.project_path, csproj), 'r') as f:
                    content = f.read().lower()
                    if 'microsoft.aspnetcore' in content:
                        return 'asp.net core'
                    if 'microsoft.net.sdk.web' in content:
                        return 'asp.net core'
                    if 'xamarin' in content:
                        return 'xamarin'
                    if 'microsoft.maui' in content:
                        return 'maui'
            except:
                pass

        # Check for Swift frameworks
        podfile_path = os.path.join(self.project_path, 'Podfile')
        if os.path.exists(podfile_path):
            try:
                with open(podfile_path, 'r') as f:
                    content = f.read().lower()
                    if 'swiftui' in content:
                        return 'swiftui'
                    if 'combine' in content:
                        return 'combine'
                    if 'vapor' in content:
                        return 'vapor'
            except:
                pass

        # Check for Kotlin frameworks
        build_gradle_path = os.path.join(self.project_path, 'build.gradle')
        if os.path.exists(build_gradle_path):
            try:
                with open(build_gradle_path, 'r') as f:
                    content = f.read().lower()
                    if 'org.jetbrains.compose' in content:
                        return 'jetpack compose'
                    if 'org.springframework.boot' in content:
                        return 'spring boot'
                    if 'ktor' in content:
                        return 'ktor'
            except:
                pass

        return 'none'

    def _detect_project_type(self) -> str:
        """Detect the type of project (web, mobile, library, etc.)."""
        package_json_path = os.path.join(self.project_path, 'package.json')
        
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    # Check for mobile frameworks
                    if 'react-native' in deps or '@ionic/core' in deps:
                        return 'mobile application'
                    
                    # Check for desktop frameworks
                    if 'electron' in deps:
                        return 'desktop application'
                    
                    # Check if it's a library
                    if data.get('name', '').startswith('@') or '-lib' in data.get('name', ''):
                        return 'library'
            except:
                pass

        # Look for common web project indicators
        web_indicators = ['index.html', 'public/index.html', 'src/index.html']
        for indicator in web_indicators:
            if os.path.exists(os.path.join(self.project_path, indicator)):
                return 'web application'

        return 'application' 