import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path to resolve imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Mock the InteractiveAgent import that's causing issues
sys.modules["interactive"] = Mock()

from minisweagent.agents.compound_agent import AgentCoordinatoor, SupervisorAgent, ExecutorAgent, AgentFactory, Utils
from minisweagent import Model, Environment

class TestRecursiveBehavior(unittest.TestCase):
    
    def setUp(self):
        # Create mocks for dependencies
        self.mock_model = Mock(spec=Model)
        self.mock_env = Mock(spec=Environment)
        
        self.mock_env.get_template_vars.return_value = {}
        self.mock_model.get_template_vars.return_value = {}
        
        self.coordinator = AgentCoordinatoor(model=self.mock_model, env=self.mock_env)
        
    def test_bottom_up_completion(self):
        """Test that executors completing triggers supervisor chain"""
        # Simple 2-level task structure
        task_desc = {
            "root": {"id": "main", "type": "planner"},
            "level_1": [
                {"id": "sub1", "supervisor": "main", "type": "supervisor"},
            ],
            "level_2": [
                {"id": "exec1", "supervisor": "sub1", "type": "executor"},
                {"id": "exec2", "supervisor": "sub1", "type": "executor"},
            ]
        }
        
        self.coordinator.supervisor_map = Utils.build_map(task_desc)
        self.coordinator.child_count_map = Utils.build_child_count_map(task_desc)
        
        # Mock AgentFactory to return mock supervisors
        with patch.object(AgentFactory, 'generate_supervisor') as mock_supervisor_factory:
            mock_supervisor = Mock(spec=SupervisorAgent)
            mock_supervisor.my_supervisor = "main"
            mock_supervisor.analyze_results.return_value = ("Failed", "Analysis failed")
            mock_supervisor_factory.return_value = mock_supervisor
            
            # Simulate both executors completing
            self.coordinator.on_child_completed("sub1", "result1")
            self.assertEqual(len(self.coordinator.completed_agents["sub1"]), 1)
            
            self.coordinator.on_child_completed("sub1", "result2")
            self.assertEqual(len(self.coordinator.completed_agents["sub1"]), 2)
            
            # Should trigger supervisor creation and analysis
            self.assertIn("sub1", self.coordinator.active_supervisors)
            mock_supervisor_factory.assert_called_once()
        
    def test_simple_two_level_recursion(self):
        """Test basic recursion: root -> supervisor -> executor"""
        task_desc = {
            "root": {"id": "main", "description": "Main Task"},
            "level_1": [
                {"id": "sub1", "description": "Subtask 1", "supervisor": "main"}
            ],
            "level_2": [
                {"id": "exec1", "description": "Execute 1", "supervisor": "sub1"},
                {"id": "exec2", "description": "Execute 2", "supervisor": "sub1"}
            ]
        }
        
        self.coordinator.supervisor_map = Utils.build_map(task_desc)
        self.coordinator.child_count_map = Utils.build_child_count_map(task_desc)
        
        # Mock AgentFactory to return mock supervisors
        with patch.object(AgentFactory, 'generate_supervisor') as mock_supervisor_factory:
            mock_supervisor = Mock(spec=SupervisorAgent)
            mock_supervisor.my_supervisor = "main"
            mock_supervisor.analyze_results.return_value = ("Failed", "Analysis failed")
            mock_supervisor_factory.return_value = mock_supervisor
            
            # Simulate executor completions
            self.coordinator.on_child_completed("sub1", "Result from exec1")
            self.assertEqual(len(self.coordinator.completed_agents["sub1"]), 1)
            
            self.coordinator.on_child_completed("sub1", "Result from exec2")
            self.assertEqual(len(self.coordinator.completed_agents["sub1"]), 2)
            
            # Verify supervisor was created after all children completed
            self.assertIn("sub1", self.coordinator.active_supervisors)
            mock_supervisor_factory.assert_called_once()
    
    def test_multi_branch_recursion(self):
        """Test recursion with multiple branches at same level"""
        task_desc = {
            "root": {"id": "main", "description": "Main Task"},
            "level_1": [
                {"id": "branch1", "description": "Branch 1", "supervisor": "main"},
                {"id": "branch2", "description": "Branch 2", "supervisor": "main"}
            ],
            "level_2": [
                {"id": "exec1", "description": "Exec 1", "supervisor": "branch1"},
                {"id": "exec2", "description": "Exec 2", "supervisor": "branch2"}
            ]
        }
        
        self.coordinator.supervisor_map = Utils.build_map(task_desc)
        self.coordinator.child_count_map = Utils.build_child_count_map(task_desc)
        
        # Mock AgentFactory to avoid real supervisor creation
        with patch.object(AgentFactory, 'generate_supervisor') as mock_factory:
            mock_supervisor = Mock(spec=SupervisorAgent)
            mock_supervisor.my_supervisor = None
            mock_supervisor.analyze_results.return_value = ("Failed", "Analysis failed")
            mock_factory.return_value = mock_supervisor
            
            # Test that different branches are handled independently
            self.coordinator.on_child_completed("branch1", "Result 1")
            self.coordinator.on_child_completed("branch2", "Result 2")
            
            # Both branches should have their results tracked separately
            self.assertIn("branch1", self.coordinator.completed_agents)
            self.assertIn("branch2", self.coordinator.completed_agents)
            
            # Each branch should have exactly one result
            self.assertEqual(len(self.coordinator.completed_agents["branch1"]), 1)
            self.assertEqual(len(self.coordinator.completed_agents["branch2"]), 1)

    def test_bottom_up_completion_basic(self):
        """Test that executors completing triggers supervisor chain"""
        # Simple 2-level task structure
        task_desc = {
            "root": {"id": "main", "type": "planner"},
            "level_1": [
                {"id": "sub1", "supervisor": "main", "type": "supervisor"},
            ],
            "level_2": [
                {"id": "exec1", "supervisor": "sub1", "type": "executor"},
                {"id": "exec2", "supervisor": "sub1", "type": "executor"},
            ]
        }
        
        self.coordinator.supervisor_map = Utils.build_map(task_desc)
        self.coordinator.child_count_map = Utils.build_child_count_map(task_desc)
        
        # Mock AgentFactory to return mock supervisors
        with patch.object(AgentFactory, 'generate_supervisor') as mock_supervisor_factory:
            mock_supervisor = Mock(spec=SupervisorAgent)
            mock_supervisor.my_supervisor = "main"
            mock_supervisor.analyze_results.return_value = ("Failed", "Analysis failed")
            mock_supervisor_factory.return_value = mock_supervisor
            
            # Simulate first executor completing
            self.coordinator.on_child_completed("sub1", "result1")
            self.assertEqual(len(self.coordinator.completed_agents["sub1"]), 1)
            # Supervisor not created yet
            self.assertNotIn("sub1", self.coordinator.active_supervisors)
            
            # Simulate second executor completing - should trigger supervisor
            self.coordinator.on_child_completed("sub1", "result2")
            self.assertEqual(len(self.coordinator.completed_agents["sub1"]), 2)
            # Should have created supervisor
            self.assertIn("sub1", self.coordinator.active_supervisors)
            mock_supervisor_factory.assert_called_once()

if __name__ == '__main__':
    unittest.main()