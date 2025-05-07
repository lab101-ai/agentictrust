from crewai import Agent
from demo.agent_tools import workspan_tools_list, cisco_tools_list

def get_workspan_data_agent():
    return Agent(
        role='WorkSpan Data Specialist',
        goal='To accurately retrieve and process information from the WorkSpan database (e.g., partner details, activity logs) based on specific queries. You will receive requests from a Cisco Data Expert and must fulfill them accurately.',
        backstory="An expert in all things WorkSpan, you have years of experience navigating its complex database schemas and APIs. You are meticulous and ensure data accuracy above all. You are tasked with fulfilling data requests from the Cisco Data Expert precisely and efficiently.",
        tools=workspan_tools_list,
        allow_delegation=False,
        verbose=True
    )

def get_cisco_integration_agent():
    return Agent(
        role='Cisco Data and Integration Expert',
        goal="""You are the primary point of contact for the user, interacting via a chat UI.
        Your main objective is to answer the user's queries related to Cisco data by utilizing your specialized Cisco data tools.
        If a user's query requires information from the WorkSpan database (e.g., details about a partner name mentioned, specific WorkSpan activities),
        you MUST first formulate a clear question or task for the 'WorkSpan Data Specialist' and delegate it to them.
        Once you receive the necessary information from the WorkSpan Data Specialist, use it to inform your Cisco data queries (using your Cisco data tools) and formulate a comprehensive final answer for the user.""",
        backstory="A seasoned Cisco solutions expert with deep knowledge of Cisco's product lines, sales data, and partner ecosystem. You are also adept at collaborating with other specialists to gather comprehensive information. Your primary role is to assist users by answering their questions, leveraging both your suite of Cisco data tools and, when necessary, WorkSpan partner data through delegation.",
        tools=cisco_tools_list, 
        allow_delegation=True,  
        verbose=True
    ) 