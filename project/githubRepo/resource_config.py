"""Configuration for resource estimation parameters."""

# Memory configuration
MEMORY_CONFIG = {
    "base": {
        "min_mb": 10.0,  # Minimum base memory for any Python application
        "web_framework_mb": 100.0,  # Additional memory for web frameworks
        "data_processing_mb": 200.0,  # Additional memory for data processing libraries
        "ml_framework_mb": 500.0,  # Additional memory for ML frameworks
    },
    "scaling_factors": {
        "low": 1.2,  # Low data growth
        "medium": 1.5,  # Medium data growth
        "high": 2.0,  # High data growth
        "very_high": 4.0,  # Very high data growth (ML/Big Data)
    },
    "library_impacts": {
        "pandas": {"base": 50.0, "peak": 100.0, "scaling": "high"},
        "numpy": {"base": 30.0, "peak": 60.0, "scaling": "medium"},
        "tensorflow": {"base": 200.0, "peak": 500.0, "scaling": "very_high"},
        "torch": {"base": 200.0, "peak": 500.0, "scaling": "very_high"},
        "sklearn": {"base": 100.0, "peak": 200.0, "scaling": "high"},
        "flask": {"base": 50.0, "peak": 100.0, "scaling": "medium"},
        "django": {"base": 75.0, "peak": 150.0, "scaling": "medium"},
    }
}

# CPU configuration
CPU_CONFIG = {
    "base_cores": {
        "io_bound": 1.0,  # I/O-bound applications
        "cpu_bound": 2.0,  # CPU-bound applications
        "web_server": 2.0,  # Web server applications
        "data_processing": 4.0,  # Data processing applications
        "ml_training": 8.0,  # ML training applications
    },
    "parallelization_factors": {
        "none": 1.0,
        "low": 1.2,
        "medium": 1.5,
        "high": 2.0,
    },
    "complexity_cores": {
        "O(1)": 1.0,
        "O(log n)": 1.2,
        "O(n)": 1.5,
        "O(n log n)": 2.0,
        "O(n^2)": 2.5,
        "O(n^3)": 3.0,
    }
}

# Bandwidth configuration
BANDWIDTH_CONFIG = {
    "base_mbps": {
        "minimal": 0.1,  # Minimal network activity
        "web_api": 1.0,  # Web API calls
        "data_streaming": 5.0,  # Data streaming
        "file_transfer": 10.0,  # Large file transfers
    },
    "operation_costs": {
        "http_get": 0.1,  # GET request
        "http_post": 0.5,  # POST request
        "file_upload": 5.0,  # File upload
        "file_download": 5.0,  # File download
        "websocket": 1.0,  # WebSocket connection
        "database": 0.2,  # Database operation
    },
    "library_impacts": {
        "requests": {"calls": 1, "mb_per_call": 0.1},
        "urllib": {"calls": 1, "mb_per_call": 0.1},
        "aiohttp": {"calls": 2, "mb_per_call": 0.2},
        "httpx": {"calls": 1, "mb_per_call": 0.1},
        "websockets": {"calls": 5, "mb_per_call": 0.5},
        "flask": {"calls": 5, "mb_per_call": 0.2},
        "django": {"calls": 5, "mb_per_call": 0.3},
    }
}

# Code analysis patterns
CODE_PATTERNS = {
    "data_processing": [
        r"pd\.(read|merge|concat|groupby)",
        r"np\.(array|matrix|concatenate)",
        r"\.fit\(",
        r"\.predict\(",
    ],
    "web_operations": [
        r"@app\.route",
        r"@api\.",
        r"\.get\(",
        r"\.post\(",
    ],
    "file_operations": [
        r"\.read\(",
        r"\.write\(",
        r"open\(",
        r"with\s+open",
    ],
    "parallel_processing": [
        r"multiprocessing\.",
        r"concurrent\.",
        r"threading\.",
        r"asyncio\.",
    ]
} 