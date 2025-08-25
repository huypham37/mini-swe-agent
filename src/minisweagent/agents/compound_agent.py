"""The compound agent system that recursively genereates agent on demands."""

import uuid
from interactive import InteractiveAgent
from typing import Optional, Callable
from enum import Enum
from minisweagent.agents.default import AgentConfig, DefaultAgent, LimitsExceeded, NonTerminatingException, Submitted


class Status(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(Enum):
    PLANNER = "Planner"
    SUPERVISOR = "Supervisor"
    EXECUTOR = "Executor"


# TODO: dont forget to filling the supervisor config
# The system consists of a list of executor to run, but it should not be a Default Agent, this
# is not a good design, but at the moment, I use it to access query() method from Default Agent
class AgentCoordinatoor(DefaultAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.completed_agents = {}  # supervisor_id -> [completed_agent_results]
        self.supervisor_config = {}  # supervisor_id -> supervisor_config
        self.active_supervisors = {}

    # TODO: How do the supervisors know which task they are working on?
    # NOTE: If there are more than 1 layer of supervisor, after the executor
    # submit to their supervisor, then these supervisor dont know their supervisor to
    # create. So I am thinking of making a tree.
    def on_child_completed(self, supervisor_id: str, result: str):
        """generate supervisor agent when child completed"""
        if supervisor_id not in self.completed_agents:
            self.completed_agents[supervisor_id] = []

        self.completed_agents[supervisor_id].append(result)

        # Check if all children submitted
        expected_count = len(self.supervisor_config[supervisor_id])
        if len(self.completed_agents[supervisor_id]) == expected_count:
            supervisor = AgentFactory.generate_supervisor()
            self.active_supervisors[supervisor_id] = supervisor

    def generate_agent(self, agent_type: AgentType):
        if agent_type == AgentType.SUPERVISOR:
            return AgentFactory.generate_supervisor()
        elif agent_type == AgentType.EXECUTOR:
            return AgentFactory.generate_executor()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    # TODO: Supervisor query
    def run(self, task: str, **kwargs) -> str:
        """Run step() until agent is finished. Return exit status & message"""
        self.extra_template_vars |= {"task": task, **kwargs}
        self.messages = []
        self.add_message("system", self.render_template(self.config.system_template))
        self.add_message("user", self.render_template(self.config.instance_template))

        task_desc = self.query()
        self.supervisor_config = Utils.parse_task_structure(task_desc)
        depth = len(task_desc) - 1

        # Distritbute task to small agent and let them work.
        for item in task_desc[f"level_{depth}"]:
            executor = AgentFactory.generate_executor()
            executor.my_supervisor = item["supervisor"]
            atomic_task = item["description"]
            executor.set_completion_callback(self.on_child_completed)

            exit_status, task_result = executor.run(atomic_task)  # task_result: str
            if exit_status == "Submitted":
                result = {"agent_id": executor.id, "result": task_result}
                executor.complete_task(task_result)


def generate_unique_id():
    """Generate a unique agent ID"""
    return f"agent_{uuid.uuid4().hex[:8]}"


class SupervisorAgent(DefaultAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = generate_unique_id()
        self.agent_type = AgentType.SUPERVISOR
        self.status = Status.INACTIVE
        self.completion_callback: Optional[Callable[[str, str], None]] = None
        self.my_supervisor = None
        self.child_results = []

    def set_completion_callback(self, callback):
        """Set a callback when this agent completes"""
        self.completion_callback = callback

    def analyze_results(self, results) -> tuple[str, str]:
        """Analyze child results without execution loop"""
        super().extra_template_vars |= {"task": results, **kwargs}
        super().add_message("system", self.render_template(self.config.system_template))
        super().add_message("user", self.render_template(self.config.instance_template))

        try:
            response = super().query()
            self.status = Status.COMPLETED
            return "Submitted", response["content"]
        except Exception as e:
            self.status = Status.FAILED
            return "Failed", str(e)

    def complete_task(self, result: str | None = None):
        """Complete this agent's task and notify supervisor"""
        self.status = Status.COMPLETED
        if self.completion_callback and self.my_supervisor is not None:
            if result is None:
                result = "No result returned"
            self.completion_callback(self.my_supervisor, result)


class ExecutorAgent(DefaultAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = generate_unique_id()
        self.agent_type = AgentType.EXECUTOR
        self.status = Status.INACTIVE
        self.completion_callback: Optional[Callable[[str, str], None]] = None
        self.my_supervisor = None

    def set_completion_callback(self, callback):
        """Set a callback when this agent completes"""
        self.completion_callback = callback

    def complete_task(self, result: str | None = None):
        """Complete this agent's task and notify supervisor"""
        self.status = Status.COMPLETED
        if self.completion_callback and self.my_supervisor is not None:
            if result is None:
                result = "No result returned"
            self.completion_callback(self.my_supervisor, result)


class AgentFactory:
    @staticmethod
    def generate_supervisor() -> SupervisorAgent:
        return SupervisorAgent()

    @staticmethod
    def generate_executor() -> ExecutorAgent:
        return ExecutorAgent()


class Utils:
    @staticmethod
    def parse_task_structure(task_desc: dict) -> dict:
        """Convert the query to the supervisor -> supervisor_config dictionary"""
        supervisor_config = {}
        for level_key in task_desc:
            if level_key.startswith("level_"):
                for item in task_desc[level_key]:
                    if "supervisor" in item:
                        supervisor_id = item["supervisor"]
                        if supervisor_id in supervisor_config:
                            supervisor_config[supervisor_id].append(item)
        return supervisor_config

    @staticmethod
    def build_map(task_desc: dict) -> dict:
        """Build a parent lookup table: {agent_id: parent_id}"""
        parent_map = {}

        for level_key in task_desc:
            if level_key.startswith("level_"):
                for item in task_desc[level_key]:
                    if "supervisor" in item:
                        parent_map[item["id"]] = item["supervisor"]

        return parent_map


# {
#   "root": {
#     "id": "vuln_assessment",
#     "description": "Vulnerability Assessment",
#     "type": "planner"
#   },
#   "level_1": [
#     {
#       "id": "recon",
#       "description": "Reconnaissance",
#       "supervisor": "vuln_assessment",
#       "type": "supervisor"
#     },
#     {
#       "id": "web_testing",
#       "description": "Web Testing",
#       "supervisor": "vuln_assessment",
#       "type": "supervisor"
#     },
#     {
#       "id": "network_testing",
#       "description": "Network Testing",
#       "supervisor": "vuln_assessment",
#       "type": "supervisor"
#     }
#   ],
#   "level_2": [
#     {
#       "id": "domain_enum",
#       "description": "Domain enumeration",
#       "supervisor": "recon",
#       "type": "executor",
#       "command": "subfinder -d target.com"
#     },
#     {
#       "id": "port_scan",
#       "description": "Port scanning",
#       "supervisor": "recon",
#       "type": "executor",
#       "command": "nmap -sS target.com"
#     },
#     {
#       "id": "service_detect",
#       "description": "Service detection",
#       "supervisor": "recon",
#       "type": "executor",
#       "command": "nmap -sV target.com"
#     },
#     {
#       "id": "sql_injection",
#       "description": "SQL injection test",
#       "supervisor": "web_testing",
#       "type": "executor",
#       "command": "sqlmap -u http://target.com/login"
#     },
#     {
#       "id": "xss_test",
#       "description": "XSS testing",
#       "supervisor": "web_testing",
#       "type": "executor",
#       "command": "xsshunter scan http://target.com"
#     },
#     {
#       "id": "dir_enum",
#       "description": "Directory enumeration",
#       "supervisor": "web_testing",
#       "type": "executor",
#       "command": "gobuster dir -u http://target.com"
#     }
#   ]
# }
