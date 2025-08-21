import json
from typing import Dict, Any, List, Optional


class JsonParser:
    def __init__(self, json_data: str = ""):
        """Initialize with optional JSON string"""
        self.json_data = json_data
        self.parsed_data = None
    
    def load_from_string(self, json_string: str) -> Dict[str, Any]:
        """Parse JSON from string"""
        try:
            self.parsed_data = json.loads(json_string)
            return self.parsed_data
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {}
    
    def load_from_file(self, file_path: str) -> Dict[str, Any]:
        """Parse JSON from file"""
        try:
            with open(file_path, 'r') as file:
                self.parsed_data = json.load(file)
                return self.parsed_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON file: {e}")
            return {}
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get value by key from parsed data"""
        if self.parsed_data is None:
            return default
        return self.parsed_data.get(key, default)
    
    def get_nested_value(self, keys: List[str], default: Any = None) -> Any:
        """Get nested value using list of keys"""
        if self.parsed_data is None:
            return default
        
        current = self.parsed_data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def to_json_string(self, indent: int = 2) -> str:
        """Convert parsed data back to JSON string"""
        if self.parsed_data is None:
            return "{}"
        return json.dumps(self.parsed_data, indent=indent)
    
    def save_to_file(self, file_path: str, indent: int = 2) -> bool:
        """Save parsed data to JSON file"""
        try:
            with open(file_path, 'w') as file:
                json.dump(self.parsed_data, file, indent=indent)
            return True
        except Exception as e:
            print(f"Error saving JSON file: {e}")
            return False


# Example usage (you can fill in your JSON data)
if __name__ == "__main__":
    parser = JsonParser()
    
    # Example JSON - replace with your own
    sample_json = '''
    {
    "root": {
        "id": "vuln_assessment",
        "description": "Vulnerability Assessment",
        "type": "planner"
    },
    "level_1": [
        {
        "id": "recon",
        "description": "Reconnaissance",
        "supervisor": "vuln_assessment",
        "type": "supervisor"
        },
        {
        "id": "web_testing", 
        "description": "Web Testing",
        "supervisor": "vuln_assessment",
        "type": "supervisor"
        },
        {
        "id": "network_testing",
        "description": "Network Testing", 
        "supervisor": "vuln_assessment",
        "type": "supervisor"
        }
    ],
    "level_2": [
        {
        "id": "domain_enum",
        "description": "Domain enumeration",
        "supervisor": "recon",
        "type": "executor",
        "command": "subfinder -d target.com"
        },
        {
        "id": "port_scan",
        "description": "Port scanning", 
        "supervisor": "recon",
        "type": "executor",
        "command": "nmap -sS target.com"
        },
        {
        "id": "service_detect",
        "description": "Service detection",
        "supervisor": "recon", 
        "type": "executor",
        "command": "nmap -sV target.com"
        },
        {
        "id": "sql_injection",
        "description": "SQL injection test",
        "supervisor": "web_testing",
        "type": "executor", 
        "command": "sqlmap -u http://target.com/login"
        },
        {
        "id": "xss_test",
        "description": "XSS testing",
        "supervisor": "web_testing",
        "type": "executor",
        "command": "xsshunter scan http://target.com"
        },
        {
        "id": "dir_enum",
        "description": "Directory enumeration",
        "supervisor": "web_testing",
        "type": "executor",
        "command": "gobuster dir -u http://target.com"
        }
    ]
    }
    '''
    
    # Parse the JSON
    data = parser.load_from_string(sample_json)
    print("Parsed data:", data)
    
    # Get values
    print(type(data))
    # Convert back to string

