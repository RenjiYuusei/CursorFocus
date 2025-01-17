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
        
        # Calculate quality scores with improved weights and metrics
        maintainability = calculate_maintainability_score(
            advanced_metrics['maintainability_index'],
            advanced_metrics['pattern_score'],
            advanced_metrics['halstead_metrics'],
            len(patterns['anti_patterns'])
        )
        
        readability = calculate_readability_score(
            complexity,
            detailed_metrics,
            comment_ratio,
            patterns
        )
        
        complexity_score = calculate_complexity_score(
            complexity,
            detailed_metrics,
            patterns
        )
        
        documentation = calculate_documentation_score(
            comment_ratio,
            detailed_metrics,
            patterns
        )
        
        reusability = calculate_reusability_score(
            advanced_metrics,
            patterns
        )
        
        testability = calculate_testability_score(
            complexity,
            detailed_metrics,
            patterns
        )
        
        # Update quality scores with weighted average
        alpha = 0.3  # Weight for new scores
        metrics.quality_scores['maintainability'] = update_score(
            metrics.quality_scores['maintainability'], maintainability, alpha
        )
        metrics.quality_scores['readability'] = update_score(
            metrics.quality_scores['readability'], readability, alpha
        )
        metrics.quality_scores['complexity'] = update_score(
            metrics.quality_scores['complexity'], complexity_score, alpha
        )
        metrics.quality_scores['documentation'] = update_score(
            metrics.quality_scores['documentation'], documentation, alpha
        )
        metrics.quality_scores['reusability'] = update_score(
            metrics.quality_scores['reusability'], reusability, alpha
        )
        metrics.quality_scores['testability'] = update_score(
            metrics.quality_scores['testability'], testability, alpha
        )
        
    except Exception as e:
        logging.error(f"Error analyzing code quality for {file_path}: {e}")

def calculate_maintainability_score(
    maintainability_index: float,
    pattern_score: float,
    halstead_metrics: Dict,
    anti_patterns_count: int
) -> float:
    """Calculate maintainability score with improved weights."""
    # Base maintainability from index
    base_score = maintainability_index * 0.4
    
    # Pattern quality impact
    pattern_impact = pattern_score * 0.25
    
    # Complexity factors
    complexity_impact = (100 - halstead_metrics['difficulty']) * 0.2
    effort_penalty = min(15, (halstead_metrics['effort'] / 1000) * 0.1)
    
    # Anti-pattern impact
    anti_pattern_penalty = min(25, anti_patterns_count * 6)
    
    # Volume consideration
    volume_penalty = min(10, (halstead_metrics['volume'] / 1000) * 0.1)
    
    final_score = base_score + pattern_impact + complexity_impact - effort_penalty - anti_pattern_penalty - volume_penalty
    
    return max(0, min(100, final_score))

def calculate_readability_score(
    complexity: int,
    detailed_metrics: Dict,
    comment_ratio: float,
    patterns: Dict
) -> float:
    """Calculate readability score with improved metrics."""
    base_score = 100
    
    # Complexity impacts
    complexity_penalty = min(25, complexity * 1.2)
    nesting_penalty = min(15, detailed_metrics['max_depth'] * 3)
    
    # Comment quality
    comment_bonus = min(25, comment_ratio * 50)
    comment_quality = 0
    if detailed_metrics['comment_lines'] > 0:
        # Kiểm tra tỷ lệ comment có ý nghĩa
        meaningful_ratio = detailed_metrics.get('meaningful_comments', 0) / detailed_metrics['comment_lines']
        comment_quality = min(15, meaningful_ratio * 30)
    
    # Code style impacts
    style_issues = patterns['code_style']
    style_penalty = min(20, len(style_issues) * 4)
    
    # Variable naming
    naming_penalty = 0
    if 'single_letter_vars' in style_issues:
        naming_penalty += 10
    if 'inconsistent_naming' in style_issues:
        naming_penalty += 8
    
    # Line length consideration
    if 'long_lines' in style_issues:
        style_penalty += min(10, style_issues.count('long_lines') * 2)
    
    final_score = base_score - complexity_penalty - nesting_penalty + comment_bonus + comment_quality - style_penalty - naming_penalty
    
    return max(0, min(100, final_score))

def calculate_complexity_score(
    complexity: int,
    detailed_metrics: Dict,
    patterns: Dict
) -> float:
    """Calculate complexity score with cognitive weight."""
    base_score = 100
    
    # Core complexity metrics
    cyclomatic_penalty = min(25, complexity * 1.8)
    cognitive_penalty = min(25, detailed_metrics['cognitive_complexity'] * 1.2)
    
    # Nesting depth impact
    nesting_penalty = min(15, detailed_metrics['max_depth'] * 5)
    
    # Pattern impacts
    anti_pattern_penalty = min(15, len(patterns['anti_patterns']) * 4)
    
    # Control flow complexity
    control_flow_penalty = 0
    if 'nested_conditionals' in patterns['anti_patterns']:
        control_flow_penalty += 10
    if 'complex_expressions' in patterns['code_style']:
        control_flow_penalty += 8
        
    # Function complexity
    function_penalty = 0
    if detailed_metrics.get('max_function_complexity', 0) > 10:
        function_penalty = min(10, (detailed_metrics['max_function_complexity'] - 10) * 2)
    
    final_score = base_score - cyclomatic_penalty - cognitive_penalty - nesting_penalty - anti_pattern_penalty - control_flow_penalty - function_penalty
    
    return max(0, min(100, final_score))

def calculate_documentation_score(
    comment_ratio: float,
    detailed_metrics: Dict,
    patterns: Dict
) -> float:
    """Calculate documentation score with quality metrics."""
    base_score = 0
    
    # Comment coverage and quality
    comment_score = min(40, comment_ratio * 80)
    
    # Documentation completeness
    has_docstrings = 'docstring' in str(patterns['design_patterns'])
    docstring_score = 0
    if has_docstrings:
        docstring_quality = detailed_metrics.get('docstring_quality', 0)
        docstring_score = min(25, 15 + docstring_quality * 10)
    
    # API documentation
    api_doc_score = 0
    if detailed_metrics.get('has_api_docs', False):
        api_doc_score = 15
    
    # Comment quality metrics
    comment_quality = 0
    if detailed_metrics['comment_lines'] > 0:
        # Meaningful comments ratio
        meaningful_ratio = detailed_metrics.get('meaningful_comments', 0) / detailed_metrics['comment_lines']
        comment_quality = min(20, meaningful_ratio * 40)
        
        # Inline documentation
        if detailed_metrics.get('has_inline_docs', False):
            comment_quality += 5
    
    # Documentation maintenance
    outdated_docs_penalty = 0
    if 'outdated_docs' in patterns.get('documentation_issues', []):
        outdated_docs_penalty = 15
    
    final_score = base_score + comment_score + docstring_score + api_doc_score + comment_quality - outdated_docs_penalty
    
    return min(100, final_score)

def calculate_reusability_score(
    advanced_metrics: Dict,
    patterns: Dict
) -> float:
    """Calculate reusability score with pattern analysis."""
    base_score = advanced_metrics['pattern_score'] * 0.35
    
    # Design pattern implementation
    pattern_bonus = min(25, len(patterns['design_patterns']) * 8)
    
    # Code organization
    organization_score = 0
    if 'modular_design' in patterns['design_patterns']:
        organization_score += 15
    if 'interface_segregation' in patterns['design_patterns']:
        organization_score += 10
    
    # Complexity impact
    complexity_impact = (100 - advanced_metrics['halstead_metrics']['difficulty']) * 0.25
    
    # Dependency management
    dependency_penalty = 0
    if 'high_coupling' in patterns['anti_patterns']:
        dependency_penalty += 15
    if 'circular_dependency' in patterns['anti_patterns']:
        dependency_penalty += 20
    
    # Code duplication
    duplication_penalty = min(20, patterns.get('duplicate_code_percentage', 0) * 2)
    
    final_score = base_score + pattern_bonus + organization_score + complexity_impact - dependency_penalty - duplication_penalty
    
    return max(0, min(100, final_score))

def calculate_testability_score(
    complexity: int,
    detailed_metrics: Dict,
    patterns: Dict
) -> float:
    """Calculate testability score with testing considerations."""
    base_score = 100
    
    # Complexity impacts
    complexity_penalty = min(25, complexity * 1.5)
    cognitive_penalty = min(20, detailed_metrics['cognitive_complexity'] * 1.2)
    
    # Testing infrastructure
    test_bonus = 0
    if detailed_metrics.get('has_unit_tests', False):
        test_bonus += 15
    if detailed_metrics.get('has_integration_tests', False):
        test_bonus += 10
    
    # Code coverage
    coverage_score = min(20, detailed_metrics.get('test_coverage', 0) * 0.2)
    
    # Pattern impacts
    bug_penalty = min(20, len(patterns['potential_bugs']) * 8)
    security_penalty = min(15, len(patterns['security_issues']) * 6)
    
    # Dependency injection
    di_bonus = 10 if 'dependency_injection' in patterns['design_patterns'] else 0
    
    # Mocking difficulty
    mock_penalty = 0
    if 'hard_to_mock' in patterns.get('testing_issues', []):
        mock_penalty = 15
    
    final_score = base_score - complexity_penalty - cognitive_penalty + test_bonus + coverage_score - bug_penalty - security_penalty + di_bonus - mock_penalty
    
    return max(0, min(100, final_score))

def update_score(current: float, new: float, alpha: float) -> float:
    """Update score with exponential moving average."""
    return current * (1 - alpha) + new * alpha

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
    if re.search(r'@\s*(classmethod|staticmethod|property|abstractmethod)', content):
        patterns['design_patterns'].append('decorator')
    if re.search(r'def\s+__init__\s*\(\s*self\s*,\s*\**\w+\s*\):', content):
        patterns['design_patterns'].append('factory')
    if re.search(r'@\s*singleton|_instance\s*=\s*None', content):
        patterns['design_patterns'].append('singleton')
    if re.search(r'def\s+__iter__\s*\(\s*self\s*\)|def\s+__next__\s*\(\s*self\s*\)', content):
        patterns['design_patterns'].append('iterator')
    if re.search(r'def\s+notify|def\s+update|def\s+subscribe|def\s+unsubscribe', content):
        patterns['design_patterns'].append('observer')
        
    # Detect anti-patterns
    if re.search(r'global\s+\w+', content):
        patterns['anti_patterns'].append('global_state')
    if len(re.findall(r'except\s*:', content)) > 0:
        patterns['anti_patterns'].append('bare_except')
    if re.search(r'while\s+True:', content):
        patterns['anti_patterns'].append('infinite_loop')
    if re.search(r'(?:if|while|for).+(?:if|while|for).+(?:if|while|for)', content):
        patterns['anti_patterns'].append('nested_conditionals')
    if re.search(r'print\s*\([^)]*\)\s*#.*debug', content, re.I):
        patterns['anti_patterns'].append('debug_code')
        
    # Detect code style issues
    if re.search(r'\t', content):
        patterns['code_style'].append('mixed_indentation')
    if re.search(r'[^"]"[^"]+"\s+\+\s+|[^\']\'\w+\'\s+\+\s+', content):
        patterns['code_style'].append('string_concatenation')
    if re.search(r'\b(i|j|k|x|y|z)\b\s*=\s*\d+', content):
        patterns['code_style'].append('single_letter_vars')
    if re.search(r'(?:if|while|for).{120,}:', content):
        patterns['code_style'].append('long_lines')
        
    # Detect potential bugs
    if re.search(r'except\s+\w+\s+as\s+e\s*:\s*pass', content):
        patterns['potential_bugs'].append('swallowed_exception')
    if re.search(r'\bprint\s*\(', content):
        patterns['potential_bugs'].append('debug_print')
    if re.search(r'(?:if|while|for).+(?:return|break|continue).+(?:else):', content):
        patterns['potential_bugs'].append('unreachable_code')
    if re.search(r'(?:list|dict|set)\([^)]*\)\s*==\s*(?:list|dict|set)\([^)]*\)', content):
        patterns['potential_bugs'].append('collection_comparison')
        
    # Detect security issues
    if re.search(r'os\.system\s*\(|subprocess\.call\s*\(', content):
        patterns['security_issues'].append('command_injection')
    if re.search(r'eval\s*\(|exec\s*\(', content):
        patterns['security_issues'].append('code_execution')
    if re.search(r'(?:password|secret|key|token)\s*=\s*["\'][^"\']+["\']', content, re.I):
        patterns['security_issues'].append('hardcoded_secrets')
    if re.search(r'input\s*\([^)]*\)', content):
        patterns['security_issues'].append('unvalidated_input')
        
    # Detect performance issues
    if re.search(r'\+\s*=\s*[\'"]|[\'"].+[\'"].join', content):
        patterns['performance_issues'].append('inefficient_string_concat')
    if re.search(r'for\s+.+\s+in\s+range\s*\(\s*len\s*\(', content):
        patterns['performance_issues'].append('inefficient_loop')
    if re.search(r'(?:list|set|dict)\((?:list|set|dict)\([^)]+\)\)', content):
        patterns['performance_issues'].append('nested_conversions')
    if re.search(r'\.index\(|\.count\(', content):
        patterns['performance_issues'].append('inefficient_operations')
        
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