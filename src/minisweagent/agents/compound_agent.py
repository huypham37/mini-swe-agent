""" The compound agent system that recursively genereates agent on demands."""

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
        self.completion_callback: Optional[Callable[[str,Dict], None]] = None
        self.child_result = {} # Store results from managed agents # Store results from managed agents.


    def set_completion_callback(self, callback):
        """Set a call back when this agent complete"""
        self.completion_callback = callback

    def on_child_completed(self, child_id:str, result:Dict):
        """Called when a managed agent completes"""
        self.child_result[child_id] = result
        if self.all_children_completed():
            self.finalize_and_callback()
         
# {
#   "root": {
#     "id": "vuln_assessment",
#     "description": "Vulnerability Assessment",
#     "type": "planner"
#   },
#   "level_1": [:
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
