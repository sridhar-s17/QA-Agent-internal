from AuthenticationAgent import AuthenticationAgent
from DiscoveryValidationAgent import DiscoveryValidationAgent
from BuildProcessAgent import BuildProcessAgent
from DesignValidationAgent import DesignValidationAgent
from RequirementsGatheringAgent import RequirementsGatheringAgent
from WireframesValidationAgent import WireframesValidationAgent
from PreviewAppAgent import PreviewAppAgent
from TestValidationAgent import TestValidationAgent
from FinalConfirmationAgent import FinalConfirmationAgent

import logging

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('master_agent.log', encoding='utf-8'),
            logging.StreamHandler()
            ]
        )
logger = logging.getLogger(__name__)

def main():

    # 2. Initialize Shared Resources
    # In a real scenario, this would be your SeleniumClass()
    shared_selenium = {"browser": "chrome"} 
    
    # 3. Define/Load your Graph (Logic for the flow)
    # This could also be loaded from a JSON file
    graph_config = {
        "start": "login",
        "nodes": {
            "login": {"agent": "auth", "next": "requirement"},
            "requirement": {"agent": "requirement", "next": "discovery"},
            "discovery": {"agent": "discovery", "next": "wireframe"},
            "wireframe": {"agent": "wireframe", "next": "design"},
            "design": {"agent": "design", "next": "build"},
            "build": {"agent": "build", "next": "test"},
            "test": {"agent": "test", "next": "preview"},
            "preview": {"agent": "preview", "next": "final"},
            "final": {"agent": "final", "next": "end"}
        }
    }

    # 4. Initialize the Agents
    # We pass the same 'shared_selenium' to all of them
    agents_registry = {
        "auth": AuthenticationAgent(shared_selenium, "Login Task", "Auth-01"),
        "discovery": DiscoveryValidationAgent(shared_selenium, "Discovery Doc Validation", "dis-01"),
        "requirement":RequirementsGatheringAgent(shared_selenium, "Requirement Gathering", "req-01"),
        "wireframe":WireframesValidationAgent(shared_selenium, "WireFrame Validation", "wireframe-01"),
        "design":DesignValidationAgent(shared_selenium, "Design Document Validation", "design-01"),
        "build":BuildProcessAgent(shared_selenium, "Build process", "build-01"),
        "test":TestValidationAgent(shared_selenium, "Test Plan", "test-01"),
        "preview":PreviewAppAgent(shared_selenium, "Preview", "preview-01"),
        "final":FinalConfirmationAgent(shared_selenium, "Final Confirmation", "final-01"),
    }

    # 5. Execute the Workflow
    current_node_key = graph_config["start"]
    
    print("--- Starting Workflow Execution ---")
    
    while current_node_key != "end":
        # Get instructions for the current step
        step_info = graph_config["nodes"].get(current_node_key)
        
        if not step_info:
            break
            
        # Select the correct agent from our registry
        agent_key = step_info["agent"]
        current_agent = agents_registry.get(agent_key)
        logger.info(f"current agent:{agent_key}")
        
        if current_agent:
            # RUN THE AGENT
            current_agent.execute_agent()
        
        # Move to the next node in the graph
        current_node_key = step_info["next"]

    print("--- Workflow Completed Successfully ---")

if __name__ == "__main__":
    main()