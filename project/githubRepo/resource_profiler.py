import os


class ResourceProfiler:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.profiles = {}
    
    def profile_repository(self, repo_path):
        """Create a complete resource profile for a repository"""
        total_profile = {
            "memory": {
                "estimated_base_mb": 50,
                "estimated_peak_mb": 50,
                "scalability_factor": 1.0,
            },
            "cpu": {
                "estimated_cores": 1,
                "parallelization_potential": "low",
                "cpu_bound_score": 0,
            },
            "bandwidth": {
                "estimated_baseline_kbps": 0,
                "estimated_peak_mbps": 0,
                "data_transfer_frequency": "low",
            },
            "files_analyzed": 0,
            "component_profiles": {},
        }
        
        # Analyze Python files
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    # Skip test files and setup files
                    if 'test' in file or file == 'setup.py':
                        continue
                        
                    file_profile = self.analyzer.analyze_file(file_path)
                    if isinstance(file_profile, str):
                        import json
                        try:
                            file_profile = json.loads(file_profile)
                        except Exception as e:
                            print(f"Skipping {file} due to JSON parsing error: {e}")
                            continue

                    if not isinstance(file_profile, dict) or "error" in file_profile:
                        print(f"Skipping {file} due to analysis error: {file_profile.get('error', 'Unknown error')}")
                        continue
                    
                    total_profile["files_analyzed"] += 1
                    total_profile["component_profiles"][relative_path] = file_profile
                    
                    try:
                        self._update_aggregate_profile(total_profile, file_profile)
                    except Exception as e:
                        print(f"Failed to update aggregate profile for {relative_path}: {e}")

        
        # Generate recommendations
        total_profile["recommendations"] = self._generate_recommendations(total_profile)
        
        return total_profile
    
    def _update_aggregate_profile(self, total_profile, file_profile):
        """Update the aggregate profile with file-specific metrics"""
        
        if "memory" in file_profile:
            mem_intensive_libs = file_profile["memory"].get("memory_intensive_libs", [])
            large_structs = file_profile["memory"].get("large_data_structures", 0)
        else:
            print(f"File profile missing memo data for {file_profile}")
            mem_intensive_libs = []
            large_structs = 0

        
        if "pandas" in mem_intensive_libs or "numpy" in mem_intensive_libs:
            total_profile["memory"]["estimated_base_mb"] += 100
            total_profile["memory"]["scalability_factor"] = max(total_profile["memory"]["scalability_factor"], 1.5)
        
        if "tensorflow" in mem_intensive_libs or "torch" in mem_intensive_libs:
            total_profile["memory"]["estimated_base_mb"] += 500
            total_profile["memory"]["scalability_factor"] = max(
                total_profile["memory"]["scalability_factor"], 2.0
            )
        
        
        total_profile["memory"]["estimated_peak_mb"] += large_structs * 50
        
        # CPU
        if "cpu" in file_profile:
            if file_profile["cpu"].get("nested_loops", 0) > 1:
                total_profile["cpu"]["cpu_bound_score"] += file_profile["cpu"]["nested_loops"]

            if file_profile["cpu"].get("recursive_calls", 0) > 0:
                total_profile["cpu"]["cpu_bound_score"] += file_profile["cpu"]["recursive_calls"] * 2
        else:
            print(f"File profile missing CPU data for {file_profile}")

        
        # Adjust CPU requirements
        if total_profile["cpu"]["cpu_bound_score"] > 5:
            total_profile["cpu"]["estimated_cores"] = 2
            total_profile["cpu"]["parallelization_potential"] = "medium"
        
        if total_profile["cpu"]["cpu_bound_score"] > 10:
            total_profile["cpu"]["estimated_cores"] = 4
            total_profile["cpu"]["parallelization_potential"] = "high"
        
        # Bandwidth estimates
        network_calls = file_profile["bandwidth"]["network_calls"]
        network_libs = file_profile["bandwidth"]["network_libraries"]
        
        if network_calls > 0:
            total_profile["bandwidth"]["estimated_baseline_kbps"] += network_calls * 10
            total_profile["bandwidth"]["estimated_peak_mbps"] += network_calls * 0.5
        
        if network_libs:
            total_profile["bandwidth"]["data_transfer_frequency"] = "medium"
            if network_calls > 10:
                total_profile["bandwidth"]["data_transfer_frequency"] = "high"
    
    def _generate_recommendations(self, profile):
        """Generate resource allocation recommendations"""
        recommendations = {
            "memory": {},
            "cpu": {},
            "bandwidth": {},
            "scaling": {},
        }
        
        # Memory recommendations
        base_memory = profile["memory"]["estimated_base_mb"]
        peak_memory = profile["memory"]["estimated_peak_mb"]
        scaling_factor = profile["memory"]["scalability_factor"]
        
        recommendations["memory"]["min_allocation"] = f"{max(128, base_memory)}MB"
        recommendations["memory"]["recommended_allocation"] = f"{max(256, base_memory + peak_memory)}MB"
        recommendations["memory"]["scaling_strategy"] = (
            "Static" if scaling_factor < 1.2 else 
            "Linear scaling with data size" if scaling_factor < 1.8 else
            "Exponential scaling with data size"
        )
        
        # CPU recommendations
        cpu_bound = profile["cpu"]["cpu_bound_score"] > 5
        estimated_cores = profile["cpu"]["estimated_cores"]
        
        recommendations["cpu"]["min_cores"] = 1
        recommendations["cpu"]["recommended_cores"] = estimated_cores
        recommendations["cpu"]["core_scaling"] = (
            "Fixed allocation" if not cpu_bound else
            "Scale with workload"
        )
        
        # Bandwidth recommendations
        baseline_kbps = profile["bandwidth"]["estimated_baseline_kbps"]
        peak_mbps = profile["bandwidth"]["estimated_peak_mbps"]
        
        recommendations["bandwidth"]["baseline_requirement"] = f"{baseline_kbps}Kbps"
        recommendations["bandwidth"]["peak_requirement"] = f"{peak_mbps}Mbps"
        
        # Overall scaling recommendation
        cpu_scaling_needed = cpu_bound
        memory_scaling_needed = scaling_factor > 1.5
        bandwidth_scaling_needed = profile["bandwidth"]["data_transfer_frequency"] != "low"
        
        scaling_dimensions = []
        if memory_scaling_needed:
            scaling_dimensions.append("memory")
        if cpu_scaling_needed:
            scaling_dimensions.append("cpu")
        if bandwidth_scaling_needed:
            scaling_dimensions.append("bandwidth")
        
        recommendations["scaling"]["priority_dimension"] = (
            scaling_dimensions[0] if scaling_dimensions else "none"
        )
        recommendations["scaling"]["scaling_trigger"] = (
            "Data size" if "memory" in scaling_dimensions else
            "Request volume" if "bandwidth" in scaling_dimensions else
            "Computation complexity" if "cpu" in scaling_dimensions else
            "None required"
        )
        
        return recommendations