import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from Thesis.implem.Analyzing_file_codes import StaticFileAnalyzer, DynamicAnalyzer, LLMAnalyzer, CodeStructureAnalyzer, merge_sort

class TestStaticFileAnalyzer:
    @pytest.fixture
    def sample_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("def add(a, b):\n    # Add two numbers\n    return a + b\n")
        yield f.name
        os.unlink(f.name)
    
    def test_initialization(self, sample_file):
        """Test correct initialization of StaticFileAnalyzer."""
        analyzer = StaticFileAnalyzer(sample_file)
        assert analyzer.file_path.endswith(sample_file)
        assert analyzer.file_size > 0
        assert analyzer.loc == 3
        assert analyzer.overhead > 0
        
    def test_file_not_found(self):
        """Test FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            StaticFileAnalyzer("nonexistent_file.py")
    
    def test_get_file_size(self, sample_file):
        """Test file size calculation."""
        analyzer = StaticFileAnalyzer(sample_file)
        assert analyzer.get_file_size() == os.path.getsize(sample_file)
    
    def test_line_of_codes(self, sample_file):
        """Test line counting."""
        analyzer = StaticFileAnalyzer(sample_file)
        assert analyzer.line_of_codes() == 3
    
    def test_calculate_overhead_per_line(self, sample_file):
        """Test overhead calculation."""
        analyzer = StaticFileAnalyzer(sample_file)
        assert analyzer.calculate_overhead_per_line() > 0
    
    def test_comment_ratio(self, sample_file):
        """Test comment ratio calculation."""
        analyzer = StaticFileAnalyzer(sample_file)
        assert analyzer.comment_ratio() == 1/3 
    
    def test_complexity_analysis(self, sample_file):
        """Test complexity metrics calculation."""
        analyzer = StaticFileAnalyzer(sample_file)
        metrics = analyzer.complexity_metrics
        assert "cyclomatic_complexity" in metrics
        assert "halstead_metrics" in metrics
        assert "maintainability_index" in metrics
    
    def test_estimate_memory_usage(self, sample_file):
        """Test memory usage estimation."""
        analyzer = StaticFileAnalyzer(sample_file)
        assert analyzer.estimate_memory_usage() > 0
    
    def test_analyze(self, sample_file, capsys):
        """Test the analyze method output."""
        analyzer = StaticFileAnalyzer(sample_file)
        result = analyzer.analyze()
        captured = capsys.readouterr()
        
        assert "Analyzing" in captured.out
        assert "File Size" in captured.out
        assert "Lines of Code" in captured.out
        
        assert result["file_path"].endswith(sample_file)
        assert result["file_size"] > 0
        assert result["lines_of_code"] == 3
        assert result["overhead_per_line"] > 0
        assert result["memory_usage"] > 0
        assert "complexity_metrics" in result

class TestDynamicAnalyzer:
    @pytest.fixture
    def mock_static_analyzer(self):
        """Create a mock StaticFileAnalyzer."""
        mock = MagicMock(spec=StaticFileAnalyzer)
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py')
        temp_file.write("def merge_sort(arr):\n    return sorted(arr)")
        temp_file.close()
        mock.file_path = temp_file.name
        return mock
    
    @pytest.fixture(autouse=True)
    def cleanup_globals(self):
        """Clean up global variables after each test."""
        yield
        if 'merge_sort' in globals():
            del globals()['merge_sort']
    
    def test_initialization(self, mock_static_analyzer):
        """Test correct initialization of DynamicAnalyzer."""
        test_array = [3, 1, 4, 1, 5]
        analyzer = DynamicAnalyzer(test_array, mock_static_analyzer)
        assert analyzer.array == test_array
        assert analyzer.static_file_analyzer == mock_static_analyzer
    
    def test_run_with_memory_profile(self, mock_static_analyzer):
        """Test memory profiling."""
        test_array = [3, 1, 4, 1, 5]
        analyzer = DynamicAnalyzer(test_array, mock_static_analyzer)
        
        # Mock the merge_sort global to avoid exec
        global merge_sort
        merge_sort = lambda arr: sorted(arr)
        
        memory_used = analyzer.run_with_memory_profile()
        assert memory_used > 0
        assert analyzer.sorted_array == test_array  
    
    @patch('file_analyzer.memory_usage')
    def test_memory_usage_called(self, mock_memory_usage, mock_static_analyzer):
        """Test that memory_usage is called correctly."""
        mock_memory_usage.return_value = 100.0
        
        test_array = [3, 1, 4, 1, 5]
        analyzer = DynamicAnalyzer(test_array, mock_static_analyzer)
        
      
        global merge_sort
        merge_sort = lambda arr: sorted(arr)
        
        result = analyzer.run_with_memory_profile()
        mock_memory_usage.assert_called_once()
        assert result == 100.0

class TestLLMAnalyzer:
    @pytest.fixture
    def mock_file_analyzer(self):
        """Create a mock StaticFileAnalyzer."""
        mock = MagicMock(spec=StaticFileAnalyzer)
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py')
        temp_file.write("def add(a, b):\n    return a + b\n")
        temp_file.close()
        mock.file_path = temp_file.name
        return mock
    
    @patch.dict(os.environ, {"api_keys": "fake_api_key"})
    @patch('file_analyzer.anthropic.Anthropic')
    def test_initialization(self, mock_anthropic, mock_file_analyzer):
        """Test correct initialization of LLMAnalyzer."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        analyzer = LLMAnalyzer(mock_file_analyzer)
        assert analyzer.api_key == "fake_api_key"
        assert analyzer.client == mock_client
        assert analyzer.model == "claude-3-7-sonnet-20250219"
        assert analyzer.file_analyzer == mock_file_analyzer
    
    @patch.dict(os.environ, {"api_keys": "fake_api_key"})
    @patch('file_analyzer.anthropic.Anthropic')
    def test_analyze_code_success(self, mock_anthropic, mock_file_analyzer):
        """Test successful code analysis."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Analysis result"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        analyzer = LLMAnalyzer(mock_file_analyzer)
        result = analyzer.analyze_code()
        
        mock_client.messages.create.assert_called_once()
        assert result == "Analysis result"
    
    @patch.dict(os.environ, {"api_keys": "fake_api_key"})
    @patch('file_analyzer.anthropic.Anthropic')
    def test_analyze_code_error(self, mock_anthropic, mock_file_analyzer):
        """Test error handling in code analysis."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_anthropic.return_value = mock_client
        
        analyzer = LLMAnalyzer(mock_file_analyzer)
        result = analyzer.analyze_code()
        
        assert "Error analyzing" in result

class TestCodeStructureAnalyzer:
    def test_initialization(self):
        """Test correct initialization of CodeStructureAnalyzer."""
        code = "def add(a, b): return a + b"
        analyzer = CodeStructureAnalyzer(code)
        assert analyzer.code == code
        assert hasattr(analyzer, 'tree')
        assert isinstance(analyzer.analysis, dict)
    
    def test_analyze_variables(self):
        """Test variable analysis."""
        code = """
        x = 1
        y = "hello"
        z = [1, 2, 3]
        """
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()
        
        assert "x" in result["variables"]
        assert "y" in result["variables"]
        assert "z" in result["variables"]
        assert "Constant" in result["variables"]["x"]
        assert "Constant" in result["variables"]["y"]
        assert "List" in result["variables"]["z"]
    
    def test_analyze_functions(self):
        """Test function analysis."""
        code = """
        def add(a, b):
            return a + b
            
        def subtract(a, b) -> int:
            return a - b
        """
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()
        
        assert "add" in result["functions"]
        assert "subtract" in result["functions"]
        assert result["functions"]["add"]["params"] == ["a", "b"]
        assert result["functions"]["subtract"]["params"] == ["a", "b"]
        assert result["functions"]["subtract"]["returns"] == "int"
    
    def test_analyze_imports(self):
        """Test import analysis."""
        code = """
        import os
        import sys as system
        from math import sqrt
        """
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()
        
        assert "os" in result["imports"]
        assert "sys" in result["imports"]
        assert "math.sqrt" in result["imports"]
    
    def test_analyze_naming_conventions(self):
        """Test naming convention analysis."""
        code = """
        my_stack = []
        search_tree = {}
        def dfs_algorithm(graph):
            pass
        """
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()
        
        assert "my_stack" in result["naming_conventions"]["data_structures"]
        assert "search_tree" in result["naming_conventions"]["data_structures"]
        assert "dfs_algorithm" in result["naming_conventions"]["algorithms"]
    
    def test_analyze_control_flow(self):
        """Test control flow analysis."""
        code = """
        for i in range(10):
            if i % 2 == 0:
                print(i)
                
        while True:
            break
        """
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()
        
        assert result["control_flow"]["loops"] == 2 
        assert result["control_flow"]["conditionals"] == 1 