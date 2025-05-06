import os
from multiprocessing.dummy import Pool

class ResourceProfiler:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.profiles = {}

    def profile_repository(self, repo_path, repo_structure):
        total_profile = {
            "memory": {
                "estimated_base_mb": 0.0,
                "estimated_peak_mb": 0.0,
                "scaling_factor": 1.0,
            },
            "cpu": {
                "estimated_cores": 0.0,
                "parallelization_potential": "low",
            },
            "bandwidth": {
                "network_calls_per_execution": 0,
                "data_transfer_mb": 0.0,
                "bandwidth_mbps": 0.0,
                "transfer_type": "bulk",
            },
            "files_analyzed": 0,
            "component_profiles": {},
            "sources_used": {"llm": 0, "static": 0},
        }
        
        python_files = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py') and 'test' not in file and file != 'setup.py':
                    python_files.append(os.path.join(root, file))
        
        if not python_files:
            total_profile["recommendations"] = self._generate_recommendations(total_profile)
            total_profile["network_summary"] = self.summarize_network_usage(total_profile)
            return total_profile
        
        with Pool() as pool:
            file_profiles = pool.starmap(
                self.analyzer.analyze_file,
                [(f, repo_structure) for f in python_files]
            )
        
        for file_path, file_profile in zip(python_files, file_profiles):
            if isinstance(file_profile, dict) and "error" not in file_profile:
                relative_path = os.path.relpath(file_path, repo_path)
                total_profile["files_analyzed"] += 1
                total_profile["component_profiles"][relative_path] = file_profile
                source = file_profile.get("source", "static")
                if source in total_profile["sources_used"]:
                    total_profile["sources_used"][source] += 1
                try:
                    self._update_aggregate_profile(total_profile, file_profile)
                except Exception as e:
                    print(f"Failed to update aggregate profile for {relative_path}: {e}")
        
        total_profile["recommendations"] = self._generate_recommendations(total_profile)
        total_profile["network_summary"] = self.summarize_network_usage(total_profile)
        
        return total_profile

    def _update_aggregate_profile(self, total_profile, file_profile):
        memory = file_profile.get("memory", {})
        total_profile["memory"]["estimated_base_mb"] += memory.get("base_mb", 0.0)
        total_profile["memory"]["estimated_peak_mb"] += memory.get("peak_mb", 0.0)
        total_profile["memory"]["scaling_factor"] = max(
            total_profile["memory"]["scaling_factor"],
            memory.get("scaling_factor", 1.0)
        )
        
        cpu = file_profile.get("cpu", {})
        total_profile["cpu"]["estimated_cores"] += cpu.get("estimated_cores", 0.0)
        if cpu.get("parallelization_potential", "low") == "high":
            total_profile["cpu"]["parallelization_potential"] = "high"
        elif cpu.get("parallelization_potential", "low") == "medium":
            total_profile["cpu"]["parallelization_potential"] = max(
                total_profile["cpu"]["parallelization_potential"], "medium"
            )
        
        bandwidth = file_profile.get("bandwidth", {})
        total_profile["bandwidth"]["network_calls_per_execution"] += bandwidth.get("network_calls_per_execution", 0)
        total_profile["bandwidth"]["data_transfer_mb"] += bandwidth.get("data_transfer_mb", 0.0)
        total_profile["bandwidth"]["bandwidth_mbps"] += bandwidth.get("bandwidth_mbps", 0.0)
        if bandwidth.get("transfer_type", "bulk") == "streaming":
            total_profile["bandwidth"]["transfer_type"] = "streaming"

    def summarize_network_usage(self, total_profile):
        network_libs = set()
        total_calls = 0
        total_data_mb = 0
        for file_path, profile in total_profile["component_profiles"].items():
            bandwidth = profile.get("bandwidth", {})
            notes = bandwidth.get("notes", "")
            for lib in self.analyzer.network_libs:
                if lib in notes:
                    network_libs.add(lib)
            total_calls += bandwidth.get("network_calls_per_execution", 0)
            total_data_mb += bandwidth.get("data_transfer_mb", 0.0)
        return {
            "network_libraries_used": list(network_libs),
            "total_network_calls": total_calls,
            "estimated_data_transfer_mb": total_data_mb,
            "estimated_bandwidth_mbps": total_data_mb / 10,
        }

    def _generate_recommendations(self, profile):
        recommendations = {
            "memory": {},
            "cpu": {},
            "bandwidth": {},
            "scaling": {},
        }
        
        base_memory = profile["memory"]["estimated_base_mb"]
        peak_memory = profile["memory"]["estimated_peak_mb"]
        scaling_factor = profile["memory"]["scaling_factor"]
        
        recommendations["memory"]["min_allocation"] = f"{max(0, base_memory)}MB"
        recommendations["memory"]["recommended_allocation"] = f"{max(0, base_memory + peak_memory)}MB"
        recommendations["memory"]["scaling_strategy"] = (
            "Static" if scaling_factor < 1.2 else 
            "Linear scaling with data size" if scaling_factor < 1.8 else
            "Exponential scaling with data size"
        )
        
        estimated_cores = profile["cpu"]["estimated_cores"]
        parallelization = profile["cpu"]["parallelization_potential"]
        
        recommendations["cpu"]["min_cores"] = 1
        recommendations["cpu"]["recommended_cores"] = max(1, round(estimated_cores))
        recommendations["cpu"]["core_scaling"] = (
            "Fixed allocation" if parallelization == "low" else
            "Scale with workload"
        )
        
        baseline_kbps = profile["bandwidth"]["bandwidth_mbps"] * 8 * 1000 / 10
        peak_mbps = profile["bandwidth"]["bandwidth_mbps"]
        
        recommendations["bandwidth"]["baseline_requirement"] = f"{baseline_kbps}Kbps"
        recommendations["bandwidth"]["peak_requirement"] = f"{peak_mbps}Mbps"
        
        memory_scaling_needed = scaling_factor > 1.5
        cpu_scaling_needed = estimated_cores > 2
        bandwidth_scaling_needed = profile["bandwidth"]["transfer_type"] == "streaming"
        
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