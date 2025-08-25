import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path to resolve imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from minisweagent import Model, Environment
from minisweagent.agents.default import DefaultAgent

# Mock the InteractiveAgent import that's causing issues
sys.modules["interactive"] = Mock()


# Create a mock AgentCoordinatoor that inherits from DefaultAgent
class MockAgentCoordinatoor(DefaultAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.completed_agents = {}
        self.supervisor_config = {}
        self.active_supervisors = {}

    def parse_task_structure(self) -> dict:
        """Convert the query to the supervisor -> supervisor_config dictionary"""
        task_desc = self.query()
        for level_key in task_desc:
            if level_key.startswith("level_"):
                for item in task_desc[level_key]:
                    if "supervisor" in item:
                        supervisor_id = item["supervisor"]
                        if supervisor_id not in self.supervisor_config:
                            self.supervisor_config[supervisor_id] = []
                        self.supervisor_config[supervisor_id].append(item)
        return self.supervisor_config


class TestAgentCoordinatoor:
    @pytest.fixture
    def coordinator(self):
        mock_model = Mock(spec=Model)
        mock_env = Mock(spec=Environment)

        mock_env.get_template_vars.return_value = {}
        mock_model.get_template_vars.return_value = {}

        return MockAgentCoordinatoor(model=mock_model, env=mock_env)

    def test_parse_task_structure(self, coordinator):
        # Mock the query method to return a structured task
        mock_task_desc = {
            "root": {"id": "vuln_assessment", "description": "Vulnerability Assessment", "type": "planner"},
            "level_1": [
                {"id": "recon", "description": "Reconnaissance", "supervisor": "vuln_assessment", "type": "supervisor"},
                {
                    "id": "web_testing",
                    "description": "Web Testing",
                    "supervisor": "vuln_assessment",
                    "type": "supervisor",
                },
            ],
            "level_2": [
                {"id": "domain_enum", "description": "Domain enumeration", "supervisor": "recon", "type": "executor"},
                {"id": "port_scan", "description": "Port scanning", "supervisor": "recon", "type": "executor"},
            ],
        }

        with patch.object(coordinator, "query", return_value=mock_task_desc):
            result = coordinator.parse_task_structure()

        # Should return the supervisor_config dictionary
        assert isinstance(result, dict)

        # Check that supervisors were parsed correctly
        assert "vuln_assessment" in result
        assert "recon" in result

        # Check that items were assigned to correct supervisors
        assert len(result["vuln_assessment"]) == 2
        assert len(result["recon"]) == 2

        # Verify content
        vuln_items = result["vuln_assessment"]
        assert any(item["id"] == "recon" for item in vuln_items)
        assert any(item["id"] == "web_testing" for item in vuln_items)

        recon_items = result["recon"]
        assert any(item["id"] == "domain_enum" for item in recon_items)
        assert any(item["id"] == "port_scan" for item in recon_items)


class TestUtils:
    def test_build_map(self):
        from minisweagent.agents.compound_agent import Utils
        
        # Test data matching the example in compound_agent.py
        task_desc = {
            "root": {"id": "vuln_assessment", "description": "Vulnerability Assessment", "type": "planner"},
            "level_1": [
                {"id": "recon", "description": "Reconnaissance", "supervisor": "vuln_assessment", "type": "supervisor"},
                {"id": "web_testing", "description": "Web Testing", "supervisor": "vuln_assessment", "type": "supervisor"},
                {"id": "network_testing", "description": "Network Testing", "supervisor": "vuln_assessment", "type": "supervisor"}
            ],
            "level_2": [
                {"id": "domain_enum", "description": "Domain enumeration", "supervisor": "recon", "type": "executor"},
                {"id": "port_scan", "description": "Port scanning", "supervisor": "recon", "type": "executor"},
                {"id": "service_detect", "description": "Service detection", "supervisor": "recon", "type": "executor"},
                {"id": "sql_injection", "description": "SQL injection test", "supervisor": "web_testing", "type": "executor"},
                {"id": "xss_test", "description": "XSS testing", "supervisor": "web_testing", "type": "executor"},
                {"id": "dir_enum", "description": "Directory enumeration", "supervisor": "web_testing", "type": "executor"}
            ]
        }
        
        result = Utils.build_map(task_desc)
        
        # Should return a parent lookup table
        assert isinstance(result, dict)
        
        # Check level_1 agents have correct parents
        assert result["recon"] == "vuln_assessment"
        assert result["web_testing"] == "vuln_assessment"
        assert result["network_testing"] == "vuln_assessment"
        
        # Check level_2 agents have correct parents
        assert result["domain_enum"] == "recon"
        assert result["port_scan"] == "recon"
        assert result["service_detect"] == "recon"
        assert result["sql_injection"] == "web_testing"
        assert result["xss_test"] == "web_testing"
        assert result["dir_enum"] == "web_testing"
        
        # Root should not be in the map (has no parent)
        assert "vuln_assessment" not in result
        
        # Should have exactly 9 entries (3 supervisors + 6 executors)
        assert len(result) == 9
