import pytest
import os
import tempfile
import shutil
from unittest.mock import patch


from implem.Analyzing_file_codes import DynamicAnalyzer, LLMAnalyzer, StaticFileAnalyzer
from implem.Read_git_files import RepoMemoryAnalyzer


class TestRepoMemoryAnalyzer:
    @pytest.fixture
    def analyzer(self):
        with patch('anthropic.Anthropic') as mock_anthropic:
            with patch('os.getenv', return_value='fake_api_key'):
                analyzer = RepoMemoryAnalyzer()
                yield analyzer

    @pytest.fixture
    def temp_repo(self):
    
        temp_dir = tempfile.mkdtemp()
        
        os.makedirs(os.path.join(temp_dir, "src"))
        with open(os.path.join(temp_dir, "src", "test1.py"), "w") as f:
            f.write("def test_function():\n    return 'test'")
            
        with open(os.path.join(temp_dir, "src", "test2.py"), "w") as f:
            f.write("class TestClass:\n    pass")
            
        with open(os.path.join(temp_dir, "README.md"), "w") as f:
            f.write("# Test Repository")
            
        yield temp_dir
        
        shutil.rmtree(temp_dir)

    def test_init(self, analyzer):
        assert analyzer.client is not None
        assert analyzer.repo_path is None
        assert analyzer.code_files == {}

    @patch('builtins.input', return_value='https://github.com/user/repo.git')
    @patch('git.Repo.clone_from')
    @patch('tempfile.mkdtemp', return_value='/tmp/fake_dir')
    def test_clone_repo_from_input_success(self, mock_mkdtemp, mock_clone, mock_input, analyzer):
        analyzer.clone_repo_from_input()
        
        mock_input.assert_called_once()
        mock_mkdtemp.assert_called_once()
        mock_clone.assert_called_once_with('https://github.com/user/repo.git', '/tmp/fake_dir')
        assert analyzer.repo_path == '/tmp/fake_dir'

    @patch('builtins.input', return_value='https://github.com/user/repo')
    def test_clone_repo_from_input_invalid_url(self, mock_input, analyzer):
        with pytest.raises(ValueError, match="Invalid Git URL. Must end with .git"):
            analyzer.clone_repo_from_input()

    def test_fetch_py_files(self, analyzer, temp_repo):
        analyzer.repo_path = temp_repo
        analyzer.fetch_py_files()
        
        assert len(analyzer.code_files) == 2
        file_paths = list(analyzer.code_files.values())
        assert any("test1.py" in path for path in file_paths)
        assert any("test2.py" in path for path in file_paths)
        assert not any("README.md" in path for path in file_paths)

    @patch.object(RepoMemoryAnalyzer, 'clone_repo_from_input')
    @patch.object(RepoMemoryAnalyzer, 'fetch_py_files')
    @patch.object(RepoMemoryAnalyzer, 'extract_llm_memory_estimate')
    @patch.object(StaticFileAnalyzer, 'analyze')
    @patch.object(DynamicAnalyzer, 'run_with_memory_profile')
    @patch.object(LLMAnalyzer, 'analyze_code')
    def test_analyze_repo(self, mock_analyze_code, mock_run_with_memory, mock_static_analyze, 
                          mock_extract_mem, mock_fetch, mock_clone, analyzer):
       
        analyzer.code_files = {'/tmp/test1.py': '/tmp/test1.py', '/tmp/test2.py': '/tmp/test2.py'}
        mock_static_analyze.return_value = {"memory_usage": 1000}
        mock_run_with_memory.return_value = [0.5] 
        mock_analyze_code.return_value = "Peak memory: 10 MB"
        mock_extract_mem.return_value = 10 * 1024 * 1024 
        
        
        with patch('builtins.print') as mock_print:
            analyzer.analyze_repo()
        
        
        mock_clone.assert_called_once()
        mock_fetch.assert_called_once()
        assert mock_static_analyze.call_count == 2
        assert mock_run_with_memory.call_count == 2
        assert mock_analyze_code.call_count == 2
        assert mock_extract_mem.call_count == 2
        
        
        mock_print.assert_any_call("❯ Total Static Memory Estimate: 2,000 bytes")
        mock_print.assert_any_call("❯ Peak Dynamic Memory Estimate: 524,288 bytes")
        mock_print.assert_any_call("❯ LLM Estimated Peak Memory: 10,485,760 bytes")

    def test_extract_llm_memory_estimate(self, analyzer):
       
        assert analyzer.extract_llm_memory_estimate("Peak memory: 500 KB") == 512000
        
       
        assert analyzer.extract_llm_memory_estimate("Uses about 2.5 MB of memory") == 2621440
        
        
        assert analyzer.extract_llm_memory_estimate("Could use up to 1 GB") == 1073741824
        
        assert analyzer.extract_llm_memory_estimate("Needs 10 kb") == 10240
        
        assert analyzer.extract_llm_memory_estimate("No memory info here") == 0

    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_clone_repo_keyboard_interrupt(self, mock_input, analyzer):
        with pytest.raises(KeyboardInterrupt):
            analyzer.clone_repo_from_input()

    @patch.object(RepoMemoryAnalyzer, 'clone_repo_from_input')
    @patch.object(RepoMemoryAnalyzer, 'fetch_py_files')
    def test_analyze_repo_with_errors(self, mock_fetch, mock_clone, analyzer):
        # Setup
        analyzer.code_files = {'/tmp/test1.py': '/tmp/test1.py'}
        
        with patch.object(StaticFileAnalyzer, 'analyze', side_effect=Exception("Static analysis error")):
            with patch('builtins.print') as mock_print:
                analyzer.analyze_repo()
                
                mock_print.assert_any_call("[Static] Skipped /tmp/test1.py due to error: Static analysis error")
                
              
                mock_print.assert_any_call("❯ Total Static Memory Estimate: 0 bytes")
                mock_print.assert_any_call("❯ Peak Dynamic Memory Estimate: 0 bytes")
                mock_print.assert_any_call("❯ LLM Estimated Peak Memory: 0 bytes")