import ast
import json
import os
import re
import hashlib
import openai
from openai import OpenAI
from dotenv import load_dotenv


class ResourceAnalyzer:
    def __init__(self, llm_api_key):
        self.llm_client = OpenAI(api_key=llm_api_key)
        self.memory_intensive_libs = ["pandas", "numpy", "tensorflow", "torch", "sklearn"]
        self.network_libs = ["requests", "urllib", "aiohttp", "httpx", "websockets", "socket", "BeautifulSoup"]
        self.response_cache = {}

    def analyze_file(self, file_path, repo_structure):
        """Analyze a single Python file using LLM, with static fallback"""
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                code = f.read()
                return self._analyze_code(code, file_path, repo_structure)
            except Exception as e:
                return {"error": str(e)}

    def _analyze_code(self, code, file_path, repo_structure):
        """Use LLM for primary analysis, fallback to static if needed"""
        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        if code_hash in self.response_cache:
            return self.response_cache[code_hash]

        llm_profile = self._get_llm_insights(code, file_path, repo_structure)
        if llm_profile and "error" not in llm_profile:
            # print(f"LLM analysis successful Initiated....\n")
            resource_profile = llm_profile
        else:
            print(f"LLM analyzing has failed for {file_path}, \n")
            print(f"Shiffting to using STATIC ANALYSIS \n")
            resource_profile = {
                "memory": self._estimate_memory_usage(code),
                "cpu": self._estimate_cpu_usage(code),
                "bandwidth": self._estimate_bandwidth_usage(code),
                "static_fallback": True,
            }

        self.response_cache[code_hash] = resource_profile
        return resource_profile

    def _get_llm_insights(self, code, file_path, repo_structure):
        """Get resource usage insights from LLM"""
        load_dotenv("../.env")
        modo = os.getenv("MODEL")
        try:
            repo_context = json.dumps(repo_structure, indent=2)
            prompt = f"""
            You are an expert code analyzer. Analyze the following Python code from file '{file_path}' in a repository with the structure:
            ```json
            {repo_context}
            ```

            Code:
            ```python
            {code}
            ```

            Provide a detailed JSON response with quantitative estimates for resource usage:
            ```json
            {{
                "memory": {{
                    "base_mb": float,  // Base memory requirement in MB
                    "peak_mb": float,  // Peak memory requirement in MB
                    "scaling_factor": float,  // Scaling factor (1.0 = constant, >1.0 = grows with input)
                    "notes": string  // Observations (e.g., large data structures, leaks)
                }},
                "cpu": {{
                    "complexity": string,  // Big-O notation (e.g., "O(n)", "O(n^2)")
                    "estimated_cores": float,  // Number of CPU cores needed (e.g., 1.0, 2.5)
                    "parallelization_potential": string,  // "low", "medium", "high"
                    "notes": string  // Observations (e.g., nested loops, recursion)
                }},
                "bandwidth": {{
                    "network_calls_per_execution": int,  // Estimated network calls
                    "data_transfer_mb": float,  // Estimated data transfer per execution
                    "bandwidth_mbps": float,  // Estimated bandwidth in Mbps
                    "transfer_type": string,  // "streaming" or "bulk"
                    "notes": string  // Observations (e.g., libraries used)
                }}
            }}
            ```
            Ensure all fields are populated with reasonable estimates. For CPU, estimate the number of cores based on computational intensity, parallelization potential, and code patterns (e.g., loops, recursion, multiprocessing usage).
            """
            response = self.llm_client.chat.completions.create(
                    model=modo,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
            res = response.choices[0].message.content
            # print(f"\n{res}")
            return json.loads(res)
        except openai.APIError as e:
            print(f"LLM analysis failed for {file_path}: {str(e)}")
            return {"error": str(e)}
        
        except openai.APIConnectionError as e:
            print(f"Failed to connect to OpenAI API: {e}")
            return {"error": str(e)}

    def _estimate_memory_usage(self, code):
        """Static fallback for memory usage estimation"""
        memory_profile = {
            "base_mb": 0.0,
            "peak_mb": 0.0,
            "scaling_factor": 1.0,
            "notes": "Static fallback: basic Python runtime",
        }
        
        import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
        imports = re.findall(import_pattern, code)
        for imp in imports:
            for lib in [x for x in imp if x]:
                if lib in self.memory_intensive_libs:
                    memory_profile["base_mb"] += 50.0
                    memory_profile["scaling_factor"] = max(memory_profile["scaling_factor"], 1.5)
                    memory_profile["notes"] += f"; Found {lib}"
        
        large_data_patterns = [
            r"= \[\s*for .+ in .+\]",
            r"= \{\s*for .+ in .+\}",
            r"\.read\(\)",
            r"pd\.readGRAVITY_csv|pd\.read_excel|pd\.read_json",
            r"class\s+[A-Za-z0-9_]+\s*:",
        ]
        large_structs = sum(len(re.findall(pattern, code)) for pattern in large_data_patterns)
        memory_profile["peak_mb"] += large_structs * 10.0
        
        return memory_profile

    def _estimate_cpu_usage(self, code):
        """Static fallback for CPU usage estimation"""
        cpu_profile = {
            "complexity": "O(n)",
            "estimated_cores": 1.0,
            "parallelization_potential": "low",
            "notes": "Static fallback: basic processing",
        }
        
        try:
            tree = ast.parse(code)
            class LoopVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.max_depth = 0
                    self.current_depth = 0
                def visit_For(self, node):
                    self.current_depth += 1
                    self.max_depth = max(self.max_depth, self.current_depth)
                    self.generic_visit(node)
                    self.current_depth -= 1
                def visit_While(self, node):
                    self.current_depth += 1
                    self.max_depth = max(self.max_depth, self.current_depth)
                    self.generic_visit(node)
                    self.current_depth -= 1
            visitor = LoopVisitor()
            visitor.visit(tree)
            cpu_profile["estimated_cores"] += visitor.max_depth * 0.5  # 0.5 cores per loop depth
            cpu_profile["complexity"] = f"O(n^{visitor.max_depth})" if visitor.max_depth > 1 else "O(n)"
            cpu_profile["notes"] += f"; Nested loops depth: {visitor.max_depth}"
            
            # Check for parallelization
            if re.search(r"multiprocessing|threading", code):
                cpu_profile["parallelization_potential"] = "high"
                cpu_profile["estimated_cores"] += 1.0
        except SyntaxError:
            pass
        
        return cpu_profile

    def _estimate_bandwidth_usage(self, code):
        """Static fallback for bandwidth usage estimation"""
        bandwidth_profile = {
            "network_calls_per_execution": 0,
            "data_transfer_mb": 0.0,
            "bandwidth_mbps": 0.0,
            "transfer_type": "bulk",
            "notes": "Static fallback: no network activity",
        }
        
        import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
        imports = re.findall(import_pattern, code)
        for imp in imports:
            for lib in [x for x in imp if x]:
                if lib in self.network_libs:
                    bandwidth_profile["notes"] += f"; Found {lib}"
        
        network_patterns = [
            (r"\.get\(\s*['\"]https?://", 0.1),
            (r"\.post\(\s*['\"]https?://", 0.5),
            (r"\.request\(\s*['\"]https?://", 0.3),
            (r"urllib\.request\.urlopen", 0.2),
            (r"\.download\(", 10.0),
            (r"websockets\.connect", 1.0),
        ]
        for pattern, size_mb in network_patterns:
            matches = re.findall(pattern, code)
            bandwidth_profile["network_calls_per_execution"] += len(matches)
            bandwidth_profile["data_transfer_mb"] += len(matches) * size_mb
        bandwidth_profile["bandwidth_mbps"] = bandwidth_profile["data_transfer_mb"] / 10
        
        return bandwidth_profile