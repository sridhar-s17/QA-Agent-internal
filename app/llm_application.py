"""
QA Agent LLM Application - Handles QA workflow graph generation
Simplified version of UNO's llm_application.py focused on QA automation needs
"""

from models.qa_models import QAGraph, QAPromptContext
from modules.model_manager import Gemini, ModelManager
import os
from pydantic import BaseModel
from typing import Dict, Any, Union

class QALLMApplication:
    """
    Manages interactions with Gemini LLM for QA workflow graph generation.
    Simplified version of UNO's GeminiApplication focused on QA automation.
    """
    
    def __init__(self, model_id: str = None):
        """
        Initialize QA LLM Application with Gemini model.
        
        Args:
            model_id (str, optional): Gemini model ID. If None, uses ModelManager default.
        """
        if model_id is None:
            model_manager = ModelManager()
            model_id = model_manager.get_model_id()
        
        self.gemini = Gemini(model_id=model_id)
        self.model_id = model_id
    
    def _load_prompt(self, prompt_path: str) -> str:
        """
        Load prompt from file.
        
        Args:
            prompt_path (str): Path to prompt file
            
        Returns:
            str: Prompt content
        """
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Prompt file not found: {prompt_path}")
            return ""
    
    def _format_prompt(self, prompt_path: str, **kwargs) -> str:
        """
        Load and format prompt with provided arguments.
        
        Args:
            prompt_path (str): Path to prompt file
            **kwargs: Arguments to format the prompt
            
        Returns:
            str: Formatted prompt
        """
        prompt = self._load_prompt(prompt_path)
        return prompt.format(**kwargs)
    
    def generate_qa_graph(
        self, 
        test_objective: str = "QA automation workflow", 
        application_type: str = "Web Application",
        selenium_functions: list = None,
        validation_requirements: list = None,
        automation_phases: list = None,
        expected_steps: int = 9
    ) -> QAGraph:
        """
        Generate QA workflow graph using the simplified sequential approach.
        
        Args:
            test_objective (str): What the QA automation should achieve
            application_type (str): Type of application being tested
            selenium_functions (list): Available Selenium functions (not used in sequential mode)
            validation_requirements (list): Validation requirements (not used in sequential mode)
            automation_phases (list): QA phases to automate (not used in sequential mode)
            expected_steps (int): Expected number of automation steps (fixed at 9)
            
        Returns:
            QAGraph: Generated QA workflow graph
        """
        # Use the simplified prompt that enforces the sequential workflow
        system_prompt = self._load_prompt("prompts/qa_graph_generation.txt")
        
        if not system_prompt:
            # Fallback to inline sequential prompt
            system_prompt = """
You are a Graph Workflow Agent.

Your responsibility is to populate a sequential QA workflow graph.
The node and edge structure is already enforced by the response schema.
You must only populate values that conform exactly to the schema.

Sequential QA Agent Mapping:
1. AuthenticationAgent - QA_phase: Authentication and setup - phase: Discovery - selenium_functions: execute_authentication_phase
2. RequirementsGatheringAgent - QA_phase: Requirements Gathering - phase: Discovery - selenium_functions: answer_all_questions
3. DiscoveryValidationAgent - QA_phase: Discovery Document Validation - phase: Discovery - selenium_functions: validate_discovery_document
4. WireframesValidationAgent - QA_phase: Wireframes Validation - phase: Wireframe - selenium_functions: validate_wireframes
5. DesignValidationAgent - QA_phase: Design Document Validation - phase: Specification - selenium_functions: validate_design_document
6. BuildProcessAgent - QA_phase: Build Process – Monitor build process - phase: Build - selenium_functions: monitor_build_process
7. TestValidationAgent - QA_phase: Test Document Validation - phase: Test - selenium_functions: validate_test_document
8. PreviewAppAgent - QA_phase: App Preview Validation - phase: Test - selenium_functions: validate_app_preview
9. FinalConfirmationAgent - QA_phase: Final Confirmation - phase: Deploy - selenium_functions: final_confirmation

The workflow is strictly linear. Each node must read from the immediately previous node.
Output MUST be valid JSON and conform to the response schema.
"""
        
        # Generate graph using Gemini
        try:
            response = self.gemini.generate_json(
                system_prompt=system_prompt,
                response_schema=QAGraph
            )
            
            # Parse and return the graph
            qa_graph = QAGraph.model_validate_json(response["content"])
            return qa_graph
            
        except Exception as e:
            print(f"Error generating QA graph: {e}")
            raise
    
    def generate_simple_qa_graph(self, test_description: str = None) -> QAGraph:
        """
        Generate a simple QA graph using the sequential workflow approach.
        
        Args:
            test_description (str): Simple description of what to test (optional, not used in sequential mode)
            
        Returns:
            QAGraph: Generated QA workflow graph
        """
        # Use the same sequential approach as generate_qa_graph
        return self.generate_qa_graph()
    
    def validate_qa_graph(self, graph: QAGraph) -> Dict[str, Any]:
        """
        Validate the generated QA graph for completeness and correctness.
        
        Args:
            graph (QAGraph): QA graph to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges)
        }
        
        # Check for nodes without edges
        node_ids = {node.id for node in graph.nodes}
        edge_sources = {edge.source for edge in graph.edges}
        edge_targets = {edge.target for edge in graph.edges}
        
        # Find orphaned nodes
        orphaned_nodes = node_ids - (edge_sources | edge_targets)
        if orphaned_nodes:
            validation_results["warnings"].append(f"Orphaned nodes found: {orphaned_nodes}")
        
        # Check for invalid edge references
        for edge in graph.edges:
            if edge.source not in node_ids:
                validation_results["errors"].append(f"Edge source '{edge.source}' not found in nodes")
                validation_results["is_valid"] = False
            if edge.target not in node_ids:
                validation_results["errors"].append(f"Edge target '{edge.target}' not found in nodes")
                validation_results["is_valid"] = False
        
        # Check for required phases
        phases = {node.phase for node in graph.nodes}
        required_phases = {"Authentication", "Validation"}
        missing_phases = required_phases - phases
        if missing_phases:
            validation_results["warnings"].append(f"Missing recommended phases: {missing_phases}")
        
        return validation_results