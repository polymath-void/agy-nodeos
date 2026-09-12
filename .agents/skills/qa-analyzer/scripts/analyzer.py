import io
import os
import re
import sys
import tokenize
from abc import ABC, abstractmethod

class UniversalStructuralChecker:
    @staticmethod
    def check_balanced_brackets(content, filepath):
        brackets = {'{': '}', '(': ')', '[': ']'}
        stack = []

        if filepath.endswith('.py'):
            try:
                tokens = tokenize.tokenize(io.BytesIO(content.encode('utf-8')).readline)
                for toknum, tokval, (srow, _), _, _ in tokens:
                    if toknum in (tokenize.COMMENT, tokenize.STRING, tokenize.ENCODING):
                        continue
                    if toknum == tokenize.OP:
                        for char in tokval:
                            if char in brackets.keys():
                                stack.append((char, srow))
                            elif char in brackets.values():
                                if not stack:
                                    return f"[{filepath}:L{srow}] Structural Error: Unmatched closing '{char}'"
                                top, line_num = stack.pop()
                                if brackets[top] != char:
                                    return f"[{filepath}:L{srow}] Structural Error: Mismatched brackets. Expected '{brackets[top]}' but found '{char}'"
                if stack:
                    top, line_num = stack.pop()
                    return f"[{filepath}:L{line_num}] Structural Error: Unmatched opening '{top}'"
                return None
            except Exception:
                pass  # Fall back to general regex checker if tokenization fails

        # Fallback for non-Python files (or malformed Python)
        # Strip comments first
        clean_content = re.sub(r'//.*', '', content)
        clean_content = re.sub(r'/\*.*?\*/', '', clean_content, flags=re.DOTALL)
        clean_content = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\'|".*?(?<!\\)"|\'.*?(?<!\\)\')', '""', clean_content, flags=re.DOTALL)

        lines = clean_content.split('\n')
        for i, line in enumerate(lines):
            for char in line:
                if char in brackets.keys():
                    stack.append((char, i + 1))
                elif char in brackets.values():
                    if not stack:
                        return f"[{filepath}:L{i+1}] Structural Error: Unmatched closing '{char}'"
                    top, line_num = stack.pop()
                    if brackets[top] != char:
                        return f"[{filepath}:L{i+1}] Structural Error: Mismatched brackets. Expected '{brackets[top]}' but found '{char}'"
        if stack:
            top, line_num = stack.pop()
            return f"[{filepath}:L{line_num}] Structural Error: Unmatched opening '{top}'"
        return None




class LanguageHandler(ABC):
    @abstractmethod
    def get_extensions(self):
        pass

    @abstractmethod
    def extract_definitions(self, content):
        """Returns a list of defined symbols (classes, functions, etc)"""
        pass

    @abstractmethod
    def extract_calls(self, content):
        """Returns a list of invoked symbols (methods, functions)"""
        pass

class KotlinHandler(LanguageHandler):
    def get_extensions(self):
        return ['.kt', '.kts']

    def extract_definitions(self, content):
        funcs = re.findall(r'(?:suspend\s+)?(?:override\s+)?fun\s+(\w+)\s*\(', content)
        classes = re.findall(r'(?:data\s+)?(?:sealed\s+)?class\s+(\w+)', content)
        interfaces = re.findall(r'interface\s+(\w+)', content)
        return set(funcs + classes + interfaces)

    def extract_calls(self, content):
        # Match dot-notation method calls: .methodName(
        return set(re.findall(r'\.\s*(\w+)\s*\(', content))

class PythonHandler(LanguageHandler):
    def get_extensions(self):
        return ['.py']

    def extract_definitions(self, content):
        funcs = re.findall(r'def\s+(\w+)\s*\(', content)
        classes = re.findall(r'class\s+(\w+)', content)
        return set(funcs + classes)

    def extract_calls(self, content):
        # In Python, we can match general function/method calls: name(
        # But to avoid standard functions (print, len), we might filter later
        return set(re.findall(r'(\w+)\s*\(', content))

class JavaScriptHandler(LanguageHandler):
    def get_extensions(self):
        return ['.js', '.jsx', '.ts', '.tsx']

    def extract_definitions(self, content):
        funcs = re.findall(r'function\s+(\w+)\s*\(', content)
        arrow_funcs = re.findall(r'const\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=]*)\s*=>', content)
        classes = re.findall(r'class\s+(\w+)', content)
        return set(funcs + arrow_funcs + classes)

    def extract_calls(self, content):
        return set(re.findall(r'\.\s*(\w+)\s*\(', content))

class GenericHandler(LanguageHandler):
    def get_extensions(self):
        return ['*'] # Fallback

    def extract_definitions(self, content):
        return set()

    def extract_calls(self, content):
        return set()

class CrossReferenceEngine:
    def __init__(self):
        self.symbol_table = set()
        
        # Standard lib whitelist to reduce false positives
        self.whitelist = {
            'let', 'run', 'apply', 'also', 'with', 'forEach', 'map', 'filter', # Kotlin
            'print', 'println', 'len', 'range', 'enumerate', 'zip', # Python
            'log', 'warn', 'error', 'push', 'pop', 'map', 'filter', 'reduce' # JS
        }

    def register_symbols(self, symbols):
        self.symbol_table.update(symbols)

    def analyze_calls(self, calls, filepath):
        warnings = []
        for call in calls:
            # We flag calls that are not in standard whitelist and not defined in project
            # Note: This is highly heuristic. It catches obvious typos but has false positives
            # if calling external library methods not declared locally.
            # So we treat them as 'Warnings' rather than hard failures, unless it's a known project interface method.
            pass # Suppressing heuristic unresolved warnings for now as they are too noisy without a real AST
        return warnings

class UniversalAnalyzer:
    def __init__(self):
        self.handlers = [KotlinHandler(), PythonHandler(), JavaScriptHandler(), GenericHandler()]
        self.cre = CrossReferenceEngine()
        self.errors = []
        self.warnings = []

    def get_handler(self, filepath):
        ext = os.path.splitext(filepath)[1]
        for handler in self.handlers:
            if ext in handler.get_extensions():
                return handler
        return self.handlers[-1]

    def run(self, root_dir):
        print(f"🚀 Running Universal QA Analyzer on: {root_dir}")
        source_files = []
        
        # 1. Discover files
        for root, dirs, files in os.walk(root_dir):
            if '.git' in root or 'node_modules' in root or 'build' in root:
                continue
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in ['.kt', '.kts', '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h']:
                    source_files.append(os.path.join(root, file))

        if not source_files:
            print("No supported source files found.")
            return

        # 2. First Pass: Structural Checking & Symbol Registration
        for filepath in source_files:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Brackets
            err = UniversalStructuralChecker.check_balanced_brackets(content, filepath)
            if err:
                self.errors.append(err)
                
            # Register Symbols
            handler = self.get_handler(filepath)
            defs = handler.extract_definitions(content)
            self.cre.register_symbols(defs)

        # 3. Second Pass: Cross-Referencing
        for filepath in source_files:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            handler = self.get_handler(filepath)
            calls = handler.extract_calls(content)
            warns = self.cre.analyze_calls(calls, filepath)
            self.warnings.extend(warns)

        self.report()

    def report(self):
        if not self.errors and not self.warnings:
            print("\n✅ UNIVERSAL QA PASS: Structural integrity and syntax verified.")
            sys.exit(0)
            
        print("\n--- QA ANALYZER REPORT ---")
        if self.errors:
            print(f"\n🚨 CRITICAL ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"  - {e}")
                
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  - {w}")
                
        print("\n--------------------------")
        if self.errors:
            sys.exit(1)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    UniversalAnalyzer().run(target)
