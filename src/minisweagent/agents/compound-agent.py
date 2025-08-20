""" The compound agent system that recursively genereates agent on demands."""
from enum import Enum
from minisweagent.agents.interactive import InteractiveAgent

class Status(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentType(Enum):
    PLANNER = "Planner"
    SUPERVISOR = "Supervior"
    EXECUTOR = "Executor"

class CompoundAgent(InteractiveAgent):
    def __init__(self, manages = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = None
        self.agent_type = None
        self.time_complete = 0.0
        self.status = Status.INACTIVE
        self.my_supervisor = None
        self.who_did_what =  {}
        self.manages = manages or []

    def run(self) -> String:
        planner_agent = CompoundAgent(
            model = self.model,
            env = self.env,
            agent_type = AgentType.PLANNER,
            id = "planner_00"
        )

        task_desc = planner_agent.query()
        
        


