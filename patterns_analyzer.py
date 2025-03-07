import re
from typing import Dict, Any, Pattern, List, Tuple, Union

class PatternsAnalyzer:
    """Class containing regex patterns for analyzing source code across different languages."""
    
    # Common regex patterns for all languages
    # Language groups:
    # python: Python
    # web: JavaScript, TypeScript, Java, Ruby, Dart, Kotlin
    # system: C/C++, C#, PHP, Swift, Objective-C, Go, Rust
    # data: SQL, R, Julia
    PATTERNS = {
        'import': {
            'python': r'^(?:from\s+(?P<module>[a-zA-Z0-9_\.]+)\s+import\s+(?P<imports>[^#\n]+)|import\s+(?P<module2>[a-zA-Z0-9_\.]+(?:\s*,\s*[a-zA-Z0-9_\.]+)*))(?:\s*#[^\n]*)?$',
            
            'web': r'(?:' + '|'.join([
                r'import\s+.*?from\s+[\'"](?P<module>[^\'\"]+)[\'"]',  # ES6 import
                r'require\s*\([\'"](?P<module2>[^\'\"]+)[\'"]\)',      # CommonJS require
                r'import\s+(?:static\s+)?(?P<module3>[a-zA-Z0-9_\.]+(?:\.[*])?)',  # Java/TypeScript import
                r'require\s+[\'"](?P<module4>[^\'\"]+)[\'"]',          # Ruby require
                r'import\s+[\'"](?P<module5>[^\'\"]+)[\'"]',           # Plain import
                r'package\s+(?P<module6>[a-zA-Z0-9_\.]+);',           # Java/Kotlin package
                r'import\s+(?:package:)?(?P<module7>[^;]+);'          # Dart import
            ]) + ')',
            
            'system': r'(?:' + '|'.join([
                r'#include\s*[<"](?P<module>[^>"]+)[>"]',              # C/C++ include
                r'using\s+(?:static\s+)?(?P<module2>[a-zA-Z0-9_\.]+)\s*;',  # C# using
                r'namespace\s+(?P<module3>[a-zA-Z0-9_\\]+)',          # Namespace
                r'import\s+(?P<module4>[^\n;]+)\s*;?',                # Swift import
                r'#import\s*[<"](?P<module5>[^>"]+)[>"]',             # Objective-C import
                r'import\s+(?:"(?P<module6>[^"]+)"|(?P<module7>[a-zA-Z0-9_/\.]+))',  # Go import
                r'use\s+(?P<module8>[a-zA-Z0-9_:]+)(?:::\{(?P<imports>[^}]+)\})?;'   # Rust use
            ]) + ')',
            
            'data': r'(?:' + '|'.join([
                r'library\s*\((?P<module>[^)]+)\)',                   # R library
                r'source\s*\([\'"](?P<module2>[^\'"]+)[\'"]',         # R source
                r'using\s+(?P<module3>[a-zA-Z0-9_\.]+)',              # Julia using
                r'import\s+(?P<module4>[a-zA-Z0-9_\.]+)',             # Julia import
                r'require\s+[\'"](?P<module5>[^\'"]+)[\'"]'           # SQL require (some dialects)
            ]) + ')',
        },
        
        'class': {
            'python': r'(?:@\w+(?:\(.*?\))?\s+)*class\s+(?P<n>\w+)(?:\((?P<base>[^)]+)\))?\s*:(?:\s*[\'"](?P<docstring>[^\'"]*)[\'"])?',
            
            'web': r'(?:' + '|'.join([
                r'(?:export\s+)?(?:abstract\s+)?class\s+(?P<n>\w+)(?:\s*(?:extends|implements)\s+(?P<base>[^{<]+))?(?:\s*<[^>]+>)?\s*{',  # Standard class
                r'(?:export\s+)?(?:const|let|var)\s+(?P<name2>\w+)\s*=\s*class(?:\s+extends\s+(?P<base2>[^{]+))?\s*{',  # Class expression
                r'(?:export\s+)?class\s+(?P<name3>\w+)\s*(?:<[^>]+>)?\s*(?:extends|implements)\s+(?P<base3>[^{]+)?\s*{',  # Generic class
                r'(?:public|private|protected)?\s+(?:abstract\s+)?class\s+(?P<name4>\w+)(?:\s+extends\s+(?P<base4>[^{]+))?(?:\s+implements\s+(?P<impl>[^{]+))?\s*{',  # Java/Kotlin class
                r'class\s+(?P<name5>\w+)(?:\s+extends\s+(?P<base5>[^{]+))?(?:\s+with\s+(?P<mixins>[^{]+))?(?:\s+implements\s+(?P<impl2>[^{]+))?\s*{'  # Dart class
            ]) + ')',
            
            'system': r'(?:' + '|'.join([
                r'(?:(?:public|private|protected|internal|friend)\s+)*(?:abstract\s+)?(?:partial\s+)?(?:sealed\s+)?(?:class|struct|enum|union|@interface|@implementation)\s+(?P<n>\w+)(?:\s*(?::\s*|extends\s+|implements\s+)(?P<base>[^{;]+))?(?:\s*{)?',  # C++/C#/Java class
                r'(?:@interface|@implementation)\s+(?P<name2>\w+)(?:\s*:\s*(?P<base2>[^{]+))?\s*{?',  # Objective-C interface
                r'type\s+(?P<name3>\w+)\s+struct\s*{',  # Go struct
                r'type\s+(?P<name4>\w+)\s+interface\s*{',  # Go interface
                r'(?:pub\s+)?(?:struct|enum|trait|union)\s+(?P<name5>\w+)(?:<[^>]+>)?\s*(?:where\s+[^{]+)?{',  # Rust struct/enum/trait
                r'impl(?:<[^>]+>)?\s+(?P<name6>\w+)(?:<[^>]+>)?(?:\s+for\s+(?P<for_type>[^{]+))?\s*{'  # Rust impl
            ]) + ')',
            
            'data': r'(?:' + '|'.join([
                r'CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(?P<n>[a-zA-Z0-9_\.]+)',  # SQL table
                r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?P<name2>[a-zA-Z0-9_\.]+)',  # SQL view
                r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?P<name3>[a-zA-Z0-9_\.]+)',  # SQL function
                r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(?P<name4>[a-zA-Z0-9_\.]+)',  # SQL procedure
                r'(?:setClass|setRefClass)\s*\([\'"](?P<name5>[^\'"]+)[\'"]',  # R class
                r'struct\s+(?P<name6>\w+)',  # Julia struct
                r'abstract\s+type\s+(?P<name7>\w+)'  # Julia type
            ]) + ')',
        },
        
        'function': {
            'python': r'(?:@\w+(?:\(.*?\))?\s+)*def\s+(?P<n>\w+)\s*\((?P<params>[^)]*)\)(?:\s*->\s*(?P<return>[^:#]+))?\s*:(?:\s*[\'"](?P<docstring>[^\'"]*)[\'"])?',
            
            'web': r'(?:' + '|'.join([
                r'(?:export\s+)?(?:async\s+)?function\s*(?P<n>\w+)\s*(?:<[^>]+>)?\s*\((?P<params>[^)]*)\)(?:\s*:\s*(?P<return>[^{=]+))?\s*{',  # Standard function
                r'(?:export\s+)?(?:const|let|var)\s+(?P<name2>\w+)\s*=\s*(?:async\s+)?(?:function\s*\*?|\([^)]*\)\s*=>)',  # Function expression/arrow
                r'(?:public|private|protected)?\s*(?:static\s+)?(?:async\s+)?(?P<name3>\w+)\s*\((?P<params2>[^)]*)\)(?:\s*:\s*(?P<return2>[^{;]+))?\s*{?',  # Method
                r'(?:public|private|protected)?(?:\s+override)?\s+(?:static\s+)?(?:final\s+)?(?:void|[a-zA-Z0-9_<>\.]+)\s+(?P<name4>\w+)\s*\((?P<params3>[^)]*)\)\s*(?:throws\s+[^{]+)?\s*{',  # Java method
                r'(?:public|private|protected)?(?:\s+override)?\s+fun\s+(?P<name5>\w+)\s*\((?P<params4>[^)]*)\)(?:\s*:\s*(?P<return3>[^{]+))?\s*{'  # Kotlin function
            ]) + ')',
            
            'system': r'(?:' + '|'.join([
                r'(?:(?:public|private|protected|internal|friend)\s+)*(?:static\s+)?(?:virtual\s+)?(?:override\s+)?(?:async\s+)?(?:[\w:]+\s+)?(?P<n>\w+)\s*\((?P<params>[^)]*)\)(?:\s*(?:const|override|final|noexcept))?\s*(?:{\s*)?',  # C++/C#/Java method
                r'[-+]\s*\((?P<return>[^)]+)\)(?P<name2>\w+)(?::\s*\((?P<paramtype>[^)]+)\)(?P<param>\w+))*',  # Objective-C method
                r'func\s+(?P<name3>\w+)\s*\((?P<params2>[^)]*)\)(?:\s*(?:throws|rethrows))?(?:\s*->\s*(?P<return2>[^{]+))?\s*{',  # Swift function
                r'func\s+(?P<name4>\w+)(?:\([^)]*\))?\s*(?:\s*\([^)]*\))?\s*(?:\s*->\s*[^{]+)?\s*{',  # Go function
                r'(?:pub(?:\([^\)]+\))?\s+)?(?:async\s+)?fn\s+(?P<name5>\w+)(?:<[^>]+>)?\s*\((?P<params3>[^)]*)\)(?:\s*->\s*(?P<return3>[^{]+))?\s*(?:where\s+[^{]+)?\s*{'  # Rust function
            ]) + ')',
            
            'data': r'(?:' + '|'.join([
                r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?P<n>[a-zA-Z0-9_\.]+)\s*\((?P<params>[^)]*)\)',  # SQL function
                r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(?P<name2>[a-zA-Z0-9_\.]+)\s*\((?P<params2>[^)]*)\)',  # SQL procedure
                r'(?P<name3>\w+)\s*<-\s*function\s*\((?P<params3>[^)]*)\)',  # R function
                r'function\s+(?P<name4>\w+)\s*\((?P<params4>[^)]*)\)',  # Julia function
                r'(?P<name5>\w+)\s*=\s*\([^)]*\)\s*->|(?P<name6>\w+)\s*=\s*\([^)]*\)\s*=>'  # Lambda expressions
            ]) + ')',
        },
        
        'common': {
            'method': r'(?:(?:public|private|protected)\s+)?(?:static\s+)?(?:async\s+)?(?P<n>\w+)\s*\((?P<params>[^)]*)\)(?:\s*:\s*(?P<return>[^{]+))?\s*{',
            'variable': r'(?:(?:public|private|protected)\s+)?(?:static\s+)?(?:const|let|var|final)\s+(?P<n>\w+)\s*(?::\s*(?P<type>[^=;]+))?\s*=\s*(?P<value>[^;]+)',
            'error': r'try\s*{(?:[^{}]|{[^{}]*})*}\s*catch\s*\((?P<e>\w+)(?:\s*:\s*(?P<type>[^)]+))?\)',
            'interface': r'(?:export\s+)?interface\s+(?P<n>\w+)(?:\s+extends\s+(?P<base>[^{]+))?\s*{(?:[^{}]|{[^{}]*})*}',
            'jsx_component': r'<(?P<n>[A-Z]\w*)(?:\s+(?:(?!\/>)[^>])+)?>',
            'react_hook': r'\buse[A-Z]\w+\b(?=\s*\()',
            'next_api': r'export\s+(?:async\s+)?function\s+(?:getStaticProps|getStaticPaths|getServerSideProps)\s*\(',
            'next_page': r'(?:pages|app)/(?!_)[^/]+(?:/(?!_)[^/]+)*\.(?:js|jsx|ts|tsx)$',
            'next_layout': r'(?:layout|page|loading|error|not-found)\.(?:js|jsx|ts|tsx)$',
            'next_middleware': r'middleware\.(?:js|jsx|ts|tsx)$',
            'styled_component': r'(?:const\s+)?(?P<n>\w+)\s*=\s*styled(?:\.(?P<element>\w+)|(?:\([\w.]+\)))`[^`]*`',
            
            # Flask patterns
            'flask_route': r'@(?:app|blueprint)\.route\s*\([\'"](?P<route>[^\'"]+)[\'"](?:\s*,\s*methods=(?P<methods>\[[^\]]+\]))?\)',
            'flask_view': r'class\s+(?P<n>\w+)(?:\((?P<base>\w+View)\))?\s*:',
            
            # Django patterns
            'django_model': r'class\s+(?P<n>\w+)\s*\(\s*models\.Model\s*\)\s*:',
            'django_view': r'class\s+(?P<n>\w+)\s*\(\s*(?P<base>View|ListView|DetailView|CreateView|UpdateView|DeleteView|TemplateView)\s*\)\s*:',
            'django_url': r'path\s*\(\s*[\'"](?P<route>[^\'"]+)[\'"](?:\s*,\s*(?P<view>\w+(?:\.\w+)*))?\s*(?:,\s*name=\s*[\'"](?P<name>[^\'"]+)[\'"])?\s*\)',
            
            # FastAPI patterns
            'fastapi_route': r'@(?:app|router)\.(?:get|post|put|delete|patch|options|head)\s*\([\'"](?P<route>[^\'"]+)[\'"](?:\s*,\s*response_model=(?P<model>\w+))?\)',
            'fastapi_dependency': r'Depends\s*\(\s*(?P<dependency>\w+)\s*\)',
            
            # Redux patterns
            'redux_action': r'const\s+(?P<n>\w+)\s*=\s*[\'"](?P<action>[^\'"]+)[\'"]',
            'redux_reducer': r'function\s+(?P<n>\w+)(?:Reducer)?\s*\(\s*(?:state\s*=\s*(?P<initial>[^,)]+))?\s*,\s*action\s*\)',
            'redux_selector': r'export\s+const\s+(?:select|get)(?P<n>\w+)\s*=\s*(?:createSelector|\([^)]*\)\s*=>)',
            
            # Common web patterns
            'api_endpoint': r'(?:GET|POST|PUT|DELETE|PATCH)\s+[\'"](?P<endpoint>/[^\'"]+)[\'"]',
            'jwt_auth': r'(?:jwt|token|auth)\.(?:sign|verify|decode)',
            
            # Testing patterns
            'test_function': r'(?:test|it|describe)\s*\(\s*[\'"](?P<desc>[^\'"]+)[\'"]',
            'assert_statement': r'(?:assert|expect)(?:\.\w+|\([^)]*\))',
            
            # Comment patterns
            'todo_comment': r'(?:\/\/|#|\/\*)\s*TODO\s*(?::|-)?\s*(?P<todo>.*?)(?:\*\/)?$',
            'fixme_comment': r'(?:\/\/|#|\/\*)\s*FIXME\s*(?::|-)?\s*(?P<fixme>.*?)(?:\*\/)?$'
        },
        
        'unity': {
            'component': r'(?:public\s+)?class\s+\w+\s*:\s*(?:MonoBehaviour|ScriptableObject|EditorWindow)',
            'lifecycle': r'(?:private\s+|protected\s+|public\s+)?(?:virtual\s+)?(?:override\s+)?void\s+(?:Awake|Start|Update|FixedUpdate|LateUpdate|OnEnable|OnDisable|OnDestroy|OnTriggerEnter|OnTriggerExit|OnCollisionEnter|OnCollisionExit|OnMouseDown|OnMouseUp|OnGUI)\s*\([^)]*\)',
            'attribute': r'\[\s*(?:SerializeField|Header|Tooltip|Range|RequireComponent|ExecuteInEditMode|CreateAssetMenu|MenuItem)(?:\s*\(\s*(?P<params>[^)]+)\s*\))?\s*\]',
            'type': r'\b(?:GameObject|Transform|Rigidbody|Collider|AudioSource|Camera|Light|Animator|ParticleSystem|Canvas|Image|Text|Button|Vector[23]|Quaternion)\b',
            'event': r'(?:public\s+|private\s+|protected\s+)?UnityEvent\s*<\s*(?P<type>[^>]*)\s*>\s+(?P<n>\w+)',
            'field': r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:\[SerializeField\]\s*)?(?P<type>\w+(?:<[^>]+>)?)\s+(?P<n>\w+)\s*(?:=\s*(?P<value>[^;]+))?;'
        },
        
        # Go patterns
        'go': {
            'struct': r'type\s+(?P<n>\w+)\s+struct\s*{',
            'interface': r'type\s+(?P<n>\w+)\s+interface\s*{',
            'method': r'func\s+\(\s*(?P<receiver>\w+)\s+(?P<receiverType>[*]?\w+)\s*\)\s+(?P<n>\w+)\s*\(',
            'goroutine': r'go\s+(?P<func>\w+\([^)]*\))',
            'channel': r'(?:make\s*\(\s*chan\s+(?P<type>[^)]+)\s*\)|<-\s*chan\s+(?P<type2>[^{]+))'
        },
        
        # Rust patterns
        'rust': {
            'struct': r'(?:pub\s+)?struct\s+(?P<n>\w+)(?:<[^>]+>)?\s*{',
            'enum': r'(?:pub\s+)?enum\s+(?P<n>\w+)(?:<[^>]+>)?\s*{',
            'trait': r'(?:pub\s+)?trait\s+(?P<n>\w+)(?:<[^>]+>)?\s*{',
            'impl': r'impl(?:<[^>]+>)?\s+(?P<for_type>[^{]+)\s*{',
            'macros': r'(?P<n>\w+)!\s*\(',
            'lifetimes': r'<\s*\'(?P<lifetime>\w+)',
            'unsafe': r'unsafe\s*{',
            'derive': r'#\[derive\((?P<traits>[^)]+)\)\]'
        },
        
        # SQL patterns
        'sql': {
            'create_table': r'CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(?P<n>[a-zA-Z0-9_\.]+)\s*\(',
            'create_view': r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?P<n>[a-zA-Z0-9_\.]+)\s+AS',
            'create_index': r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?P<n>[a-zA-Z0-9_\.]+)\s+ON',
            'select': r'SELECT\s+(?P<columns>[^FROM]+)\s+FROM\s+(?P<table>[a-zA-Z0-9_\.]+)',
            'join': r'(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+(?P<table>[a-zA-Z0-9_\.]+)\s+(?:AS\s+(?P<alias>\w+))?\s+ON\s+(?P<condition>[^(WHERE|GROUP|ORDER|LIMIT)]+)',
            'where': r'WHERE\s+(?P<condition>[^(GROUP|ORDER|LIMIT)]+)',
            'transaction': r'(?:BEGIN|START)\s+TRANSACTION'
        },
        
        # GraphQL patterns
        'graphql': {
            'query': r'(?:query|mutation)\s+(?P<n>\w+)(?:\((?P<params>[^)]*)\))?\s*{',
            'type': r'type\s+(?P<n>\w+)(?:\s+implements\s+(?P<implements>\w+))?\s*{',
            'interface': r'interface\s+(?P<n>\w+)\s*{',
            'input': r'input\s+(?P<n>\w+)\s*{',
            'enum': r'enum\s+(?P<n>\w+)\s*{',
            'directive': r'directive\s+@(?P<n>\w+)(?:\((?P<params>[^)]*)\))?\s+on\s+(?P<locations>.+)'
        },
        
        # Docker patterns
        'docker': {
            'from': r'FROM\s+(?P<image>[^\s]+)(?:\s+AS\s+(?P<stage>\w+))?',
            'run': r'RUN\s+(?P<cmd>.+)',
            'copy': r'COPY\s+(?:--from=(?P<from>\w+)\s+)?(?P<src>[^\s]+)\s+(?P<dest>.+)',
            'env': r'ENV\s+(?P<key>\w+)(?:=|\s+)(?P<value>[^\s]+)',
            'expose': r'EXPOSE\s+(?P<ports>[\d\s]+)',
            'volume': r'VOLUME\s+(?P<dirs>.*)',
            'cmd': r'CMD\s+(?P<cmd>.*)',
            'entrypoint': r'ENTRYPOINT\s+(?P<entrypoint>.*)'
        }
    }
    
    # Language groups
    LANGUAGE_GROUPS = {
        'python': ['Python'],
        'web': ['JavaScript', 'TypeScript', 'TypeScript/React', 'Java', 'Ruby', 'Dart', 'Kotlin'],
        'system': ['C++', 'C', 'C/C++ Header', 'C++ Header', 'C#', 'C# Script', 'PHP', 
                   'Swift', 'Objective-C', 'Go', 'Rust'],
        'data': ['SQL', 'R', 'Julia'],
        'markup': ['HTML', 'XML', 'CSS', 'SCSS', 'LESS', 'Markdown']
    }
    
    def __init__(self):
        """Initialize the PatternsAnalyzer with compiled regex patterns."""
        self.compiled_patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Precompile all regex patterns for better performance."""
        compiled = {}
        
        # Compile patterns for each category
        for category, patterns in self.PATTERNS.items():
            compiled[category] = {}
            
            if isinstance(patterns, dict):
                # Handle nested patterns (import, class, function)
                if category in ['import', 'class', 'function']:
                    for lang_group, pattern in patterns.items():
                        compiled[category][lang_group] = re.compile(pattern, re.IGNORECASE if 'sql' in lang_group or 'data' == lang_group else 0)
                # Handle common patterns and other language-specific patterns
                else:
                    for pattern_name, pattern in patterns.items():
                        flags = re.IGNORECASE if category == 'sql' or (category == 'docker') else 0
                        compiled[category][pattern_name] = re.compile(pattern, flags)
            else:
                # Handle simple patterns
                compiled[category] = re.compile(patterns)
                
        return compiled
        
    def get_language_from_ext(self, ext: str) -> str:
        """Get programming language from file extension."""
        lang_map = {
            # Scripting languages
            '.py': 'Python',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.pl': 'Perl',
            '.lua': 'Lua',
            '.sh': 'Shell',
            '.bash': 'Bash',
            
            # Web languages
            '.js': 'JavaScript',
            '.jsx': 'JavaScript/React',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript/React',
            '.html': 'HTML',
            '.htm': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'LESS',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            
            # System languages
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.cpp': 'C++',
            '.cc': 'C++',
            '.cxx': 'C++',
            '.hpp': 'C++ Header',
            '.cs': 'C#',
            '.csx': 'C# Script',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.m': 'Objective-C',
            '.mm': 'Objective-C++',
            
            # Mobile development
            '.kt': 'Kotlin',
            '.kts': 'Kotlin Script',
            '.dart': 'Dart',
            '.swift': 'Swift',
            '.xib': 'iOS Interface',
            '.storyboard': 'iOS Storyboard',
            
            # Data languages
            '.sql': 'SQL',
            '.r': 'R',
            '.jl': 'Julia',
            '.ipynb': 'Jupyter Notebook',
            
            # Configuration
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
            '.xml': 'XML',
            '.ini': 'INI',
            '.conf': 'Config',
            '.csv': 'CSV',
            '.tsv': 'TSV',
            
            # Others
            '.md': 'Markdown',
            '.rst': 'reStructuredText',
            '.tex': 'LaTeX',
            '.graphql': 'GraphQL',
            '.gql': 'GraphQL',
            '.proto': 'Protocol Buffers',
            '.sol': 'Solidity',
            '.f': 'Fortran',
            '.f90': 'Fortran',
            '.d': 'D',
            '.ex': 'Elixir',
            '.exs': 'Elixir Script',
            '.erl': 'Erlang',
            '.hs': 'Haskell',
            '.clj': 'Clojure',
            '.scala': 'Scala',
            '.groovy': 'Groovy',
            '.ps1': 'PowerShell',
            '.bat': 'Batch',
            '.cmake': 'CMake',
            '.asm': 'Assembly',
            '.s': 'Assembly',
            '.objc': 'Objective-C',
        }
        return lang_map.get(ext.lower(), 'Unknown')
        
    def get_language_group(self, language: str) -> str:
        """Determine the language group for a given language."""
        for group, languages in self.LANGUAGE_GROUPS.items():
            if language in languages:
                return group
        return 'unknown'
        
    def analyze_patterns(self, content: str, language: str) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze content for patterns based on language."""
        language_group = self.get_language_group(language)
        results = {
            'imports': [],
            'classes': [],
            'functions': [],
            'variables': [],
            'other_patterns': []
        }
        
        # Analyze imports
        if language_group in self.compiled_patterns['import']:
            pattern = self.compiled_patterns['import'][language_group]
            for match in pattern.finditer(content):
                groups = match.groupdict()
                module = next((v for k, v in groups.items() if v and k.startswith('module')), None)
                if module:
                    results['imports'].append({
                        'module': module.strip(),
                        'span': match.span(),
                        'text': match.group(0)
                    })
        
        # Analyze classes
        if language_group in self.compiled_patterns['class']:
            pattern = self.compiled_patterns['class'][language_group]
            for match in pattern.finditer(content):
                groups = match.groupdict()
                name = next((v for k, v in groups.items() if v and (k == 'name' or k == 'n')), None)
                if name:
                    class_info = {
                        'name': name.strip(),
                        'span': match.span(),
                        'text': match.group(0)
                    }
                    
                    # Add inheritance info if available
                    base = next((v for k, v in groups.items() if v and k.startswith('base')), None)
                    if base:
                        class_info['base'] = base.strip()
                        
                    # Add implementation info if available
                    impl = next((v for k, v in groups.items() if v and k.startswith('impl')), None)
                    if impl:
                        class_info['implements'] = impl.strip()
                        
                    results['classes'].append(class_info)
        
        # Analyze functions
        if language_group in self.compiled_patterns['function']:
            pattern = self.compiled_patterns['function'][language_group]
            for match in pattern.finditer(content):
                groups = match.groupdict()
                name = next((v for k, v in groups.items() if v and (k == 'name' or k == 'n')), None)
                if name:
                    func_info = {
                        'name': name.strip(),
                        'span': match.span(),
                        'text': match.group(0)
                    }
                    
                    # Add parameters if available
                    params = next((v for k, v in groups.items() if v and k.startswith('params')), None)
                    if params:
                        func_info['parameters'] = params.strip()
                        
                    # Add return type if available
                    return_type = next((v for k, v in groups.items() if v and k.startswith('return')), None)
                    if return_type:
                        func_info['return_type'] = return_type.strip()
                        
                    results['functions'].append(func_info)
        
        # Analyze common patterns
        for pattern_name, pattern in self.compiled_patterns['common'].items():
            for match in pattern.finditer(content):
                groups = match.groupdict()
                if any(groups.values()):
                    pattern_info = {
                        'pattern': pattern_name,
                        'span': match.span(),
                        'text': match.group(0),
                        'details': {k: v.strip() if v else v for k, v in groups.items() if v}
                    }
                    results['other_patterns'].append(pattern_info)
        
        # Analyze language-specific patterns
        if language.lower() == 'go' and 'go' in self.compiled_patterns:
            self._analyze_language_specific_patterns(content, 'go', results)
            
        if language.lower() == 'rust' and 'rust' in self.compiled_patterns:
            self._analyze_language_specific_patterns(content, 'rust', results)
            
        if language.lower() == 'sql' and 'sql' in self.compiled_patterns:
            self._analyze_language_specific_patterns(content, 'sql', results)
            
        if language.lower() in ['javascript/react', 'typescript/react'] and 'unity' in self.compiled_patterns:
            self._analyze_language_specific_patterns(content, 'unity', results)
        
        return results
        
    def _analyze_language_specific_patterns(self, content: str, category: str, results: Dict[str, List[Dict[str, Any]]]):
        """Analyze content for language-specific patterns."""
        for pattern_name, pattern in self.compiled_patterns[category].items():
            for match in pattern.finditer(content):
                groups = match.groupdict()
                if any(groups.values()):
                    pattern_info = {
                        'pattern': f"{category}_{pattern_name}",
                        'span': match.span(),
                        'text': match.group(0),
                        'details': {k: v.strip() if v else v for k, v in groups.items() if v}
                    }
                    results['other_patterns'].append(pattern_info) 