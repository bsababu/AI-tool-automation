import ast
import json
import os
import re
import hashlib
import openai
from openai import OpenAI
from dotenv import load_dotenv
import time
import backoff

class ResourceAnalyzer:
    def __init__(self, llm_api_key):
        self.llm_client = OpenAI(api_key=llm_api_key)
        self.memory_intensive_libs = ["pandas", "numpy", "tensorflow", "torch", "sklearn", "flask", "werkzeug"]
        self.network_libs = ["requests", "urllib", "aiohttp", "httpx", "websockets", "socket", "BeautifulSoup"]
        self.response_cache = {}
        self.llm_count = 0
        self.static_count = 0

    def get_analysis_counts(self):
        return {"llm": self.llm_count, "static": self.static_count}

    def analyze_file(self, file_path, repo_structure):
        """Analyze a single Python file using LLM, with static fallback"""
        print(f"Analyzing file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return self._analyze_code(code, file_path, repo_structure)
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            self.static_count += 1
            return {
                "metrics": {"loc": 0, "libraries": []},
                "resources": {
                    "memory": {"base_mb": 10.0, "peak_mb": 20.0, "scaling_factor": 1.0, "notes": "Error fallback"},
                    "cpu": {"estimated_cores": 1.0, "complexity": "O(n)", "parallelization_potential": "low", "notes": "Error fallback"},
                    "bandwidth": {"network_calls_per_execution": 0, "data_transfer_mb": 0.0, "bandwidth_mbps": 0.1, "transfer_type": "bulk", "notes": "Error fallback"},
                    "static_fallback": True
                },
                "source": "static"
            }

    def _analyze_code(self, code, file_path, repo_structure):
        """Use LLM for primary analysis, fallback to static if needed"""
        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        if code_hash in self.response_cache:
            print(f"Using cached result for {file_path}")
            return self.response_cache[code_hash]

        metrics = self._compute_static_metrics(code, file_path)
        llm_profile = self._get_llm_insights(code, file_path, repo_structure, metrics)
        
        if llm_profile and "error" not in llm_profile and self._is_valid_llm_profile(llm_profile):
            self.llm_count += 1
            resource_profile = {
                "metrics": metrics,
                "resources": llm_profile,
                "source": "llm"
            }
        else:
            print(f"LLM analysis failed or invalid for {file_path}, using STATIC ANALYSIS")
            self.static_count += 1
            static_profile = {
                "memory": self._estimate_memory_usage(code),
                "cpu": self._estimate_cpu_usage(code),
                "bandwidth": self._estimate_bandwidth_usage(code),
                "static_fallback": True
            }
            static_profile["memory"]["base_mb"] = max(static_profile["memory"]["base_mb"], 10.0)
            static_profile["memory"]["peak_mb"] = max(static_profile["memory"]["peak_mb"], 20.0)
            static_profile["bandwidth"]["bandwidth_mbps"] = max(static_profile["bandwidth"]["bandwidth_mbps"], 0.1)
            resource_profile = {
                "metrics": metrics,
                "resources": static_profile,
                "source": "static"
            }

        self.response_cache[code_hash] = resource_profile
        return resource_profile

    def _is_valid_llm_profile(self, profile):
        """Validate LLM profile to ensure non-zero resource estimates"""
        try:
            memory = profile.get("memory", {})
            bandwidth = profile.get("bandwidth", {})
            cpu = profile.get("cpu", {})
            return (
                memory.get("base_mb", 0.0) >= 1.0 and
                memory.get("peak_mb", 0.0) >= 1.0 and
                bandwidth.get("bandwidth_mbps", 0.0) >= 0.0 and
                cpu.get("estimated_cores", 0.0) >= 0.5
            )
        except Exception as e:
            print(f"Invalid LLM profile: {str(e)}")
            return False

    def _compute_static_metrics(self, code, file_path):
        """Compute basic static analysis metrics"""
        metrics = {
            "loc": sum(1 for line in code.splitlines() if line.strip() and not line.strip().startswith('#')),
            "libraries": []
        }
        try:
            tree = ast.parse(code)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names if alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            metrics["libraries"] = sorted(set(imp.split('.')[0] for imp in imports if imp))
        except SyntaxError:
            print(f"Syntax error in {file_path}, skipping AST-based metrics")
        return metrics

    @backoff.on_exception(backoff.expo, openai.APIError, max_tries=3, giveup=lambda e: not (isinstance(e, openai.APIError) and e.http_status == 429))
    def _get_llm_insights(self, code, file_path, repo_structure, metrics):
        """Get resource usage insights from LLM with retry on rate limit"""
        load_dotenv("../.env")
        modo = os.getenv("MODEL") or "gpt-4-turbo"
        print(f"Attempting LLM analysis for {file_path} with model {modo}")
        try:
            # Truncate code to 500 lines to reduce token usage
            code_lines = code.splitlines()
            truncated_code = '\n'.join(code_lines[:500])
            prompt = f"""
                You are an expert code analyzer. Analyze the Python code from file '{file_path}'.

                Code:
                ```python
                {truncated_code}
                ```

                Key Imports: {', '.join(metrics['libraries']) or 'None'}

                Static Metrics:
                - Lines of Code: {metrics['loc']}

                Instructions:
                - Identify I/O operations (e.g., file reads/writes) vs. compute-intensive patterns (e.g., nested loops).
                - Estimate resources, ensuring non-zero minimums.
                - For web frameworks (e.g., flask), assume HTTP traffic and higher memory.
                - For I/O-bound tasks, use low CPU (estimated_cores=1.0) and minimal bandwidth (bandwidth_mbps=0.1 if network calls).

                Provide a JSON response:
                ```json
                {{
                "memory": {{
                    "base_mb": float,  // e.g., 100.0 for web apps
                    "peak_mb": float,  // e.g., 200.0
                    "scaling_factor": float,
                    "notes": string
                }},
                "cpu": {{
                    "complexity": string,
                    "estimated_cores": float,
                    "parallelization_potential": string,
                    "notes": string
                }},
                "bandwidth": {{
                    "network_calls_per_execution": int,
                    "data_transfer_mb": float,
                    "bandwidth_mbps": float,
                    "transfer_type": string,
                    "notes": string
                }}
                }}
                ```

                Example for a Flask web app:
                ```json
                {{
                "memory": {{
                    "base_mb": 100.0,
                    "peak_mb": 200.0,
                    "scaling_factor": 2.0,
                    "notes": "Memory for Flask runtime and request handling"
                }},
                "cpu": {{
                    "complexity": "O(n)",
                    "estimated_cores": 2.0,
                    "parallelization_potential": "medium",
                    "notes": "Web request processing"
                }},
                "bandwidth": {{
                    "network_calls_per_execution": 10,
                    "data_transfer_mb": 1.0,
                    "bandwidth_mbps": 1.0,
                    "transfer_type": "streaming",
                    "notes": "HTTP traffic for Flask endpoints"
                }}
                }}
                """
            response = self.llm_client.chat.completions.create(
                model=modo,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            res = response.choices[0].message.content
            print(f"LLM analysis successful for {file_path}, response: {res}")
            parsed = json.loads(res)
            parsed["memory"]["base_mb"] = max(parsed["memory"].get("base_mb", 10.0), 10.0)
            parsed["memory"]["peak_mb"] = max(parsed["memory"].get("peak_mb", 20.0), 20.0)
            parsed["bandwidth"]["bandwidth_mbps"] = max(parsed["bandwidth"].get("bandwidth_mbps", 0.1), 0.1)
            parsed["cpu"]["estimated_cores"] = max(parsed["cpu"].get("estimated_cores", 1.0), 1.0)
            return parsed
        except openai.APIError as e:
            print(f"LLM analysis failed for {file_path}: APIError: {str(e)}")
            raise e  # Let backoff handle retries for 429
        except openai.APIConnectionError as e:
            print(f"LLM analysis failed for {file_path}: APIConnectionError: {str(e)}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            print(f"LLM analysis failed for {file_path}: JSONDecodeError: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            print(f"LLM analysis failed for {file_path}: Unexpected error: {str(e)}")
            return {"error": str(e)}

    def _estimate_memory_usage(self, code):
        """Static fallback for memory usage estimation"""
        memory_profile = {
            "base_mb": 10.0,
            "peak_mb": 20.0,
            "scaling_factor": 1.0,
            "notes": "Static fallback: basic Python runtime",
        }
        
        import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
        imports = re.findall(import_pattern, code)
        for imp in imports:
            for lib in [x for x in imp if x]:
                if lib in self.memory_intensive_libs:
                    memory_profile["base_mb"] += 50.0
                    memory_profile["peak_mb"] += 75.0
                    memory_profile["scaling_factor"] = max(memory_profile["scaling_factor"], 1.5)
                    memory_profile["notes"] += f"; Found {lib}"
        
        large_data_patterns = [
            r"= \[\s*for .+ in .+\]",
            r"= \{\s*for .+ in .+\}",
            r"\.read\(\)",
            r"pd\.read_csv|pd\.read_excel|pd\.read_json",
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
            cpu_profile["complexity"] = f"O(n^{visitor.max_depth})" if visitor.max_depth > 1 else "O(n)"
            cpu_profile["notes"] += f"; Nested loops depth: {visitor.max_depth}"
            
            io_libs = ["os", "shutil", "io"]
            import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
            imports = [imp for imp_pair in re.findall(import_pattern, code) for imp in imp_pair if imp]
            if any(lib in imports for lib in io_libs):
                cpu_profile["estimated_cores"] = 1.0
                cpu_profile["notes"] += "; I/O-bound, single-threaded"
            elif re.search(r"multiprocessing", code):
                cpu_profile["parallelization_potential"]= "high"
                cpu_profile["estimated_cores"] = min(4.0, 1.0 + visitor.max_depth * 0.5)
                cpu_profile["notes"] += "; Parallel processing detected"
            elif re.search(r"threading", code):
                cpu_profile["parallelization_potential"] = "medium"
                cpu_profile["estimated_cores"] = 1.5
                cpu_profile["notes"] += "; Threading detected"
        except SyntaxError:
            pass
        
        return cpu_profile

    def _estimate_bandwidth_usage(self, code):
        """Static fallback for bandwidth usage estimation"""
        bandwidth_profile = {
            "network_calls_per_execution": 0,
            "data_transfer_mb": 0.0,
            "bandwidth_mbps": 0.1,
            "transfer_type": "bulk",
            "notes": "Static fallback: minimal network activity",
        }
        
        import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
        imports = re.findall(import_pattern, code)
        for imp in imports:
            for lib in [x for x in imp if x]:
                if lib in self.network_libs:
                    bandwidth_profile["network_calls_per_execution"] += 1
                    bandwidth_profile["data_transfer_mb"] += 0.5
                    bandwidth_profile["bandwidth_mbps"] += 0.05
                    bandwidth_profile["notes"] += f"; Found {lib}"
                elif lib == "flask":
                    bandwidth_profile["network_calls_per_execution"] += 5
                    bandwidth_profile["data_transfer_mb"] += 1.0
                    bandwidth_profile["bandwidth_mbps"] += 0.5
                    bandwidth_profile["notes"] += "; Flask detected, assuming HTTP traffic"
        
        network_patterns = [
            (r"\.get\(\s*['\"]https?://", 0.1),
            (r"\.post\(\s*['\"]https?://", 0.5),
            (r"\.request\(\s*['\"]https?://", 0.3),
            (r"urllib\.request\.urlopen", 0.2),
            (r"\.download\(", 10.0),
            (r"websockets\.connect", 1.0),
            (r"@app\.route\(", 0.5),  # Flask route decorators
        ]
        for pattern, size_mb in network_patterns:
            matches = re.findall(pattern, code)
            bandwidth_profile["network_calls_per_execution"] += len(matches)
            bandwidth_profile["data_transfer_mb"] += len(matches * size_mb)
        bandwidth_profile["bandwidth_mbps"] = max(bandwidth_profile["bandwidth_mbps"], bandwidth_profile["data_transfer_mb"] / 10)
        
        return bandwidth_profile