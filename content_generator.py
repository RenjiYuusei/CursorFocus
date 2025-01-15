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
from typing import Dict, List, Tuple
import math

class ProjectMetrics:
    def __init__(self):
        self.total_files = 0
        self.total_lines = 0
        self.files_by_type = {}
        self.lines_by_type = {}
        self.alerts = {
            'warning': 0,
            'critical': 0,
            'severe': 0
        }
        self.duplicate_functions = 0
        # Code Quality Metrics
        self.code_smells = {
            'long_functions': [],  # (file_path, function_name, line_count)
            'complex_functions': [], # (file_path, function_name, complexity)
            'deeply_nested': [],  # (file_path, function_name, depth)
            'long_files': [],  # (file_path, line_count)
            'high_complexity_files': [],  # (file_path, complexity)
            'low_cohesion': [],  # (file_path, reason)
            'high_coupling': [],  # (file_path, dependencies_count)
            'naming_issues': [],  # (file_path, identifier, issue)
            'magic_numbers': [],  # (file_path, line_number, value)
            'commented_code': [],  # (file_path, line_number)
            'duplicate_code': []  # (file_path1, file_path2, similarity)
        }
        self.complexity_metrics = {
            'avg_function_length': 0,
            'avg_file_complexity': 0,
            'max_function_length': 0,
            'max_file_complexity': 0,
            'total_functions': 0,
            'cognitive_complexity': 0,  # Độ phức tạp nhận thức
            'dependency_depth': 0,      # Độ sâu phụ thuộc
            'code_duplication_rate': 0, # Tỷ lệ code trùng lặp
            'comment_ratio': 0,         # Tỷ lệ comment/code
            'test_coverage': 0          # Độ phủ test (nếu có)
        }
        self.quality_scores = {
            'maintainability': 0,  # 0-100
            'readability': 0,      # 0-100
            'complexity': 0,       # 0-100
            'testability': 0,      # 0-100
            'reusability': 0,      # 0-100
            'documentation': 0     # 0-100
        }
        self.improvement_suggestions = {
            'critical': [],
            'important': [],
            'minor': []    
        }

def get_file_length_alert(line_count, limit, thresholds):
    """Get alert level based on file length and thresholds."""
    ratio = line_count / limit
    if ratio >= thresholds.get('severe', 2.0):
        return 'severe', f"🚨 Critical-Length Alert: File is more than {int(thresholds['severe']*100)}% of recommended length"
    elif ratio >= thresholds.get('critical', 1.5):
        return 'critical', f"⚠️ High-Length Alert: File is more than {int(thresholds['critical']*100)}% of recommended length"
    elif ratio >= thresholds.get('warning', 1.0):
        return 'warning', f"📄 Length Alert: File exceeds recommended length"
    return None, None

def generate_focus_content(project_path, config):
    """Generate the Focus file content."""
    metrics = ProjectMetrics()
    patterns = {'design_patterns': [], 'anti_patterns': [], 'code_style': [], 'potential_bugs': []}
    suggestions = []
    thresholds = config.get('file_length_thresholds', {
        'warning': 1.0,
        'critical': 1.5,
        'severe': 2.0
    })
    
    project_type = detect_project_type(project_path)
    project_info = get_project_description(project_path)
    
    content = [
        f"# Project Focus: {project_info['name']}",
        "",
        f"**Current Goal:** {project_info['description']}",
        "",
        "**Key Components:**"
    ]
    
    # Add directory structure
    structure = get_directory_structure(project_path, config['max_depth'])
    content.extend(structure_to_tree(structure))
    
    content.extend([
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
        "# File Analysis"
    ])
    
    # Analyze each file
    first_file = True
    for root, _, files in os.walk(project_path):
        if any(ignored in root.split(os.path.sep) for ignored in config['ignored_directories']):
            continue
            
        for file in files:
            if any(file.endswith(ignored.replace('*', '')) for ignored in config['ignored_files']):
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            if is_binary_file(file_path):
                continue
                
            metrics.total_files += 1
            functions, line_count = analyze_file_content(file_path)
            
            # Analyze code quality
            if os.path.splitext(file)[1].lower() in CODE_EXTENSIONS:
                analyze_code_quality(file_path, metrics)
            
            if functions or line_count > 0:
                if not first_file:
                    content.append("")
                else:
                    first_file = False
                
                file_type, file_desc = get_file_type_info(file)
                content.append(f"`{rel_path}` ({line_count} lines)")
                content.append(f"**Main Responsibilities:** {file_desc}")
                
                # Update metrics
                ext = os.path.splitext(file)[1].lower()
                metrics.files_by_type[ext] = metrics.files_by_type.get(ext, 0) + 1
                metrics.lines_by_type[ext] = metrics.lines_by_type.get(ext, 0) + line_count
                metrics.total_lines += line_count
    
    # Add metrics summary
    file_dist = [f"- {ext}: {count} files ({metrics.lines_by_type[ext]:,} lines)" 
                 for ext, count in sorted(metrics.files_by_type.items())]
                 
    design_patterns = [f"  - {pattern}" for pattern in patterns['design_patterns']] or ["  - None detected"]
    anti_patterns = [f"  - {pattern}" for pattern in patterns['anti_patterns']] or ["  - None detected"]
    style_issues = [f"  - {issue}" for issue in patterns['code_style']] or ["  - None detected"]
    potential_bugs = [f"  - {bug}" for bug in patterns['potential_bugs']] or ["  - None detected"]
    improvement_suggestions = suggestions or ["✅ No immediate recommendations"]
    
    content.extend([
        "",
        "# 📊 Project Overview",
        f"**Files:** {metrics.total_files}  |  **Lines:** {metrics.total_lines:,}",
        "",
        "## 📁 File Distribution"
    ] + file_dist + [
        "",
        "# 🔍 Code Quality Analysis",
        "",
        "## 📈 Quality Scores",
        "|     Metric    | Score |  Status  |",
        "|---------------|-------|----------|",
        f"|  Maintainability  | {metrics.quality_scores['maintainability']:.1f}/100 | {'🟢' if metrics.quality_scores['maintainability'] >= 70 else '🔴'} |",
        f"|  Readability     | {metrics.quality_scores['readability']:.1f}/100 | {'🟢' if metrics.quality_scores['readability'] >= 70 else '🔴'} |",
        f"|  Complexity      | {metrics.quality_scores['complexity']:.1f}/100 | {'🟢' if metrics.quality_scores['complexity'] >= 70 else '🔴'} |",
        f"|  Documentation   | {metrics.quality_scores['documentation']:.1f}/100 | {'🟢' if metrics.quality_scores['documentation'] >= 70 else '🔴'} |",
        f"|  Reusability     | {metrics.quality_scores['reusability']:.1f}/100 | {'🟢' if metrics.quality_scores['reusability'] >= 70 else '🔴'} |",
        f"|  Testability     | {metrics.quality_scores['testability']:.1f}/100 | {'🟢' if metrics.quality_scores['testability'] >= 70 else '🔴'} |",
        "",
        "## 📊 Code Metrics",
        f"- Functions: {metrics.complexity_metrics['total_functions']}",
        f"- Average Function Length: {metrics.complexity_metrics['avg_function_length']:.1f} lines",
        f"- Maximum Function Length: {metrics.complexity_metrics['max_function_length']} lines",
        f"- Maximum Complexity: {metrics.complexity_metrics['max_file_complexity']}",
        f"- Comment Ratio: {metrics.complexity_metrics['comment_ratio']:.1%}",
        "",
        "## 🎯 Code Patterns",
        "### ✨ Good Practices",
        "- Design Patterns Used"
    ] + design_patterns + [
        "",
        "### ⚠️ Areas for Improvement",
        "- Anti-Patterns"
    ] + anti_patterns + [
        "- Style Issues"
    ] + style_issues + [
        "- Potential Bugs"
    ] + potential_bugs + [
        "",
        "## 🔄 Recommendations"
    ] + improvement_suggestions + [
        "",
        f"*Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*"
    ])
    
    return '\n'.join(content)

def get_directory_structure(project_path, max_depth=3, current_depth=0):
    """Get the directory structure."""
    if current_depth > max_depth:
        return {}
    
    structure = {}
    try:
        for item in os.listdir(project_path):
            if should_ignore_file(item):
                continue
                
            item_path = os.path.join(project_path, item)
            
            if os.path.isdir(item_path):
                substructure = get_directory_structure(item_path, max_depth, current_depth + 1)
                if substructure:
                    structure[item] = substructure
            else:
                structure[item] = None
    except Exception as e:
        print(f"Error scanning directory {project_path}: {e}")
    
    return structure

def structure_to_tree(structure, prefix=''):
    """Convert directory structure to tree format."""
    lines = []
    items = sorted(list(structure.items()), key=lambda x: (x[1] is not None, x[0]))
    
    for i, (name, substructure) in enumerate(items):
        is_last = i == len(items) - 1
        connector = '└─ ' if is_last else '├─ '
        
        if substructure is None:
            icon = '📄 '
            lines.append(f"{prefix}{connector}{icon}{name}")
        else:
            icon = '📁 '
            lines.append(f"{prefix}{connector}{icon}{name}")
            extension = '   ' if is_last else '│  '
            lines.extend(structure_to_tree(substructure, prefix + extension))
    
    return lines 

def analyze_file_content(file_path):
    """Analyze file content for functions and metrics."""
    try:
        # Skip binary and non-code files
        ext = os.path.splitext(file_path)[1].lower()
        if ext in NON_CODE_EXTENSIONS or ext not in CODE_EXTENSIONS:
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

def analyze_code_complexity(content: str) -> Tuple[int, List[Tuple[str, int]], Dict]:
    """Analyze code complexity using advanced metrics."""
    lines = content.splitlines()
    metrics = {
        'complexity': 0,
        'cognitive_complexity': 0,
        'nested_depth': 0,
        'max_depth': 0,
        'comment_lines': 0,
        'empty_lines': 0,
        'code_lines': 0,
        'magic_numbers': [],
        'naming_issues': [],
        'commented_code': []
    }
    
    functions = []
    current_function = None
    function_start = 0
    nested_depth = 0
    cognitive_weight = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            metrics['empty_lines'] += 1
            continue
            
        # Track comments
        if stripped.startswith('#'):
            metrics['comment_lines'] += 1
            # Check for commented code
            if re.match(r'#\s*(def|class|if|for|while|return|import)', stripped):
                metrics['commented_code'].append(i)
            continue
            
        metrics['code_lines'] += 1
        
        # Track function definitions
        if re.match(r'\s*def\s+\w+\s*\(', line):
            if current_function:
                functions.append((current_function, i - function_start))
            current_function = re.search(r'def\s+(\w+)', line).group(1)
            function_start = i
            
            # Check naming conventions
            if not re.match(r'^[a-z_][a-z0-9_]*$', current_function):
                metrics['naming_issues'].append((i, current_function, 'function_name'))
        
        # Check for magic numbers
        numbers = re.findall(r'\b(\d+)\b', line)
        for num in numbers:
            if len(num) > 1 and not re.match(r'^[01]+$', num):  # Ignore 0, 1 and binary numbers
                metrics['magic_numbers'].append((i, num))
        
        # Track complexity
        control_structures = ['if', 'elif', 'for', 'while', 'except', 'with']
        
        # Basic complexity (McCabe)
        if any(f"{kw} " in stripped for kw in control_structures):
            metrics['complexity'] += 1
            nested_depth += 1
            metrics['max_depth'] = max(metrics['max_depth'], nested_depth)
            
            # Cognitive complexity
            cognitive_weight = nested_depth if nested_depth > 1 else 1
            metrics['cognitive_complexity'] += cognitive_weight
        
        # Additional cognitive complexity for logical operators
        if any(op in stripped for op in ['and', 'or']):
            metrics['cognitive_complexity'] += 1
        
        # Track nesting depth
        if stripped.endswith(':'):
            nested_depth += 1
            metrics['max_depth'] = max(metrics['max_depth'], nested_depth)
        elif re.match(r'\s*return\s', line) or stripped == '':
            nested_depth = max(0, nested_depth - 1)
    
    # Add last function if exists
    if current_function:
        functions.append((current_function, len(lines) - function_start))
    
    metrics['nested_depth'] = nested_depth
    
    return metrics['complexity'] + metrics['max_depth'], functions, metrics

def analyze_code_quality(file_path: str, metrics: ProjectMetrics) -> None:
    """Analyze code quality metrics for a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analyze code patterns
        patterns = analyze_code_patterns(content)
        advanced_metrics = calculate_code_metrics(content, patterns)
        suggestions = get_code_quality_suggestions(patterns, advanced_metrics)
        
        # Get basic metrics
        complexity, functions, detailed_metrics = analyze_code_complexity(content)
        line_count = len(content.splitlines())
        
        # Update code smells
        if line_count > 300:
            metrics.code_smells['long_files'].append((file_path, line_count))
        
        if complexity > 20:
            metrics.code_smells['high_complexity_files'].append((file_path, complexity))
        
        # Analyze functions
        for func_name, func_length in functions:
            metrics.complexity_metrics['total_functions'] += 1
            
            if func_length > 50:
                metrics.code_smells['long_functions'].append((file_path, func_name, func_length))
            
            metrics.complexity_metrics['max_function_length'] = max(
                metrics.complexity_metrics['max_function_length'], 
                func_length
            )
        
        # Update complexity metrics
        metrics.complexity_metrics['max_file_complexity'] = max(
            metrics.complexity_metrics['max_file_complexity'],
            complexity
        )
        
        metrics.complexity_metrics['cognitive_complexity'] = max(
            metrics.complexity_metrics['cognitive_complexity'],
            detailed_metrics['cognitive_complexity']
        )
        
        # Calculate comment ratio
        total_lines = detailed_metrics['code_lines'] + detailed_metrics['comment_lines']
        if total_lines > 0:
            comment_ratio = detailed_metrics['comment_lines'] / total_lines
            metrics.complexity_metrics['comment_ratio'] = comment_ratio
        
        # Update averages
        if metrics.complexity_metrics['total_functions'] > 0:
            metrics.complexity_metrics['avg_function_length'] = (
                sum(f[2] for f in metrics.code_smells['long_functions']) / 
                metrics.complexity_metrics['total_functions']
            )
        
        # Calculate quality scores with improved weights and new metrics
        maintainability = (
            advanced_metrics['maintainability_index'] * 0.6 +
            advanced_metrics['pattern_score'] * 0.2 +
            (100 - advanced_metrics['halstead_metrics']['difficulty']) * 0.2
        )
        
        readability = 100 - min(100, (
            (complexity * 1.5) +
            (detailed_metrics['max_depth'] * 4) +
            ((1 - comment_ratio) * 20) +
            (len(patterns['code_style']) * 10)
        ))
        
        complexity_score = 100 - min(100, (
            (complexity * 2) +
            (detailed_metrics['cognitive_complexity'] * 1.5) +
            (detailed_metrics['max_depth'] * 6) +
            (len(patterns['anti_patterns']) * 10)
        ))
        
        documentation = min(100, (
            (comment_ratio * 50) +
            (40 if detailed_metrics['comment_lines'] > 0 else 0) +
            (10 if any('docstring' in p for p in patterns['design_patterns']) else 0)
        ))
        
        reusability = (
            advanced_metrics['pattern_score'] * 0.4 +
            (100 - advanced_metrics['halstead_metrics']['difficulty']) * 0.3 +
            (100 - len(patterns['anti_patterns']) * 10) * 0.3
        )
        
        testability = 100 - min(100, (
            (complexity * 2) +
            (detailed_metrics['cognitive_complexity'] * 1.5) +
            (len(patterns['potential_bugs']) * 15) +
            (len(patterns['security_issues']) * 10)
        ))
        
        # Update quality scores with weighted average
        alpha = 0.3  # Weight for new scores
        metrics.quality_scores['maintainability'] = (
            metrics.quality_scores['maintainability'] * (1-alpha) + maintainability * alpha
        )
        metrics.quality_scores['readability'] = (
            metrics.quality_scores['readability'] * (1-alpha) + readability * alpha
        )
        metrics.quality_scores['complexity'] = (
            metrics.quality_scores['complexity'] * (1-alpha) + complexity_score * alpha
        )
        metrics.quality_scores['documentation'] = (
            metrics.quality_scores['documentation'] * (1-alpha) + documentation * alpha
        )
        metrics.quality_scores['reusability'] = (
            metrics.quality_scores['reusability'] * (1-alpha) + reusability * alpha
        )
        metrics.quality_scores['testability'] = (
            metrics.quality_scores['testability'] * (1-alpha) + testability * alpha
        )
        
    except Exception as e:
        logging.error(f"Error analyzing code quality for {file_path}: {e}")

def analyze_code_patterns(content: str) -> Dict:
    """Analyze code patterns and design."""
    patterns = {
        'design_patterns': [],     # Các mẫu thiết kế được phát hiện
        'anti_patterns': [],
        'code_style': [],
        'potential_bugs': [],
        'security_issues': [],
        'performance_issues': [],
    }
    
    lines = content.splitlines()
    
    # Detect design patterns
    if re.search(r'class\s+\w+\s*\(\s*\w+\s*\):', content):
        patterns['design_patterns'].append('inheritance')
    if re.search(r'@\s*(classmethod|staticmethod|property)', content):
        patterns['design_patterns'].append('decorator')
    if re.search(r'def\s+__init__\s*\(\s*self\s*,\s*\**\w+\s*\):', content):
        patterns['design_patterns'].append('factory')
        
    # Detect anti-patterns
    if re.search(r'global\s+\w+', content):
        patterns['anti_patterns'].append('global_state')
    if len(re.findall(r'except\s*:', content)) > 0:
        patterns['anti_patterns'].append('bare_except')
    if re.search(r'while\s+True:', content):
        patterns['anti_patterns'].append('infinite_loop')
        
    # Detect code style issues
    if re.search(r'\t', content):
        patterns['code_style'].append('mixed_indentation')
    if re.search(r'[^"]"[^"]+"\s+\+\s+|[^\']\'\w+\'\s+\+\s+', content):
        patterns['code_style'].append('string_concatenation')
        
    # Detect potential errors
    if re.search(r'except\s+\w+\s+as\s+e\s*:\s*pass', content):
        patterns['potential_bugs'].append('swallowed_exception')
    if re.search(r'\bprint\s*\(', content):
        patterns['potential_bugs'].append('debug_print')
        
    # Detect security issues
    if re.search(r'os\.system\s*\(|subprocess\.call\s*\(', content):
        patterns['security_issues'].append('command_injection')
    if re.search(r'eval\s*\(|exec\s*\(', content):
        patterns['security_issues'].append('code_execution')
        
    # Detect performance issues
    if re.search(r'\+\s*=\s*[\'"]|[\'"].+[\'"].join', content):
        patterns['performance_issues'].append('inefficient_string_concat')
    if re.search(r'for\s+.+\s+in\s+range\s*\(\s*len\s*\(', content):
        patterns['performance_issues'].append('inefficient_loop')
        
    return patterns

def calculate_code_metrics(content: str, patterns: Dict) -> Dict:
    """Calculate advanced code metrics."""
    metrics = {
        'maintainability_index': 0,
        'halstead_metrics': {
            'volume': 0,
            'difficulty': 0,
            'effort': 0
        },
        'pattern_score': 0,
        'security_score': 0,
        'performance_score': 0
    }
    
    # Tính Maintainability Index
    lines = content.splitlines()
    loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    cc = sum(1 for l in lines if any(k in l for k in ['if', 'for', 'while', 'except']))
    
    # Halstead metrics
    operators = set(re.findall(r'[+\-*/=<>!&|^~]|\b(if|else|for|while|break|continue|return|in|is|and|or|not)\b', content))
    operands = set(re.findall(r'\b[A-Za-z_]\w*\b|\b\d+\b|\'[^\']*\'|"[^"]*"', content))
    
    n1 = len(operators)  # Unique operators
    n2 = len(operands)   # Unique operands
    N1 = len(re.findall(r'[+\-*/=<>!&|^~]|\b(if|else|for|while|break|continue|return|in|is|and|or|not)\b', content))  # Total operators
    N2 = len(re.findall(r'\b[A-Za-z_]\w*\b|\b\d+\b|\'[^\']*\'|"[^"]*"', content))  # Total operands
    
    # Calculate Halstead metrics
    if n1 > 0 and n2 > 0:
        volume = (N1 + N2) * math.log2(n1 + n2)
        difficulty = (n1 / 2) * (N2 / n2)
        effort = difficulty * volume
        
        metrics['halstead_metrics']['volume'] = volume
        metrics['halstead_metrics']['difficulty'] = difficulty
        metrics['halstead_metrics']['effort'] = effort
    
    # Calculate maintainability index
    if loc > 0:
        metrics['maintainability_index'] = max(0, (171 - 5.2 * math.log(volume) - 0.23 * cc - 16.2 * math.log(loc)) * 100 / 171)
    
    # Calculate pattern score
    good_patterns = len(patterns['design_patterns'])
    bad_patterns = (
        len(patterns['anti_patterns']) + 
        len(patterns['potential_bugs']) + 
        len(patterns['code_style'])
    )
    metrics['pattern_score'] = max(0, 100 - (bad_patterns * 10) + (good_patterns * 5))
    
    # Calculate security score
    security_issues = len(patterns['security_issues'])
    metrics['security_score'] = max(0, 100 - (security_issues * 25))
    
    # Calculate performance score
    perf_issues = len(patterns['performance_issues'])
    metrics['performance_score'] = max(0, 100 - (perf_issues * 15))
    
    return metrics

def get_code_quality_suggestions(patterns: Dict, metrics: Dict) -> List[str]:
    """Generate intelligent code improvement suggestions."""
    suggestions = []
    
    # Design pattern suggestions
    if 'factory' not in patterns['design_patterns'] and metrics['maintainability_index'] < 65:
        suggestions.append("Consider using Factory pattern to improve object creation")
    if 'decorator' not in patterns['design_patterns'] and metrics['pattern_score'] < 70:
        suggestions.append("Use decorators to reduce code duplication")
        
    # Anti-pattern fixes
    if 'global_state' in patterns['anti_patterns']:
        suggestions.append("Avoid global state - use class attributes or dependency injection")
    if 'bare_except' in patterns['anti_patterns']:
        suggestions.append("Specify exception types instead of using bare except")
        
    # Performance improvements
    if 'inefficient_string_concat' in patterns['performance_issues']:
        suggestions.append("Use ''.join() instead of += for string concatenation")
    if 'inefficient_loop' in patterns['performance_issues']:
        suggestions.append("Use enumerate() instead of range(len())")
        
    # Security improvements
    if 'command_injection' in patterns['security_issues']:
        suggestions.append("Use subprocess.run with shell=False to prevent command injection")
    if 'code_execution' in patterns['security_issues']:
        suggestions.append("Avoid using eval() or exec() - they're dangerous")
        
    # Maintainability improvements
    if metrics['maintainability_index'] < 60:
        suggestions.append("Break down complex functions into smaller, focused ones")
    if metrics['halstead_metrics']['difficulty'] > 30:
        suggestions.append("Simplify complex expressions and reduce cognitive load")
        
    return suggestions 