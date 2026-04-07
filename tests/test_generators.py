"""
Unit tests for generators module - target 80%+ coverage.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from officeboy.generators.unit_tests import UnitTestGenerator, GenerationResult
from officeboy.generators.functional_tests import FunctionalTestGenerator, RobotSuite


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""
    
    def test_generation_result_creation(self):
        """Test creating GenerationResult."""
        result = GenerationResult(
            module_count=2,
            test_count=10,
            files_created=["test1.bas", "test2.bas"]
        )
        
        assert result.module_count == 2
        assert result.test_count == 10
        assert len(result.files_created) == 2


class TestUnitTestGenerator:
    """Tests for UnitTestGenerator."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        gen = UnitTestGenerator()
        
        assert gen is not None
    
    def test_generate_tests(self, tmp_path, access_application):
        """Test generating unit tests."""
        db_path = tmp_path / "test.accdb"
        output_dir = tmp_path / "tests"
        
        access_application.NewCurrentDatabase(str(db_path))
        
        gen = UnitTestGenerator()
        
        with patch('officeboy.generators.unit_tests.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            result = gen.generate(db_path, output_dir, addin_name="TestAddin")
            
            assert isinstance(result, GenerationResult)
            assert result.module_count >= 0


class TestFunctionalTestGenerator:
    """Tests for FunctionalTestGenerator."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        gen = FunctionalTestGenerator()
        
        assert gen is not None
    
    def test_generate_robot_tests(self, tmp_path, access_application):
        """Test generating Robot Framework tests."""
        db_path = tmp_path / "test.accdb"
        output_dir = tmp_path / "robot"
        
        access_application.NewCurrentDatabase(str(db_path))
        
        gen = FunctionalTestGenerator()
        
        with patch('officeboy.generators.functional_tests.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            result = gen.generate(db_path, output_dir, library="FlaUILibrary")
            
            assert isinstance(result, RobotSuite)
            assert result.spec_count >= 0


class TestRobotSuite:
    """Tests for RobotSuite."""
    
    def test_robot_suite_creation(self):
        """Test creating RobotSuite."""
        suite = RobotSuite(
            spec_count=3,
            form_count=3,
            test_case_count=15,
            files_created=["suite1.robot", "suite2.robot"]
        )
        
        assert suite.spec_count == 3
        assert suite.test_case_count == 15
        assert len(suite.files_created) == 2