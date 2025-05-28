import ast
import json
import os
import re
import hashlib
import openai
from openai import OpenAI
from dotenv import load_dotenv
import backoff
from .resource_config import MEMORY_CONFIG, CPU_CONFIG, BANDWIDTH_CONFIG, CODE_PATTERNS

class ResourceAnalyzer:
    def __init__(self, llm_api_key):
        self.llm_client = OpenAI(api_key=llm_api_key)
        self.memory_intensive_libs = list(MEMORY_CONFIG["library_impacts"].keys())
        self.network_libs = list(BANDWIDTH_CONFIG["library_impacts"].keys())
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
        metrics = {
            "loc": len([line for line in code.splitlines() if line.strip() and not line.strip().startswith('#')]),
            "libraries": []
        }
        try:

            import_pattern = r"import\s+([a-zA-Z0-9_\.]+)|from\s+([a-zA-Z0-9_\.]+)\s+import"
            imports = re.findall(import_pattern, code)
            for imp in imports:
                for lib in [x for x in imp if x]:
                    base_lib = lib.split('.')[0]
                    if base_lib and base_lib not in metrics["libraries"]:
                        metrics["libraries"].append(base_lib)
                
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        lib_name = name.name.split('.')[0]
                        if lib_name not in metrics["libraries"]:
                            metrics["libraries"].append(lib_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        base_module = node.module.split('.')[0]
                        if base_module not in metrics["libraries"]:
                            metrics["libraries"].append(base_module)
                                    
            metrics["libraries"] = sorted(list(set(metrics["libraries"])))
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {str(e)}")
        return metrics

    @backoff.on_exception(backoff.expo, (openai.AuthenticationError, openai.APIError, openai.RateLimitError), 
    max_tries=3, giveup=lambda e: isinstance(e, openai.AuthenticationError))
    
    def _get_llm_insights(self, code, file_path, repo_structure, metrics):
        """Get resource usage insights from LLM with retry on rate limit"""
        try:
            load_dotenv("../../.env")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {"error": "keys environment variable not set"}
            
            modo = os.getenv("OPEN_MODEL")
            
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
                - Estimate resources based on code patterns and library usage.
                - For web frameworks, consider HTTP traffic and request handling overhead.
                - For data processing libraries, account for data size scaling.
                - For ML frameworks, consider higher memory and CPU requirements.
                - Analyze parallelization potential from async/threading/multiprocessing usage.
                - Consider streaming vs bulk transfer patterns for bandwidth.

                Base your estimates on these guidelines:
                - Memory: Minimum {MEMORY_CONFIG["base"]["min_mb"]}MB base, higher for web/data/ML workloads
                - CPU: {CPU_CONFIG["base_cores"]["io_bound"]} core minimum, scale based on parallelization
                - Bandwidth: Minimum {BANDWIDTH_CONFIG["base_mbps"]["minimal"]}Mbps, higher for web/streaming

                Provide a JSON response:
                ```json
                {{
                "memory": {{
                    "base_mb": float,
                    "peak_mb": float,
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
                """
            response = self.llm_client.chat.completions.create(
                model=modo,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            res = response.choices[0].message.content
            print(f"LLM analysis successful for {file_path}, response: {res}")
            parsed = json.loads(res)

            if not isinstance(parsed, dict):
                return {"error": "Invalid response format"}
            
            if "error" in parsed:
                return parsed
            
            # Validate and adjust the LLM response using configuration bounds
            if "memory" in parsed:
                memory = parsed["memory"]
                memory["base_mb"] = max(memory["base_mb"], MEMORY_CONFIG["base"]["min_mb"])
                memory["peak_mb"] = max(memory["peak_mb"], memory["base_mb"])
                memory["scaling_factor"] = min(max(memory["scaling_factor"], 
                    MEMORY_CONFIG["scaling_factors"]["low"]), 
                    MEMORY_CONFIG["scaling_factors"]["very_high"])
            
            if "cpu" in parsed:
                cpu = parsed["cpu"]
                cpu["estimated_cores"] = max(cpu["estimated_cores"], 
                    CPU_CONFIG["base_cores"]["io_bound"])
                if cpu["parallelization_potential"] not in ["low", "medium", "high"]:
                    cpu["parallelization_potential"] = "low"
            
            if "bandwidth" in parsed:
                bandwidth = parsed["bandwidth"]
                bandwidth["bandwidth_mbps"] = max(bandwidth["bandwidth_mbps"], 
                    BANDWIDTH_CONFIG["base_mbps"]["minimal"])
                bandwidth["network_calls_per_execution"] = max(0, bandwidth["network_calls_per_execution"])
                bandwidth["data_transfer_mb"] = max(0.0, bandwidth["data_transfer_mb"])
                if bandwidth["transfer_type"] not in ["bulk", "streaming"]:
                    bandwidth["transfer_type"] = "bulk"
            
            if not self._is_valid_llm_profile(parsed):
                return {"error": "Invalid profile structure"}
                    
            return parsed
            
        except (openai.APIError, openai.APIConnectionError, json.JSONDecodeError, openai.RateLimitError) as e:
            print(f"LLM analysis failed for {file_path}: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            print(f"LLM analysis failed for {file_path}: {str(e)}")
            return {"error": str(e)}

    def _estimate_memory_usage(self, code):
        """Dynamic memory usage estimation based on code analysis"""
        memory_profile = {
            "base_mb": MEMORY_CONFIG["base"]["min_mb"],
            "peak_mb": MEMORY_CONFIG["base"]["min_mb"] * 2,
            "scaling_factor": MEMORY_CONFIG["scaling_factors"]["low"],
            "notes": "Dynamic analysis based on code patterns",
        }
        
        # Analyze imports for memory-intensive libraries
        import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
        imports = re.findall(import_pattern, code)
        for imp in imports:
            for lib in [x for x in imp if x]:
                if lib in MEMORY_CONFIG["library_impacts"]:
                    impact = MEMORY_CONFIG["library_impacts"][lib]
                    memory_profile["base_mb"] += impact["base"]
                    memory_profile["peak_mb"] += impact["peak"]
                    memory_profile["scaling_factor"] = max(
                        memory_profile["scaling_factor"],
                        MEMORY_CONFIG["scaling_factors"][impact["scaling"]]
                    )
                    memory_profile["notes"] += f"; Using {lib}"
        
        # Analyze code patterns
        for pattern in CODE_PATTERNS["data_processing"]:
            if re.search(pattern, code):
                memory_profile["base_mb"] += MEMORY_CONFIG["base"]["data_processing_mb"]
                memory_profile["scaling_factor"] = max(
                    memory_profile["scaling_factor"],
                    MEMORY_CONFIG["scaling_factors"]["high"]
                )
                memory_profile["notes"] += "; Heavy data processing detected"
                break
        
        return memory_profile

    def _estimate_cpu_usage(self, code):
        """Dynamic CPU usage estimation based on code patterns"""
        cpu_profile = {
            "complexity": "O(n)",
            "estimated_cores": CPU_CONFIG["base_cores"]["io_bound"],
            "parallelization_potential": "low",
            "notes": "Dynamic CPU analysis",
        }
        
        # Analyze code for parallel processing
        for pattern in CODE_PATTERNS["parallel_processing"]:
            if re.search(pattern, code):
                cpu_profile["parallelization_potential"] = "high"
                cpu_profile["estimated_cores"] = CPU_CONFIG["base_cores"]["data_processing"]
                cpu_profile["notes"] += "; Parallel processing capabilities detected"
                break
        
        # Analyze complexity through AST
        try:
            tree = ast.parse(code)
            class ComplexityVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.max_depth = 0
                    self.current_depth = 0
                    self.has_recursion = False

                def visit_FunctionDef(self, node):
                    for n in ast.walk(node):
                        if isinstance(n, ast.Call) and n.func.id == node.name:
                            self.has_recursion = True
                    self.generic_visit(node)

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

            visitor = ComplexityVisitor()
            visitor.visit(tree)
            
            # Determine complexity
            if visitor.has_recursion:
                cpu_profile["complexity"] = "O(n log n)"
            elif visitor.max_depth > 2:
                cpu_profile["complexity"] = f"O(n^{visitor.max_depth})"
            elif visitor.max_depth == 2:
                cpu_profile["complexity"] = "O(n^2)"
            elif visitor.max_depth == 1:
                cpu_profile["complexity"] = "O(n)"
            else:
                cpu_profile["complexity"] = "O(1)"
            
            # Adjust cores based on complexity
            cpu_profile["estimated_cores"] = max(
                cpu_profile["estimated_cores"],
                CPU_CONFIG["complexity_cores"][cpu_profile["complexity"]]
            )
            
            if visitor.has_recursion:
                cpu_profile["notes"] += "; Recursive patterns detected"
            
        except Exception as e:
            cpu_profile["notes"] += f"; AST analysis failed: {str(e)}"
        
        return cpu_profile

    def _estimate_bandwidth_usage(self, code):
        """Dynamic bandwidth usage estimation based on network patterns"""
        bandwidth_profile = {
            "network_calls_per_execution": 0,
            "data_transfer_mb": 0.0,
            "bandwidth_mbps": BANDWIDTH_CONFIG["base_mbps"]["minimal"],
            "transfer_type": "bulk",
            "notes": "Dynamic bandwidth analysis",
        }
        
        # Analyze imports for network libraries
        import_pattern = r"import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import"
        imports = re.findall(import_pattern, code)
        for imp in imports:
            for lib in [x for x in imp if x]:
                if lib in BANDWIDTH_CONFIG["library_impacts"]:
                    impact = BANDWIDTH_CONFIG["library_impacts"][lib]
                    bandwidth_profile["network_calls_per_execution"] += impact["calls"]
                    bandwidth_profile["data_transfer_mb"] += impact["calls"] * impact["mb_per_call"]
                    bandwidth_profile["notes"] += f"; Using {lib}"
        
        # Analyze web operations
        web_ops_count = 0
        for pattern in CODE_PATTERNS["web_operations"]:
            matches = re.findall(pattern, code)
            web_ops_count += len(matches)
        
        if web_ops_count > 0:
            bandwidth_profile["network_calls_per_execution"] += web_ops_count
            bandwidth_profile["data_transfer_mb"] += web_ops_count * BANDWIDTH_CONFIG["operation_costs"]["http_get"]
            bandwidth_profile["bandwidth_mbps"] = max(
                bandwidth_profile["bandwidth_mbps"],
                BANDWIDTH_CONFIG["base_mbps"]["web_api"]
            )
            bandwidth_profile["notes"] += f"; {web_ops_count} web operations detected"
        
        # Check for streaming patterns
        if "streaming" in code.lower() or "websocket" in code.lower():
            bandwidth_profile["transfer_type"] = "streaming"
            bandwidth_profile["bandwidth_mbps"] = max(
                bandwidth_profile["bandwidth_mbps"],
                BANDWIDTH_CONFIG["base_mbps"]["data_streaming"]
            )
            bandwidth_profile["notes"] += "; Streaming operations detected"
        
        return bandwidth_profile