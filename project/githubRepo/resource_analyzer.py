import ast
import json
import re
from openai import OpenAI

class ResourceAnalyzer:
    def __init__(self, llm_api_key=None):
        self.llm_client = OpenAI(api_key=llm_api_key)
        self.memory_intensive_libs = ["pandas", "numpy", "tensorflow", "torch", "sklearn"]
        self.network_libs = ["requests", "urllib", "aiohttp", "httpx", "websockets","socket"]
    
    def analyze_file(self, file_path):
        """Analyze a single Python file for resource usage"""
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                code = f.read()
                return self._analyze_code(code, file_path)
            except Exception as e:
                return {"error": e}
    
    def _analyze_code(self, code, file_path):
        """Use combination of AST parsing and LLM analysis for code"""
        resource_profile = {
            "memory": self._estimate_memory_usage(code),
            "cpu": self._estimate_cpu_usage(code),
            "bandwidth": self._estimate_bandwidth_usage(code),
        }
        
        return resource_profile
    
    def _estimate_memory_usage(self, code):
        """Estimate memory usage patterns"""
        memory_profile = {
            "large_data_structures": 0,
            "memory_intensive_libs": [],
            "potential_memory_leaks": 0,
        }
        
        # Parse imports to find memory-intensive libraries
        import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
        imports = re.findall(import_pattern, code)
        for imp in imports:
            for lib in [x for x in imp if x]:
                if lib in self.memory_intensive_libs:
                    memory_profile["memory_intensive_libs"].append(lib)
        
        
        large_data_patterns = [
            r"= \[\s*for .+ in .+\]",  # List comprehensions
            r"= \{\s*for .+ in .+\}",  # Dict/set comprehensions
            r"\.read\(\)",
            r"pd\.read_csv|pd\.read_excel|pd\.read_json",
        ]
        
        for pattern in large_data_patterns:
            memory_profile["large_data_structures"] += len(re.findall(pattern, code))
            
        return memory_profile
    
    def _estimate_cpu_usage(self, code):
        """Estimate CPU usage patterns"""
        cpu_profile = {
            "nested_loops": 0,
            "recursive_calls": 0,
            "cpu_intensive_operations": 0,
        }
        
        # Check for nested loops
        loop_patterns = [r"for .+ in .+:", r"while .+:"]
        loop_lines = []
        for pattern in loop_patterns:
            loop_lines.extend([(m.start(), m.group()) for m in re.finditer(pattern, code)])
        
        loop_lines.sort()
        loop_depths = {}
        max_depth = 0
        for i, (pos, loop) in enumerate(loop_lines):
            depth = 0
            for prev_pos, _ in loop_lines[:i]:
                if code[prev_pos:pos].count("    ") > depth:
                    depth += 1
            loop_depths[pos] = depth
            max_depth = max(max_depth, depth)
        
        cpu_profile["nested_loops"] = max_depth
        
        try:
            tree = ast.parse(code)
            function_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            for func in function_names:
                if func in code and re.search(rf"{func}\s*\(", code):
                    cpu_profile["recursive_calls"] += 1
        except SyntaxError:
            pass
        
        return cpu_profile
    
    def _estimate_bandwidth_usage(self, code):
        """Estimate bandwidth usage patterns"""
        bandwidth_profile = {
            "network_calls": 0,
            "data_transfers": 0,
            "network_libraries": [],
        }
        
        # network libs
        import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
        imports = re.findall(import_pattern, code)
        for imp in imports:
            for lib in [x for x in imp if x]:
                if lib in self.network_libs:
                    bandwidth_profile["network_libraries"].append(lib)
        
        # Check for API calls
        network_patterns = [
            r"\.get\(\s*['\"]https?://",
            r"\.post\(\s*['\"]https?://",
            r"\.request\(\s*['\"]https?://",
            r"urllib\.request\.urlopen",
            r"\.download\(",
        ]
        
        for pattern in network_patterns:
            bandwidth_profile["network_calls"] += len(re.findall(pattern, code))
            
        return bandwidth_profile
    
    def _get_llm_insights(self, code):
        """Get insights from LLM for more nuanced analysis"""
        # This would call the LLM API to analyze the code
        prompt = f"""
        Analyze the following Python code for resource usage patterns:
        
        ```python
        {code}
        ```
        
        Provide a detailed analysis with quantitative estimates where possible:
        
        1. Memory Usage:
           - Estimate base memory requirements
           - Identify potential memory leaks or inefficient patterns
           - How memory usage scales with input size
        
        2. CPU Usage:
           - Algorithmic complexity of key functions
           - CPU-intensive operations
           - Parallelization opportunities
        
        3. Bandwidth Usage:
           - Network call patterns and frequency
           - Data transfer volumes
           - Streaming vs. bulk transfer patterns
        
        Format your response as JSON with these three categories and Do not include any text outside the JSON.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4-turbo", #gpt-4-turbo | gpt-4o
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            res = response.choices[0].message.content
            try:
                #print(f"LLM response: {json.loads(res)}")
                return json.loads(res)
            except json.JSONDecodeError:
                print("LLM returned non-JSON; skipping LLM augmentation")
                return {} 
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {}