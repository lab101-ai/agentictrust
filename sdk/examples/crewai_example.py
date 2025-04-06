import os
import sys
import uuid
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AgenticTrust SDK
from sdk.agentictrust import AgenticTrustClient

# Mock CrewAI imports (these would be real imports in an actual CrewAI application)
class Agent:
    def __init__(self, name, role, goal):
        self.name = name
        self.role = role
        self.goal = goal
        self.client_id = None
        self.client_secret = None
        self.oauth_token = None
        self.task_id = None
        
    def set_credentials(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        
    def set_oauth_token(self, token, task_id):
        self.oauth_token = token
        self.task_id = task_id
        
    def __str__(self):
        return f"Agent(name='{self.name}', role='{self.role}')"

class Task:
    def __init__(self, description, agent):
        self.description = description
        self.agent = agent
        self.task_id = str(uuid.uuid4())
        self.parent_task_id = None
        self.parent_token = None
        
    def set_parent_context(self, parent_task_id, parent_token):
        self.parent_task_id = parent_task_id
        self.parent_token = parent_token
        
    def __str__(self):
        return f"Task(description='{self.description}', task_id='{self.task_id}')"

class Crew:
    def __init__(self, agents, tasks=None):
        self.agents = agents
        self.tasks = tasks or []
        self.oauth_client = AgenticTrustClient(base_url="http://localhost:5000")
        
    def register_agents(self):
        """Register all agents with the AgenticTrust server."""
        for agent in self.agents:
            print(f"Registering agent: {agent.name}")
            
            # Define agent capabilities based on role
            allowed_tools = []
            allowed_resources = []
            
            if "researcher" in agent.role.lower():
                allowed_tools.extend(["web_search", "document_retrieval"])
                allowed_resources.extend(["search_engine", "document_store"])
                
            if "writer" in agent.role.lower():
                allowed_tools.extend(["text_generation", "summarization"])
                allowed_resources.extend(["content_editor"])
                
            if "analyst" in agent.role.lower():
                allowed_tools.extend(["data_analysis", "chart_generation"])
                allowed_resources.extend(["database", "analytics_platform"])
                
            # Register agent
            response = self.oauth_client.agent.register(
                agent_name=agent.name,
                description=f"{agent.role}: {agent.goal}",
                allowed_tools=allowed_tools,
                allowed_resources=allowed_resources
            )
            
            # Store credentials
            agent.set_credentials(
                response["credentials"]["client_id"],
                response["credentials"]["client_secret"]
            )
            
            # Activate agent
            self.oauth_client.agent.activate(
                response["credentials"]["registration_token"]
            )
            
            print(f"Agent registered and activated: {agent.name}")
    
    def get_token_for_task(self, agent: Agent, task: Task) -> Optional[str]:
        """Get an OAuth token for an agent to perform a specific task."""
        if not agent.client_id or not agent.client_secret:
            print(f"Agent {agent.name} has no credentials. Register agents first.")
            return None
            
        # Determine required tools and resources based on task
        required_tools = []
        required_resources = []
        scope = ["execute:task"]
        
        if "search" in task.description.lower() or "find" in task.description.lower():
            required_tools.append("web_search")
            required_resources.append("search_engine")
            scope.append("read:web")
            
        if "write" in task.description.lower() or "create" in task.description.lower():
            required_tools.append("text_generation")
            required_resources.append("content_editor")
            scope.append("write:content")
            
        if "analyze" in task.description.lower() or "review" in task.description.lower():
            required_tools.append("data_analysis")
            required_resources.append("database")
            scope.append("read:data")
            
        # Request token
        print(f"Requesting token for task: {task.description}")
        response = self.oauth_client.token.request(
            client_id=agent.client_id,
            client_secret=agent.client_secret,
            scope=scope,
            task_id=task.task_id,
            task_description=task.description,
            required_tools=required_tools,
            required_resources=required_resources,
            parent_task_id=task.parent_task_id,
            parent_token=task.parent_token
        )
        
        # Store token in agent
        agent.set_oauth_token(response["access_token"], task.task_id)
        
        print(f"Token obtained for task: {task.description}")
        print(f"Granted tools: {response['granted_tools']}")
        print(f"Granted resources: {response['granted_resources']}")
        
        return response["access_token"]
    
    def execute_task(self, task: Task) -> dict:
        """Execute a task with the appropriate agent and token."""
        # Get token for task
        token = self.get_token_for_task(task.agent, task)
        if not token:
            return {"error": "Failed to obtain token for task"}
            
        # Verify token before using it
        verification = self.oauth_client.token.verify()
        if not verification["is_valid"]:
            return {"error": "Invalid token", "details": verification}
            
        # Call protected endpoint to simulate task execution
        try:
            print(f"Executing task: {task.description}")
            result = self.oauth_client.token.call_protected_endpoint()
            
            # In a real application, this would be replaced with actual agent execution logic
            print(f"Task executed successfully: {task.description}")
            
            return {
                "status": "success",
                "task_id": task.task_id,
                "agent": task.agent.name,
                "result": "Task completed successfully"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def create_subtask(self, parent_task: Task, description: str, agent: Agent) -> Task:
        """Create a subtask with parent task context."""
        task = Task(description, agent)
        task.set_parent_context(parent_task.task_id, parent_task.agent.oauth_token)
        self.tasks.append(task)
        return task
    
    def run(self):
        """Run the crew's workflow of tasks."""
        # Register all agents first
        self.register_agents()
        
        # Execute tasks in sequence
        results = []
        for task in self.tasks:
            result = self.execute_task(task)
            results.append(result)
            
        return results

# Example usage
if __name__ == "__main__":
    # Create agents
    researcher = Agent(
        name="ResearchAgent",
        role="Researcher",
        goal="Find relevant information from the web"
    )
    
    writer = Agent(
        name="WriterAgent",
        role="Content Writer",
        goal="Create engaging content based on research"
    )
    
    analyst = Agent(
        name="AnalystAgent",
        role="Data Analyst",
        goal="Analyze and interpret data"
    )
    
    # Create tasks
    research_task = Task(
        description="Search for latest AI developments in authentication", 
        agent=researcher
    )
    
    writing_task = Task(
        description="Write a blog post about AI authentication methods",
        agent=writer
    )
    
    analysis_task = Task(
        description="Analyze effectiveness of different authentication approaches",
        agent=analyst
    )
    
    # Create crew
    crew = Crew(
        agents=[researcher, writer, analyst],
        tasks=[research_task, writing_task, analysis_task]
    )
    
    # Run workflow
    print("Starting CrewAI workflow with AgenticTrust OAuth...")
    results = crew.run()
    
    # After tasks complete, create a subtask (demonstrating parent-child relationship)
    if results and "error" not in results[0]:
        print("\nCreating subtask with parent context...")
        subtask = crew.create_subtask(
            parent_task=research_task,
            description="Verify and validate research findings",
            agent=analyst
        )
        
        subtask_result = crew.execute_task(subtask)
        print(f"Subtask result: {subtask_result}")
        
        # Revoke token when done
        print("\nRevoking token after task completion...")
        revocation = crew.oauth_client.token.revoke(
            token=researcher.oauth_token,
            reason="Task completed"
        )
        print(f"Token revocation: {revocation}")
    
    print("\nWorkflow completed!") 