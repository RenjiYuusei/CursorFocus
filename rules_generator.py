import os
import json
from typing import Dict, Any, List
from datetime import datetime
import google.generativeai as genai
import re
from rules_analyzer import RulesAnalyzer
from dotenv import load_dotenv

class RulesGenerator:
    # Common regex patterns
    IMPORT_PATTERNS = {
        'python': r'^(?:from|import)\s+([a-zA-Z0-9_\.]+)',
        'javascript': r'(?:import\s+.*?from\s+[\'"]([^\'\"]+)[\'"]|require\s*\([\'"]([^\'\"]+)[\'"]\))',
        'typescript': r'(?:import|require)\s+.*?[\'"]([^\'\"]+)[\'"]',
        'vue': r'(?:import\s+.*?from\s+[\'"]([^\'\"]+)[\'"]|require\s*\([\'"]([^\'\"]+)[\'"]\))',
        'java': r'import\s+(?:static\s+)?([a-zA-Z0-9_\.\*]+);',
        'php': r'namespace\s+([a-zA-Z0-9_\\]+)',
        'csharp': r'using\s+(?:static\s+)?([a-zA-Z0-9_\.]+);',
        'ruby': r'require(?:_relative)?\s+[\'"]([^\'"]+)[\'"]',
        'go': r'import\s+(?:\([^)]*\)|[\'"]([^\'\"]+)[\'"])',
        'cpp': r'#include\s*[<"]([^>"]+)[>"]',
        'c': r'#include\s*[<"]([^>"]+)[>"]',
        'kotlin': r'import\s+([^\n]+)',
        'swift': r'import\s+([^\n]+)',
        'zig': r'(?:const|pub const)\s+(\w+)\s*=\s*@import\("([^"]+)"\);',
        'rush': r'import\s+.*?[\'"]([^\'\"]+)[\'"]',
        'rust': r'(?:use|extern crate)\s+([a-zA-Z0-9_:]+)(?:\s*{[^}]*})?;',
        'scala': r'import\s+([a-zA-Z0-9_\.]+)(?:\._)?(?:\s*{[^}]*})?',
        'dart': r'import\s+[\'"]([^\'"]+)[\'"](?:\s+(?:as|show|hide)\s+[^;]+)?;',
        'r': r'(?:library|require)\s*\([\'"]([^\'"]+)[\'"]\)',
        'julia': r'(?:using|import)\s+([a-zA-Z0-9_\.]+)(?:\s*:\s*[a-zA-Z0-9_,\s]+)?',
        'perl': r'(?:use|require)\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?',
        'lua': r'function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*([^{]+))?'
    }

    CLASS_PATTERNS = {
        'python': r'class\s+(\w+)(?:\((.*?)\))?\s*:',
        'javascript': r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{',
        'typescript': r'(?:class|const)\s+(\w+)(?:\s*(?:extends|implements)\s+([^{]+))?(?:\s*=\s*(?:styled|React\.memo|React\.forwardRef))?\s*[{<]',
        'vue': r'(?:export\s+default\s*{[^}]*name:\s*[\'"](\w+)[\'"]|@Component\s*\(.*?\)\s*class\s+(\w+))',
        'java': r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?',
        'php': r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(?:\\)?[a-zA-Z0-9_\\]+)?(?:\s+implements\s+(?:\\)?[a-zA-Z0-9_\\]+(?:\s*,\s*(?:\\)?[a-zA-Z0-9_\\]+)*)?',
        'csharp': r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s*:\s*([^{]+))?',
        'ruby': r'class\s+(\w+)(?:\s*<\s*(\w+))?',
        'go': r'type\s+(\w+)\s+struct\s*{',
        'cpp': r'(?:class|struct)\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+(\w+))?(?:\s*{)?',
        'c': r'(?:struct|enum|union)\s+(\w+)(?:\s*{)?',
        'kotlin': r'(?:class|interface|object)\s+(\w+)(?:\s*:\s*([^{]+))?',
        'swift': r'(?:class|struct|protocol|enum)\s+(\w+)(?:\s*:\s*([^{]+))?',
        'zig': r'(?:pub\s+)?(?:const|fn)\s+(\w+)\s*=\s*struct\s*{',
        'rush': r'(?:class|interface)\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?',
        'rust': r'(?:struct|enum|trait|impl)\s+(\w+)(?:\s*(?:for\s+(\w+))?)?(?:\s*{|\s*;)?',
        'scala': r'(?:class|object|trait)\s+(\w+)(?:\s*(?:extends|with)\s+([^{]+))?(?:\s*{)?',
        'dart': r'(?:class|abstract class|mixin)\s+(\w+)(?:\s+(?:extends|with|implements)\s+([^{]+))?(?:\s*{)?',
        'r': r'(?:setClass|setRefClass)\s*\([\'"](\w+)[\'"]',
        'julia': r'(?:struct|abstract type|primitive type)\s+(\w+)(?:\s*<:\s*(\w+))?\s*(?:end)?',
        'perl': r'(?:package|use)\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?',
        'lua': r'function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*([^{]+))?'
    }

    FUNCTION_PATTERNS = {
        'python': r'def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*([^:]+))?\s*:',
        'javascript': r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))\s*\((.*?)\)',
        'typescript': r'(?:function|const)\s+(\w+)\s*(?:<[^>]+>)?\s*(?:=\s*)?(?:async\s*)?\((.*?)\)(?:\s*:\s*([^{=]+))?',
        'vue': r'(?:methods:\s*{[^}]*(\w+)\s*\((.*?)\)|@(?:Watch|Prop|Emit)\s*\([^\)]*\)\s*(\w+)\s*\((.*?)\))',
        'java': r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:<[^>]+>\s+)?(\w+)\s+(\w+)\s*\((.*?)\)',
        'php': r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?function\s+(\w+)\s*\([^)]*\)',
        'csharp': r'(?:public|private|protected|internal)?\s*(?:static\s+)?(?:async\s+)?(?:virtual\s+)?(?:<[^>]+>\s+)?(\w+)\s+(\w+)\s*\((.*?)\)',
        'ruby': r'def\s+(?:self\.)?\s*(\w+)(?:\((.*?)\))?',
        'go': r'func\s+(?:\(\w+\s+[^)]+\)\s+)?(\w+)\s*\((.*?)\)(?:\s*\([^)]*\)|[^{]+)?',
        'cpp': r'(?:virtual\s+)?(?:[\w:]+\s+)?(\w+)\s*\((.*?)\)(?:\s*(?:const|override|final|noexcept))?\s*(?:{\s*)?',
        'c': r'(?:static\s+)?(?:[\w*]+\s+)?(\w+)\s*\((.*?)\)(?:\s*{)?',
        'kotlin': r'fun\s+(\w+)\s*\((.*?)\)(?:\s*:\s*([^{]+))?',
        'swift': r'func\s+(\w+)\s*\((.*?)\)(?:\s*->\s*([^{]+))?',
        'zig': r'(?:pub\s+)?fn\s+(\w+)\s*\((.*?)\)(?:\s*([^{]+))?\s*{',
        'rush': r'(?:function|const)\s+(\w+)\s*(?:<[^>]+>)?\s*(?:=\s*)?(?:async\s*)?\((.*?)\)(?:\s*:\s*([^{=]+))?',
        'rust': r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]+>)?\s*\((.*?)\)(?:\s*->\s*([^{]+))?(?:\s*where\s+[^{]+)?\s*{?',
        'scala': r'(?:def|val|var)\s+(\w+)(?:\[.*?\])?\s*(?:\((.*?)\))?(?:\s*:\s*([^=]+))?(?:\s*=)?',
        'dart': r'(?:void\s+)?(\w+)\s*\((.*?)\)(?:\s*async\s*)?(?:\s*\{|\s*=>)',
        'r': r'(\w+)\s*<-\s*function\s*\((.*?)\)',
        'julia': r'function\s+(\w+)\s*\((.*?)\)(?:\s*::\s*([^{]+))?\s*(?:end)?',
        'perl': r'(?:sub|use)\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?',
        'lua': r'function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*([^{]+))?'
    }

    METHOD_PATTERN = r'(?:async\s+)?(\w+)\s*\((.*?)\)\s*{'
    VARIABLE_PATTERN = r'(?:const|let|var)\s+(\w+)\s*=\s*([^;]+)'
    ERROR_PATTERN = r'try\s*{[^}]*}\s*catch\s*\((\w+)\)'
    INTERFACE_PATTERN = r'(?:interface|type)\s+(\w+)(?:\s+extends\s+([^{]+))?'
    JSX_COMPONENT_PATTERN = r'<(\w+)(?:\s+[^>]*)?>'

    # Vue specific patterns
    VUE_COMPONENT_PATTERN = r'<template[^>]*>[\s\S]*?<\/template>'
    VUE_SCRIPT_PATTERN = r'<script[^>]*>([\s\S]*?)<\/script>'
    VUE_STYLE_PATTERN = r'<style[^>]*>([\s\S]*?)<\/style>'
    VUE_PROP_PATTERN = r'@Prop\s*\(\s*(?:{[^}]*})?\s*\)\s*(\w+)\s*:'
    VUE_EMIT_PATTERN = r'@Emit\s*\(\s*[\'"](\w+)[\'"]\s*\)'
    VUE_WATCH_PATTERN = r'@Watch\s*\(\s*[\'"](\w+)[\'"]\s*\)'
    VUE_COMPUTED_PATTERN = r'computed:\s*{[^}]*?(\w+)\s*\([^)]*\)\s*{[^}]*}'
    VUE_LIFECYCLE_PATTERN = r'(?:created|mounted|updated|destroyed)\s*\(\s*\)\s*{'

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.analyzer = RulesAnalyzer(project_path)
        
        # Load environment variables from .env
        load_dotenv()
        
        # Initialize Gemini AI
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is required")

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
            )
            self.chat_session = self.model.start_chat(history=[])
            
        except Exception as e:
            print(f"\n⚠️ Error when initializing Gemini AI: {e}")
            raise

    def _get_timestamp(self) -> str:
        """Get current timestamp in standard format."""
        return datetime.now().strftime('%B %d, %Y at %I:%M %p')

    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure and collect detailed information."""
        structure = {
            'files': [],
            'dependencies': {},
            'frameworks': [],
            'languages': {},
            'config_files': [],
            'code_contents': {},
            'directory_structure': {},  # Track directory hierarchy
            'language_stats': {},      # Track language statistics by directory
            'patterns': {
                'classes': [],
                'functions': [],
                'imports': [],
                'error_handling': [],
                'configurations': [],
                'naming_patterns': {},
                'code_organization': [],
                'variable_patterns': [],
                'function_patterns': [],
                'class_patterns': [],
                'error_patterns': [],
                'performance_patterns': [],
                'suggest_patterns': [],
                'directory_patterns': []  # Track directory organization patterns
            }
        }

        # Track directory statistics
        dir_stats = {}

        # Analyze each file
        for root, dirs, files in os.walk(self.project_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not any(x in d for x in ['node_modules', 'venv', '.git', '__pycache__', 'build', 'dist'])]
            
            rel_root = os.path.relpath(root, self.project_path)
            if rel_root == '.':
                rel_root = ''
                
            # Initialize directory statistics
            dir_stats[rel_root] = {
                'total_files': 0,
                'code_files': 0,
                'languages': {},
                'frameworks': set(),
                'patterns': {
                    'classes': 0,
                    'functions': 0,
                    'imports': 0
                }
            }

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_path)
                
                # Update directory statistics
                dir_stats[rel_root]['total_files'] += 1
                
                # Analyze code files
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in ['.py', '.js', '.ts', '.tsx', '.vue', '.kt', '.php', '.swift', '.cpp', '.c', '.h', '.hpp', '.cs', '.csx', '.rb', '.go', '.zig', '.rush', '.perl', '.lua']:
                    structure['files'].append(rel_path)
                    dir_stats[rel_root]['code_files'] += 1
                    
                    # Update language statistics
                    lang = self._get_language_from_ext(file_ext)
                    dir_stats[rel_root]['languages'][lang] = dir_stats[rel_root]['languages'].get(lang, 0) + 1
                    structure['languages'][lang] = structure['languages'].get(lang, 0) + 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            structure['code_contents'][rel_path] = content
                            
                            # Analyze based on file type
                            self._analyze_file_by_type(file_ext, content, rel_path, structure, dir_stats[rel_root])
                            
                    except Exception as e:
                        print(f"⚠️ Error reading file {rel_path}: {e}")
                        continue

                # Classify config files
                elif file.endswith(('.json', '.ini', '.conf')):
                    structure['config_files'].append(rel_path)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            structure['patterns']['configurations'].append({
                                'file': rel_path,
                                'content': content
                            })
                    except Exception as e:
                        print(f"⚠️ Error reading config file {rel_path}: {e}")
                        continue

            # Add directory structure information
            if rel_root:
                structure['directory_structure'][rel_root] = {
                    'stats': dir_stats[rel_root],
                    'parent': os.path.dirname(rel_root) or None
                }

        # Analyze directory patterns
        self._analyze_directory_patterns(structure, dir_stats)
        
        return structure

    def _get_language_from_ext(self, ext: str) -> str:
        """Get programming language from file extension."""
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript/React',
            '.vue': 'Vue',
            '.kt': 'Kotlin',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.hpp': 'C++ Header',
            '.cs': 'C#',
            '.csx': 'C# Script',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.zig': 'Zig',
            '.rush': 'Rush',
            '.perl': 'Perl',
            '.lua': 'Lua'
        }
        return lang_map.get(ext, 'Unknown')

    def _analyze_file_by_type(self, file_ext: str, content: str, rel_path: str, structure: Dict[str, Any], dir_stats: Dict[str, Any]):
        """Analyze file based on its type and update both structure and directory statistics."""
        # Language specific analysis
        if file_ext == '.py':
            self._analyze_python_file(content, rel_path, structure)
        elif file_ext == '.js':
            self._analyze_js_file(content, rel_path, structure)
        elif file_ext in ['.ts', '.tsx']:
            self._analyze_ts_file(content, rel_path, structure)
        elif file_ext == '.vue':
            self._analyze_vue_file(content, rel_path, structure)
        elif file_ext == '.java':
            self._analyze_java_file(content, rel_path, structure)
        elif file_ext == '.php':
            self._analyze_php_file(content, rel_path, structure)
        elif file_ext in ['.cs', '.csx']:
            self._analyze_csharp_file(content, rel_path, structure)
        elif file_ext == '.rb':
            self._analyze_ruby_file(content, rel_path, structure)
        elif file_ext == '.go':
            self._analyze_go_file(content, rel_path, structure)
        elif file_ext in ['.cpp', '.hpp', '.cc', '.cxx', '.h++']:
            self._analyze_cpp_file(content, rel_path, structure)
        elif file_ext in ['.c', '.h']:
            self._analyze_c_file(content, rel_path, structure)
        elif file_ext == '.kt':
            self._analyze_kotlin_file(content, rel_path, structure)
        elif file_ext == '.swift':
            self._analyze_swift_file(content, rel_path, structure)
        elif file_ext == '.rs':
            self._analyze_rust_file(content, rel_path, structure)
        elif file_ext == '.scala':
            self._analyze_scala_file(content, rel_path, structure)
        elif file_ext == '.dart':
            self._analyze_dart_file(content, rel_path, structure)
        elif file_ext == '.r':
            self._analyze_r_file(content, rel_path, structure)
        elif file_ext == '.jl':
            self._analyze_julia_file(content, rel_path, structure)
        elif file_ext == '.perl':
            self._analyze_perl_file(content, rel_path, structure)
        elif file_ext == '.lua':
            self._analyze_lua_file(content, rel_path, structure)

        # Update directory statistics
        dir_stats['patterns']['classes'] += len([p for p in structure['patterns']['class_patterns'] if p['file'] == rel_path])
        dir_stats['patterns']['functions'] += len([p for p in structure['patterns']['function_patterns'] if p['file'] == rel_path])
        dir_stats['patterns']['imports'] += len([imp for imp in structure['patterns']['imports'] if imp in rel_path])

    def _analyze_directory_patterns(self, structure: Dict[str, Any], dir_stats: Dict[str, Any]):
        """Analyze directory organization patterns."""
        for dir_path, stats in dir_stats.items():
            if not dir_path:  # Skip root directory
                continue
                
            # Analyze directory naming convention
            dir_name = os.path.basename(dir_path)
            if dir_name.islower():
                pattern = 'lowercase'
            elif dir_name.isupper():
                pattern = 'uppercase'
            elif '_' in dir_name:
                pattern = 'snake_case'
            elif '-' in dir_name:
                pattern = 'kebab-case'
            else:
                pattern = 'mixed'
                
            # Analyze directory purpose
            purpose = []
            if any(x in dir_name.lower() for x in ['test', 'spec', 'mock']):
                purpose.append('testing')
            if any(x in dir_name.lower() for x in ['util', 'helper', 'common', 'shared']):
                purpose.append('utilities')
            if any(x in dir_name.lower() for x in ['model', 'entity', 'domain']):
                purpose.append('domain')
            if any(x in dir_name.lower() for x in ['controller', 'handler', 'service']):
                purpose.append('business_logic')
            if any(x in dir_name.lower() for x in ['view', 'template', 'component']):
                purpose.append('presentation')
                
            # Add directory pattern
            structure['patterns']['directory_patterns'].append({
                'path': dir_path,
                'name_pattern': pattern,
                'purpose': purpose,
                'languages': stats['languages'],
                'total_files': stats['total_files'],
                'code_files': stats['code_files'],
                'code_metrics': stats['patterns']
            })

    def _generate_ai_rules(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rules using Gemini AI based on project analysis."""
        try:
            # Analyze project structure
            project_structure = self._analyze_project_structure()
            
            # Create detailed prompt with more context and examples
            prompt = f"""As an AI assistant working in Cursor IDE, analyze this project to generate comprehensive coding rules and patterns that perfectly match the project's standards.

Project Overview:
Language: {project_info.get('language', 'unknown')}
Framework: {project_info.get('framework', 'none')}
Type: {project_info.get('type', 'generic')}
Description: {project_info.get('description', 'Generic Project')}

Detailed Analysis:
1. Code Metrics:
- Total Files: {len(project_structure['files'])}
- Code Files: {len([f for f in project_structure['files'] if f.endswith(('.py', '.js', '.ts', '.tsx', '.vue', '.kt', '.php', '.swift', '.cpp', '.c', '.h', '.hpp', '.cs', '.csx', '.rb', '.go', '.zig', '.rush'))])}
- Test Files: {len([f for f in project_structure['files'] if 'test' in f.lower()])}
- Config Files: {len(project_structure['config_files'])}

2. Code Patterns Analysis:
- Classes: {len(project_structure['patterns']['class_patterns'])}
- Functions: {len(project_structure['patterns']['function_patterns'])}
- Imports: {len(project_structure['patterns']['imports'])}
- Error Patterns: {len(project_structure['patterns']['error_patterns'])}

3. Directory Structure:
{chr(10).join([f"- {dir_path}: {stats['total_files']} files" for dir_path, stats in project_structure.get('directory_structure', {}).items()][:10])}

4. Common Patterns Found:
Classes:
{chr(10).join([f"- {c['name']} ({c['file']})" for c in project_structure['patterns']['class_patterns'][:5]])}

Functions:
{chr(10).join([f"- {f['name']} ({f['file']})" for f in project_structure['patterns']['function_patterns'][:5]])}

Error Handling:
{chr(10).join([f"- {e['exception_var']} ({e['file']})" for e in project_structure['patterns']['error_patterns'][:5]])}

5. Code Organization:
{chr(10).join([f"- {p['type']}: {p['name']} ({p['file']})" for p in project_structure['patterns']['code_organization'][:5]])}

Based on this analysis, generate comprehensive rules that cover:

1. Code Style:
- Naming conventions (with real examples from the codebase)
- Documentation standards
- String formatting
- File handling
- Error handling
- Performance optimizations
- Type hints usage
- Comments and documentation
- Module organization
- Testing practices

2. Error Handling:
- Exception types used
- Error logging patterns
- Recovery strategies
- Default values
- User feedback

3. Performance:
- Data structure choices
- Caching strategies
- Resource management
- Optimization techniques
- Memory usage

4. Module Organization:
- File structure
- Dependency management
- Module responsibilities
- Code organization
- Naming conventions

Return a JSON object with detailed rules and examples from the actual codebase.
Focus on being specific and actionable, with real examples rather than generic rules.
Include both preferred patterns and patterns to avoid, based on actual code analysis.
"""

            # Get AI response
            response = self.chat_session.send_message(prompt)
            
            # Extract JSON
            json_match = re.search(r'({[\s\S]*})', response.text)
            if not json_match:
                print("⚠️ No JSON found in AI response")
                raise ValueError("Invalid AI response format")
                
            json_str = json_match.group(1)
            
            try:
                ai_rules = json.loads(json_str)
                
                # Validate and enhance rules
                if not isinstance(ai_rules, dict) or 'ai_behavior' not in ai_rules:
                    raise ValueError("Invalid AI rules structure")
                
                # Add metadata
                ai_rules['metadata'] = {
                    'generated_at': self._get_timestamp(),
                    'project_stats': {
                        'total_files': len(project_structure['files']),
                        'code_files': len([f for f in project_structure['files'] if f.endswith(('.py', '.js', '.ts', '.tsx', '.vue', '.kt', '.php', '.swift', '.cpp', '.c', '.h', '.hpp', '.cs', '.csx', '.rb', '.go', '.zig', '.rush'))]),
                        'test_files': len([f for f in project_structure['files'] if 'test' in f.lower()]),
                        'config_files': len(project_structure['config_files'])
                    },
                    'analysis_coverage': {
                        'classes_analyzed': len(project_structure['patterns']['class_patterns']),
                        'functions_analyzed': len(project_structure['patterns']['function_patterns']),
                        'imports_analyzed': len(project_structure['patterns']['imports']),
                        'error_patterns_found': len(project_structure['patterns']['error_patterns'])
                    }
                }
                
                # Add examples from codebase
                ai_rules['ai_behavior']['code_generation']['examples'] = {
                    'class_examples': [{'name': c['name'], 'file': c['file']} for c in project_structure['patterns']['class_patterns'][:5]],
                    'function_examples': [{'name': f['name'], 'file': f['file']} for f in project_structure['patterns']['function_patterns'][:5]],
                    'error_handling_examples': [{'type': e['exception_var'], 'file': e['file']} for e in project_structure['patterns']['error_patterns'][:5]],
                    'code_organization_examples': [{'type': p['type'], 'name': p['name'], 'file': p['file']} for p in project_structure['patterns']['code_organization'][:5]]
                }
                
                return ai_rules
                
            except json.JSONDecodeError as e:
                print(f"⚠️ Error parsing AI response JSON: {e}")
                raise
                
        except Exception as e:
            print(f"⚠️ Error generating AI rules: {e}")
            raise

    def _generate_project_description(self, project_structure: Dict[str, Any]) -> str:
        """Generate project description using AI based on project analysis."""
        try:
            # Analyze core modules
            core_modules = []
            for file in project_structure.get('files', []):
                if file.endswith('.py') and not any(x in file.lower() for x in ['setup', 'config', 'test']):
                    module_info = {
                        'name': file,
                        'classes': [c for c in project_structure['patterns']['class_patterns'] if c['file'] == file],
                        'functions': [f for f in project_structure['patterns']['function_patterns'] if f['file'] == file],
                        'imports': [imp for imp in project_structure['patterns']['imports'] if imp in file]
                    }
                    core_modules.append(module_info)

            # Analyze main patterns
            main_patterns = {
                'error_handling': project_structure.get('patterns', {}).get('error_patterns', []),
                'performance': project_structure.get('patterns', {}).get('performance_patterns', []),
                'code_organization': project_structure.get('patterns', {}).get('code_organization', [])
            }

            # Create detailed prompt for AI
            prompt = f"""Analyze this project structure and create a detailed description (2-3 sentences) that captures its essence:

Project Overview:
1. Core Modules Analysis:
{chr(10).join([f"- {m['name']}: {len(m['classes'])} classes, {len(m['functions'])} functions" for m in core_modules])}

2. Module Responsibilities:
{chr(10).join([f"- {m['name']}: Main purpose indicated by {', '.join([c['name'] for c in m['classes'][:2]])}" for m in core_modules if m['classes']])}

3. Technical Implementation:
- Error Handling: {len(main_patterns['error_handling'])} patterns found
- Performance Optimizations: {len(main_patterns['performance'])} patterns found
- Code Organization: {len(main_patterns['code_organization'])} patterns found

4. Project Architecture:
- Total Files: {len(project_structure.get('files', []))}
- Core Python Modules: {len(core_modules)}
- External Dependencies: {len(project_structure.get('dependencies', {}))}

Based on this analysis, create a description that covers:
1. The project's main purpose and functionality
2. Key technical features and implementation approach
3. Target users and primary use cases
4. Unique characteristics or innovations

Format: Return a clear, concise description focusing on what makes this project unique.
Do not include technical metrics in the description."""

            # Get AI response
            response = self.chat_session.send_message(prompt)
            description = response.text.strip()
            
            # Validate description length and content
            if len(description.split()) > 100:  # Length limit
                description = ' '.join(description.split()[:100]) + '...'
            
            return description
            
        except Exception as e:
            print(f"⚠️ Error generating project description: {e}")
            return "A software project with automated analysis and rule generation capabilities."

    def _generate_markdown_rules(self, project_info: Dict[str, Any], ai_rules: Dict[str, Any]) -> str:
        """Generate rules in markdown format."""
        timestamp = self._get_timestamp()
        description = project_info.get('description', 'A software project with automated analysis and rule generation capabilities.')
        
        markdown = f"""# Project Rules

## Project Information
- **Version**: {project_info.get('version', '1.0')}
- **Last Updated**: {timestamp}
- **Name**: {project_info.get('name', 'Unknown')}
- **Language**: {project_info.get('language', 'unknown')}
- **Framework**: {project_info.get('framework', 'none')}
- **Type**: {project_info.get('type', 'application')}

## Project Description
{description}

## AI Behavior Rules

### Code Generation Style
#### Preferred Patterns
"""
        # Add preferred code generation patterns
        for pattern in ai_rules['ai_behavior']['code_generation']['style']['prefer']:
            markdown += f"- {pattern}\n"
            
        markdown += "\n#### Patterns to Avoid\n"
        for pattern in ai_rules['ai_behavior']['code_generation']['style']['avoid']:
            markdown += f"- {pattern}\n"
            
        markdown += "\n### Error Handling\n#### Preferred Patterns\n"
        for pattern in ai_rules['ai_behavior']['code_generation']['error_handling']['prefer']:
            markdown += f"- {pattern}\n"
            
        markdown += "\n#### Patterns to Avoid\n"
        for pattern in ai_rules['ai_behavior']['code_generation']['error_handling']['avoid']:
            markdown += f"- {pattern}\n"
            
        markdown += "\n### Performance\n#### Preferred Patterns\n"
        for pattern in ai_rules['ai_behavior']['code_generation']['performance']['prefer']:
            markdown += f"- {pattern}\n"
            
        markdown += "\n#### Patterns to Avoid\n"
        for pattern in ai_rules['ai_behavior']['code_generation']['performance']['avoid']:
            markdown += f"- {pattern}\n"
            
        markdown += "\n### Module Organization\n#### Structure\n"
        for item in ai_rules['ai_behavior']['code_generation']['module_organization']['structure']:
            markdown += f"- {item}\n"
            
        markdown += "\n#### Dependencies\n"
        for dep in ai_rules['ai_behavior']['code_generation']['module_organization']['dependencies']:
            markdown += f"- {dep}\n"
            
        markdown += "\n#### Module Responsibilities\n"
        for module, resp in ai_rules['ai_behavior']['code_generation']['module_organization']['responsibilities'].items():
            markdown += f"- **{module}**: {resp}\n"
            
        markdown += "\n#### Rules\n"
        for rule in ai_rules['ai_behavior']['code_generation']['module_organization']['rules']:
            markdown += f"- {rule}\n"
            
        markdown += "\n#### Naming Conventions\n"
        for category, convention in ai_rules['ai_behavior']['code_generation']['module_organization']['naming'].items():
            markdown += f"- **{category}**: {convention}\n"
            
        return markdown

    def generate_rules_file(self, project_info: Dict[str, Any] = None, format: str = 'json') -> str:
        """Generate the .cursorrules file based on project analysis and AI suggestions."""
        try:
            # Use analyzer if no project_info provided
            if project_info is None:
                project_info = self.analyzer.analyze_project_for_rules()
            
            # Analyze project structure
            project_structure = self._analyze_project_structure()
            
            # Generate AI rules
            ai_rules = self._generate_ai_rules(project_info)
            
            # Generate project description
            description = self._generate_project_description(project_structure)
            project_info['description'] = description
            
            # Create rules file path
            rules_file = os.path.join(self.project_path, '.cursorrules')
            
            if format.lower() == 'markdown':
                content = self._generate_markdown_rules(project_info, ai_rules)
                with open(rules_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:  # JSON format
                # Enhanced rules structure
                rules = {
                    "version": "1.0",
                    "last_updated": self._get_timestamp(),
                    "project": {
                        **project_info,
                        "description": description,
                        "stats": {
                            "total_files": len(project_structure['files']),
                            "code_files": len([f for f in project_structure['files'] if f.endswith(('.py', '.js', '.ts', '.tsx', '.vue', '.kt', '.php', '.swift', '.cpp', '.c', '.h', '.hpp', '.cs', '.csx', '.rb', '.go', '.zig', '.rush'))]),
                            "test_files": len([f for f in project_structure['files'] if 'test' in f.lower()]),
                            "config_files": len(project_structure['config_files']),
                            "analysis_coverage": {
                                "classes_analyzed": len(project_structure['patterns']['class_patterns']),
                                "functions_analyzed": len(project_structure['patterns']['function_patterns']),
                                "imports_analyzed": len(project_structure['patterns']['imports']),
                                "error_patterns_found": len(project_structure['patterns']['error_patterns'])
                            }
                        },
                        "structure": {
                            "directories": {
                                dir_path: {
                                    "total_files": stats['total_files'],
                                    "code_files": stats['code_files'],
                                    "languages": stats['languages'],
                                    "patterns": stats['patterns']
                                }
                                for dir_path, stats in project_structure.get('directory_structure', {}).items()
                            },
                            "main_modules": [
                                {
                                    "name": f,
                                    "classes": len([c for c in project_structure['patterns']['class_patterns'] if c['file'] == f]),
                                    "functions": len([func for func in project_structure['patterns']['function_patterns'] if func['file'] == f]),
                                    "imports": len([imp for imp in project_structure['patterns']['imports'] if imp in f])
                                }
                                for f in project_structure['files']
                                if f.endswith(('.py', '.js', '.ts', '.tsx', '.vue', '.kt', '.php', '.swift', '.cpp', '.c', '.h', '.hpp', '.cs', '.csx', '.rb', '.go', '.zig', '.rush'))
                                and not any(x in f.lower() for x in ['test', 'setup', 'config'])
                            ][:10]
                        }
                    },
                    "ai_behavior": {
                        **ai_rules['ai_behavior'],
                        "examples": {
                            "classes": [
                                {
                                    "name": c['name'],
                                    "file": c['file'],
                                    "type": "class",
                                    "inheritance": c.get('inheritance', '')
                                }
                                for c in project_structure['patterns']['class_patterns'][:5]
                            ],
                            "functions": [
                                {
                                    "name": f['name'],
                                    "file": f['file'],
                                    "parameters": f.get('parameters', ''),
                                    "return_type": f.get('return_type', None)
                                }
                                for f in project_structure['patterns']['function_patterns'][:5]
                            ],
                            "error_handling": [
                                {
                                    "type": e['exception_var'],
                                    "file": e['file']
                                }
                                for e in project_structure['patterns']['error_patterns'][:5]
                            ],
                            "code_organization": [
                                {
                                    "type": p['type'],
                                    "name": p['name'],
                                    "file": p['file']
                                }
                                for p in project_structure['patterns']['code_organization'][:5]
                            ]
                        },
                        "patterns": {
                            "naming": {
                                "classes": list(set(c['name'] for c in project_structure['patterns']['class_patterns'][:10])),
                                "functions": list(set(f['name'] for f in project_structure['patterns']['function_patterns'][:10])),
                                "variables": list(set(v['name'] for v in project_structure['patterns'].get('variable_patterns', [])[:10]))
                            },
                            "imports": list(set(project_structure['patterns']['imports'][:20])),
                            "error_handling": list(set(e['exception_var'] for e in project_structure['patterns']['error_patterns'][:10])),
                            "code_organization": list(set(f"{p['type']}: {p['name']}" for p in project_structure['patterns']['code_organization'][:10]))
                        }
                    }
                }
                
                with open(rules_file, 'w', encoding='utf-8') as f:
                    json.dump(rules, f, indent=2)
            
            return rules_file
                
        except Exception as e:
            print(f"❌ Failed to generate rules: {e}")
            raise

    def _analyze_python_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Python file content."""
        # Find imports and dependencies
        imports = re.findall(self.IMPORT_PATTERNS['python'], content, re.MULTILINE)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes and their patterns
        class_patterns = re.finditer(self.CLASS_PATTERNS['python'], content)
        for match in class_patterns:
            class_name = match.group(1)
            inheritance = match.group(2) if match.group(2) else ''
            structure['patterns']['class_patterns'].append({
                'name': class_name,
                'inheritance': inheritance,
                'file': rel_path
            })
        
        # Find and analyze functions
        function_patterns = re.finditer(self.FUNCTION_PATTERNS['python'], content)
        for match in function_patterns:
            func_name = match.group(1)
            params = match.group(2)
            return_type = match.group(3) if match.group(3) else None
            structure['patterns']['function_patterns'].append({
                'name': func_name,
                'parameters': params,
                'return_type': return_type,
                'file': rel_path
            })

    def _analyze_js_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze JavaScript file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['javascript'], content)
        imports = [imp[0] or imp[1] for imp in imports]  # Flatten tuples from regex groups
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes
        classes = re.finditer(self.CLASS_PATTERNS['javascript'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'inheritance': match.group(2) if match.group(2) else '',
                'file': rel_path
            })
        
        # Find functions (including arrow functions)
        functions = re.finditer(self.FUNCTION_PATTERNS['javascript'], content)
        for match in functions:
            name = match.group(1) or match.group(2)  # Get name from either function or variable
            structure['patterns']['function_patterns'].append({
                'name': name,
                'parameters': match.group(3),
                'file': rel_path
            })
            
        # Find object methods
        methods = re.finditer(self.METHOD_PATTERN, content)
        for match in methods:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'type': 'method',
                'file': rel_path
            })
            
        # Find variables and constants
        variables = re.finditer(self.VARIABLE_PATTERN, content)
        for match in variables:
            structure['patterns']['variable_patterns'].append({
                'name': match.group(1),
                'value': match.group(2).strip(),
                'file': rel_path
            })
            
        # Find error handling patterns
        try_blocks = re.finditer(self.ERROR_PATTERN, content)
        for match in try_blocks:
            structure['patterns']['error_patterns'].append({
                'exception_var': match.group(1),
                'file': rel_path
            })
            
        # Find async/await patterns
        if 'async' in content:
            structure['patterns']['performance_patterns'].append({
                'file': rel_path,
                'has_async': True
            })

    def _analyze_kotlin_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Kotlin file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['kotlin'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes
        classes = re.finditer(self.CLASS_PATTERNS['kotlin'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'inheritance': match.group(2).strip() if match.group(2) else '',
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['kotlin'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'return_type': match.group(3).strip() if match.group(3) else None,
                'file': rel_path
            })

    def _analyze_php_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze PHP file content."""
        try:
            # Find imports/requires/namespaces
            imports = []
            lines = content.split('\n')
            
            # Process each line for imports/namespaces
            for line in lines:
                matches = re.finditer(r'(?:namespace\s+([a-zA-Z0-9_\\]+))|(?:use\s+(?:\\)?([a-zA-Z0-9_\\]+)(?:\s+as\s+[a-zA-Z0-9_]+)?)', line)
                for match in matches:
                    import_value = next((g for g in match.groups() if g is not None), None)
                    if import_value and import_value.strip():
                        imports.append(import_value.strip())
            
            if imports:
                structure['dependencies'].update({imp: True for imp in imports})
                structure['patterns']['imports'].extend(imports)
            
            # Find classes
            classes = []
            class_pattern = r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(?:\\)?[a-zA-Z0-9_\\]+)?(?:\s+implements\s+(?:\\)?[a-zA-Z0-9_\\]+(?:\s*,\s*(?:\\)?[a-zA-Z0-9_\\]+)*)?',
            
            for i, line in enumerate(lines, 1):
                matches = re.finditer(class_pattern, line)
                for match in matches:
                    class_info = {
                        'name': match.group(1),
                        'file': rel_path,
                        'line': i
                    }
                    classes.append(class_info)
            
            structure['patterns']['class_patterns'].extend(classes)
            
            # Find functions
            functions = []
            function_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?function\s+(\w+)\s*\([^)]*\)'
            
            for i, line in enumerate(lines, 1):
                matches = re.finditer(function_pattern, line)
                for match in matches:
                    func_info = {
                        'name': match.group(1),
                        'file': rel_path,
                        'line': i
                    }
                    functions.append(func_info)
            
            structure['patterns']['function_patterns'].extend(functions)
                    
        except Exception as e:
            pass

    def _analyze_swift_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Swift file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['swift'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes and protocols
        classes = re.finditer(self.CLASS_PATTERNS['swift'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'inheritance': match.group(2).strip() if match.group(2) else '',
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['swift'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'return_type': match.group(3).strip() if match.group(3) else None,
                'file': rel_path
            })

    def _analyze_ts_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze TypeScript/TSX file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['typescript'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find interfaces and types
        interfaces = re.finditer(self.INTERFACE_PATTERN, content)
        for match in interfaces:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 'interface/type',
                'inheritance': match.group(2).strip() if match.group(2) else '',
                'file': rel_path
            })
        
        # Find classes and components
        classes = re.finditer(self.CLASS_PATTERNS['typescript'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 'class/component',
                'inheritance': match.group(2).strip() if match.group(2) else '',
                'file': rel_path
            })
        
        # Find functions and hooks
        functions = re.finditer(self.FUNCTION_PATTERNS['typescript'], content)
        for match in functions:
            name = match.group(1)
            is_hook = name.startswith('use') and name[3].isupper()
            structure['patterns']['function_patterns'].append({
                'name': name,
                'type': 'hook' if is_hook else 'function',
                'parameters': match.group(2),
                'return_type': match.group(3).strip() if match.group(3) else None,
                'file': rel_path
            })
        
        # Find JSX components in TSX files
        if rel_path.endswith('.tsx'):
            components = re.finditer(self.JSX_COMPONENT_PATTERN, content)
            for match in components:
                component_name = match.group(1)
                if component_name[0].isupper():  # Custom components start with uppercase
                    structure['patterns']['class_patterns'].append({
                        'name': component_name,
                        'type': 'jsx_component',
                        'file': rel_path
                    }) 

    def _analyze_cpp_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze C++ file content."""
        # Find includes
        includes = re.findall(self.IMPORT_PATTERNS['cpp'], content)
        structure['dependencies'].update({inc: True for inc in includes})
        structure['patterns']['imports'].extend(includes)
        
        # Find classes and structs
        classes = re.finditer(self.CLASS_PATTERNS['cpp'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'inheritance': match.group(2) if match.group(2) else '',
                'file': rel_path
            })
        
        # Find functions and methods
        functions = re.finditer(self.FUNCTION_PATTERNS['cpp'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'file': rel_path
            })
            
        # Find templates
        templates = re.finditer(r'template\s*<([^>]+)>', content)
        for match in templates:
            structure['patterns']['code_organization'].append({
                'type': 'template',
                'parameters': match.group(1),
                'file': rel_path
            })
            
        # Find namespaces
        namespaces = re.finditer(r'namespace\s+(\w+)\s*{', content)
        for match in namespaces:
            structure['patterns']['code_organization'].append({
                'type': 'namespace',
                'name': match.group(1),
                'file': rel_path
            })

    def _analyze_c_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze C file content."""
        # Find includes
        includes = re.findall(self.IMPORT_PATTERNS['c'], content)
        structure['dependencies'].update({inc: True for inc in includes})
        structure['patterns']['imports'].extend(includes)
        
        # Find structs and unions
        structs = re.finditer(self.CLASS_PATTERNS['c'], content)
        for match in structs:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 'struct/union',
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['c'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'file': rel_path
            })
            
        # Find macros
        macros = re.finditer(r'#define\s+(\w+)(?:\(([^)]*)\))?\s+(.+)', content)
        for match in macros:
            structure['patterns']['code_organization'].append({
                'type': 'macro',
                'name': match.group(1),
                'parameters': match.group(2) if match.group(2) else '',
                'value': match.group(3),
                'file': rel_path
            })
            
        # Find typedefs
        typedefs = re.finditer(r'typedef\s+(?:struct|enum|union)?\s*(\w+)\s+(\w+);', content)
        for match in typedefs:
            structure['patterns']['code_organization'].append({
                'type': 'typedef',
                'original_type': match.group(1),
                'new_type': match.group(2),
                'file': rel_path
            }) 

    def _analyze_java_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Java file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['java'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes and interfaces
        classes = re.finditer(self.CLASS_PATTERNS['java'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'inheritance': match.group(2) if match.group(2) else '',
                'interfaces': match.group(3).strip() if match.group(3) else '',
                'file': rel_path
            })
        
        # Find methods
        methods = re.finditer(self.FUNCTION_PATTERNS['java'], content)
        for match in methods:
            structure['patterns']['function_patterns'].append({
                'return_type': match.group(1),
                'name': match.group(2),
                'parameters': match.group(3),
                'file': rel_path
            })
            
        # Find annotations
        annotations = re.finditer(r'@(\w+)(?:\((.*?)\))?', content)
        for match in annotations:
            structure['patterns']['code_organization'].append({
                'type': 'annotation',
                'name': match.group(1),
                'parameters': match.group(2) if match.group(2) else '',
                'file': rel_path
            })

    def _analyze_csharp_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze C# file content."""
        # Find using statements
        imports = re.findall(self.IMPORT_PATTERNS['csharp'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes and interfaces
        classes = re.finditer(self.CLASS_PATTERNS['csharp'], content)
        for match in classes:
            inheritance = match.group(2)
            if inheritance:
                inheritance_parts = [p.strip() for p in inheritance.split(',')]
                base_class = inheritance_parts[0] if inheritance_parts else ''
                interfaces = inheritance_parts[1:] if len(inheritance_parts) > 1 else []
            else:
                base_class = ''
                interfaces = []
                
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'inheritance': base_class,
                'interfaces': interfaces,
                'file': rel_path
            })
        
        # Find methods
        methods = re.finditer(self.FUNCTION_PATTERNS['csharp'], content)
        for match in methods:
            structure['patterns']['function_patterns'].append({
                'return_type': match.group(1),
                'name': match.group(2),
                'parameters': match.group(3),
                'file': rel_path
            })
            
        # Find properties
        properties = re.finditer(r'(?:public|private|protected|internal)?\s*(\w+)\s+(\w+)\s*{\s*get;\s*(?:private\s*)?set;\s*}', content)
        for match in properties:
            structure['patterns']['code_organization'].append({
                'type': 'property',
                'type_name': match.group(1),
                'name': match.group(2),
                'file': rel_path
            })

    def _analyze_ruby_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Ruby file content."""
        # Find requires
        imports = re.findall(self.IMPORT_PATTERNS['ruby'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes and modules
        classes = re.finditer(self.CLASS_PATTERNS['ruby'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'inheritance': match.group(2) if match.group(2) else '',
                'file': rel_path
            })
        
        # Find methods
        methods = re.finditer(self.FUNCTION_PATTERNS['ruby'], content)
        for match in methods:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2) if match.group(2) else '',
                'file': rel_path
            })
            
        # Find modules
        modules = re.finditer(r'module\s+(\w+)', content)
        for match in modules:
            structure['patterns']['code_organization'].append({
                'type': 'module',
                'name': match.group(1),
                'file': rel_path
            })
            
        # Find mixins
        mixins = re.finditer(r'include\s+(\w+)', content)
        for match in mixins:
            structure['patterns']['code_organization'].append({
                'type': 'mixin',
                'name': match.group(1),
                'file': rel_path
            })

    def _analyze_go_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Go file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['go'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find structs
        structs = re.finditer(self.CLASS_PATTERNS['go'], content)
        for match in structs:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 'struct',
                'file': rel_path
            })
        
        # Find functions and methods
        functions = re.finditer(self.FUNCTION_PATTERNS['go'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'file': rel_path
            })
            
        # Find interfaces
        interfaces = re.finditer(r'type\s+(\w+)\s+interface\s*{([^}]*)}', content)
        for match in interfaces:
            structure['patterns']['code_organization'].append({
                'type': 'interface',
                'name': match.group(1),
                'methods': match.group(2).strip(),
                'file': rel_path
            })
            
        # Find constants
        constants = re.finditer(r'const\s+\(\s*([^)]+)\s*\)', content)
        for match in constants:
            structure['patterns']['code_organization'].append({
                'type': 'const_block',
                'constants': match.group(1).strip(),
                'file': rel_path
            })

    def _analyze_zig_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Zig file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['zig'], content)
        for imp in imports:
            structure['dependencies'].update({imp[1]: True})  # Use the actual import path
            structure['patterns']['imports'].append(imp[1])
        
        # Find structs
        structs = re.finditer(self.CLASS_PATTERNS['zig'], content)
        for match in structs:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 'struct',
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['zig'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'return_type': match.group(3).strip() if match.group(3) else None,
                'file': rel_path
            })
            
        # Find comptime blocks
        comptimes = re.finditer(r'comptime\s*{([^}]*)}', content)
        for match in comptimes:
            structure['patterns']['code_organization'].append({
                'type': 'comptime_block',
                'content': match.group(1).strip(),
                'file': rel_path
            })
            
        # Find test blocks
        tests = re.finditer(r'test\s+"([^"]+)"\s*{([^}]*)}', content)
        for match in tests:
            structure['patterns']['code_organization'].append({
                'type': 'test',
                'name': match.group(1),
                'content': match.group(2).strip(),
                'file': rel_path
            })

    def _analyze_rush_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Rush file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['rush'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes and interfaces
        classes = re.finditer(self.CLASS_PATTERNS['rush'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'inheritance': match.group(2) if match.group(2) else '',
                'interfaces': match.group(3).strip() if match.group(3) else '',
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['rush'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'return_type': match.group(3).strip() if match.group(3) else None,
                'file': rel_path
            })
            
        # Find decorators
        decorators = re.finditer(r'@(\w+)(?:\((.*?)\))?', content)
        for match in decorators:
            structure['patterns']['code_organization'].append({
                'type': 'decorator',
                'name': match.group(1),
                'parameters': match.group(2) if match.group(2) else '',
                'file': rel_path
            })
            
        # Find type definitions
        types = re.finditer(r'type\s+(\w+)\s*=\s*([^;]+)', content)
        for match in types:
            structure['patterns']['code_organization'].append({
                'type': 'type_definition',
                'name': match.group(1),
                'definition': match.group(2).strip(),
                'file': rel_path
            }) 

    def _analyze_rust_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Rust file content."""
        # Find imports/uses
        imports = re.findall(self.IMPORT_PATTERNS['rust'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find structs, enums, traits and impls
        types = re.finditer(self.CLASS_PATTERNS['rust'], content)
        for match in types:
            type_name = match.group(1)
            impl_for = match.group(2) if match.group(2) else ''
            structure['patterns']['class_patterns'].append({
                'name': type_name,
                'impl_for': impl_for,
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['rust'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'return_type': match.group(3).strip() if match.group(3) else None,
                'file': rel_path
            })
            
        # Find macros
        macros = re.finditer(r'macro_rules!\s+(\w+)\s*{', content)
        for match in macros:
            structure['patterns']['code_organization'].append({
                'type': 'macro',
                'name': match.group(1),
                'file': rel_path
            })

    def _analyze_scala_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Scala file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['scala'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes, objects and traits
        types = re.finditer(self.CLASS_PATTERNS['scala'], content)
        for match in types:
            type_name = match.group(1)
            inheritance = match.group(2).strip() if match.group(2) else ''
            structure['patterns']['class_patterns'].append({
                'name': type_name,
                'inheritance': inheritance,
                'file': rel_path
            })
        
        # Find functions and values
        functions = re.finditer(self.FUNCTION_PATTERNS['scala'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2) if match.group(2) else '',
                'return_type': match.group(3).strip() if match.group(3) else None,
                'file': rel_path
            })
            
        # Find case classes
        case_classes = re.finditer(r'case\s+class\s+(\w+)(?:\[.*?\])?\s*\((.*?)\)', content)
        for match in case_classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 'case_class',
                'parameters': match.group(2),
                'file': rel_path
            })

    def _analyze_dart_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Dart file content."""
        # Find imports
        imports = re.findall(self.IMPORT_PATTERNS['dart'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find classes and mixins
        classes = re.finditer(self.CLASS_PATTERNS['dart'], content)
        for match in classes:
            class_name = match.group(1)
            inheritance = match.group(2).strip() if match.group(2) else ''
            structure['patterns']['class_patterns'].append({
                'name': class_name,
                'inheritance': inheritance,
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['dart'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'file': rel_path
            })
            
        # Find widgets (Flutter)
        widgets = re.finditer(r'class\s+(\w+)\s+extends\s+(?:StatelessWidget|StatefulWidget)', content)
        for match in widgets:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 'widget',
                'file': rel_path
            })

    def _analyze_r_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze R file content."""
        # Find imports/libraries
        imports = re.findall(self.IMPORT_PATTERNS['r'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find S4 classes
        classes = re.finditer(self.CLASS_PATTERNS['r'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 's4_class',
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['r'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'file': rel_path
            })
            
        # Find pipes
        pipes = re.finditer(r'([^%\s]+)\s*%>%\s*([^%\s]+)', content)
        for match in pipes:
            structure['patterns']['code_organization'].append({
                'type': 'pipe',
                'from': match.group(1),
                'to': match.group(2),
                'file': rel_path
            })

    def _analyze_julia_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Julia file content."""
        # Find imports/using
        imports = re.findall(self.IMPORT_PATTERNS['julia'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find types
        types = re.finditer(self.CLASS_PATTERNS['julia'], content)
        for match in types:
            type_name = match.group(1)
            supertype = match.group(2).strip() if match.group(2) else ''
            structure['patterns']['class_patterns'].append({
                'name': type_name,
                'supertype': supertype,
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['julia'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'return_type': match.group(3).strip() if match.group(3) else None,
                'file': rel_path
            })
            
        # Find macros
        macros = re.finditer(r'macro\s+(\w+)\s*\((.*?)\)', content)
        for match in macros:
            structure['patterns']['code_organization'].append({
                'type': 'macro',
                'name': match.group(1),
                'parameters': match.group(2),
                'file': rel_path
            }) 

    def _analyze_perl_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Perl file content."""
        # Find imports/libraries
        imports = re.findall(self.IMPORT_PATTERNS['perl'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find S4 classes
        classes = re.finditer(self.CLASS_PATTERNS['perl'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 's4_class',
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['perl'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'file': rel_path
            })
            
        # Find pipes
        pipes = re.finditer(r'([^%\s]+)\s*%>%\s*([^%\s]+)', content)
        for match in pipes:
            structure['patterns']['code_organization'].append({
                'type': 'pipe',
                'from': match.group(1),
                'to': match.group(2),
                'file': rel_path
            })

    def _analyze_lua_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Lua file content."""
        # Find imports/libraries
        imports = re.findall(self.IMPORT_PATTERNS['lua'], content)
        structure['dependencies'].update({imp: True for imp in imports})
        structure['patterns']['imports'].extend(imports)
        
        # Find S4 classes
        classes = re.finditer(self.CLASS_PATTERNS['lua'], content)
        for match in classes:
            structure['patterns']['class_patterns'].append({
                'name': match.group(1),
                'type': 's4_class',
                'file': rel_path
            })
        
        # Find functions
        functions = re.finditer(self.FUNCTION_PATTERNS['lua'], content)
        for match in functions:
            structure['patterns']['function_patterns'].append({
                'name': match.group(1),
                'parameters': match.group(2),
                'file': rel_path
            })
            
        # Find pipes
        pipes = re.finditer(r'([^%\s]+)\s*%>%\s*([^%\s]+)', content)
        for match in pipes:
            structure['patterns']['code_organization'].append({
                'type': 'pipe',
                'from': match.group(1),
                'to': match.group(2),
                'file': rel_path
            })

    def _analyze_vue_file(self, content: str, rel_path: str, structure: Dict[str, Any]):
        """Analyze Vue file content."""
        # Extract template, script and style sections
        template_match = re.search(self.VUE_COMPONENT_PATTERN, content)
        script_match = re.search(self.VUE_SCRIPT_PATTERN, content)
        style_match = re.search(self.VUE_STYLE_PATTERN, content)
        
        if script_match:
            script_content = script_match.group(1)
            
            # Find imports
            imports = re.findall(self.IMPORT_PATTERNS['vue'], script_content)
            imports = [imp[0] or imp[1] for imp in imports]  # Flatten tuples from regex groups
            structure['dependencies'].update({imp: True for imp in imports})
            structure['patterns']['imports'].extend(imports)
            
            # Find component definitions
            components = re.finditer(self.CLASS_PATTERNS['vue'], script_content)
            for match in components:
                component_name = match.group(1) or match.group(2)  # Get name from options API or class API
                structure['patterns']['class_patterns'].append({
                    'name': component_name,
                    'type': 'vue_component',
                    'file': rel_path
                })
            
            # Find methods
            methods = re.finditer(self.FUNCTION_PATTERNS['vue'], script_content)
            for match in methods:
                method_name = match.group(1) or match.group(3)  # Get name from methods or decorators
                params = match.group(2) or match.group(4)
                structure['patterns']['function_patterns'].append({
                    'name': method_name,
                    'parameters': params,
                    'type': 'vue_method',
                    'file': rel_path
                })
            
            # Find props
            props = re.finditer(self.VUE_PROP_PATTERN, script_content)
            for match in props:
                structure['patterns']['variable_patterns'].append({
                    'name': match.group(1),
                    'type': 'vue_prop',
                    'file': rel_path
                })
            
            # Find emits
            emits = re.finditer(self.VUE_EMIT_PATTERN, script_content)
            for match in emits:
                structure['patterns']['code_organization'].append({
                    'type': 'vue_emit',
                    'name': match.group(1),
                    'file': rel_path
                })
            
            # Find watchers
            watchers = re.finditer(self.VUE_WATCH_PATTERN, script_content)
            for match in watchers:
                structure['patterns']['code_organization'].append({
                    'type': 'vue_watch',
                    'name': match.group(1),
                    'file': rel_path
                })
            
            # Find computed properties
            computed = re.finditer(self.VUE_COMPUTED_PATTERN, script_content)
            for match in computed:
                structure['patterns']['function_patterns'].append({
                    'name': match.group(1),
                    'type': 'vue_computed',
                    'file': rel_path
                })
            
            # Find lifecycle hooks
            lifecycle = re.finditer(self.VUE_LIFECYCLE_PATTERN, script_content)
            for match in lifecycle:
                structure['patterns']['code_organization'].append({
                    'type': 'vue_lifecycle',
                    'hook': match.group(0),
                    'file': rel_path
                })