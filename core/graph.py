"""
QA Graph - Static workflow graph for QA automation
Since QA flow is always the same (14 steps, 9 phases), we use a static graph
instead of LLM generation like UNO-MCP.
Steps are loaded from external JSON file to prepare for future LLM generation.
"""

from typing import List, Dict, Any, Optional
import json
import os
from enum import Enum

class NodeType(Enum):
    """Node types for QA workflow"""
    AUTHENTICATION = "AuthenticationAgent"
    REQUIREMENTS_GATHERING = "RequirementsGatheringAgent"
    DISCOVERY_VALIDATION = "DiscoveryValidationAgent"
    WIREFRAMES_VALIDATION = "WireframesValidationAgent"
    DESIGN_VALIDATION = "DesignValidationAgent"
    BUILD_PROCESS = "BuildProcessAgent"
    TEST_VALIDATION = "TestValidationAgent"
    PREVIEW_APP = "PreviewAppAgent"
    FINAL_CONFIRMATION = "FinalConfirmationAgent"
    CONFIRMATION = "ConfirmationAgent"
    END = "EndAgent"

# Simple wrapper classes for compatibility
class Node:
    """Node class for QA workflow graph"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # No default values - JSON file is single source of truth
        # But ensure attributes exist to prevent AttributeError
        for attr in ['reads', 'message', 'query', 'guided_step', 'guided_step_complete', 
                     'introduction', 'transition_prompt', 'selenium_functions']:
            if not hasattr(self, attr):
                setattr(self, attr, [] if attr in ['reads', 'selenium_functions'] else "")

class Edge:
    """Legacy Edge class for backward compatibility"""
    def __init__(self, source: str, target: str, label: Optional[str] = None, condition: Optional[str] = None):
        self.source = source
        self.target = target
        self.label = label
        self.condition = condition

class QAGraph:
    """
    Static QA workflow graph - always the same 14 steps, 9 phases.
    No LLM generation needed since QA flow is consistent.
    """
    
    def __init__(self):
        """Initialize static QA graph"""
        self.nodes = []
        self.edges = []
        self.guided_journey = ""
        self.test_objective = "QA Automation for App Creation Process"
        self.expected_duration = "5-10 minutes"
        self.automation_scope = "Full app creation workflow validation"
        
        # Load steps configuration from JSON file
        self.steps_config = self._load_steps_config()
        
        # Build the static graph
        self._build_qa_graph()
    
    def _load_steps_config(self) -> Dict[str, Any]:
        """Load QA steps configuration from JSON file"""
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "qa_steps.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_qa_graph(self):
        """Build the QA workflow graph with all phases using steps from JSON config"""
        
        # Phase 1: AUTHENTICATION & SETUP
        auth_config = self.steps_config["authentication"]
        auth_node = Node(
            id="authentication_1",
            type=NodeType.AUTHENTICATION.value,
            phase=auth_config["phase"],
            steps=auth_config["step_numbers"],
            selenium_functions=auth_config["selenium_functions"],
            description=auth_config["description"],
            guided_step="🔐 Phase 1: AUTHENTICATION & SETUP\nInitializing browser and logging into the platform...",
            guided_step_complete="✅ Authentication completed successfully. Browser ready for testing.",
            introduction="Starting QA automation with authentication and setup phase.",
            message="Proceed to requirements gathering?",
            query="Authenticate and setup browser session"
        )
        
        # Phase 2: REQUIREMENTS GATHERING  
        requirements_config = self.steps_config["requirements"]
        requirements_node = Node(
            id="requirements_2",
            type=NodeType.REQUIREMENTS_GATHERING.value,
            phase=requirements_config["phase"], 
            steps=requirements_config["step_numbers"],
            selenium_functions=requirements_config["selenium_functions"],
            description=requirements_config["description"],
            guided_step="📋 Phase 2: REQUIREMENTS GATHERING\nAutomatically answering all questions...",
            guided_step_complete="✅ All questions answered successfully. Requirements gathered.",
            reads=["authentication_1"],
            query="Answer all questions automatically"
        )
        

        
        # Phase 3: DISCOVERY DOCUMENT VALIDATION
        discovery_config = self.steps_config["discovery"]
        discovery_validation_node = Node(
            id="discovery_validation_3",
            type=NodeType.DISCOVERY_VALIDATION.value,
            phase=discovery_config["phase"],
            steps=discovery_config["step_numbers"],
            selenium_functions=discovery_config["selenium_functions"],
            description=discovery_config["description"],
            guided_step="📄 Phase 3: DISCOVERY DOCUMENT VALIDATION\nOpening and validating discovery document...",
            guided_step_complete="✅ Discovery document validated successfully.",
            reads=["requirements_2"],
            query="Validate discovery document"
        )
        
        # Phase 4: WIREFRAMES VALIDATION
        wireframes_config = self.steps_config["wireframes"]
        wireframes_validation_node = Node(
            id="wireframes_validation_4",
            type=NodeType.WIREFRAMES_VALIDATION.value,
            phase=wireframes_config["phase"],
            steps=wireframes_config["step_numbers"],
            selenium_functions=wireframes_config["selenium_functions"],
            description=wireframes_config["description"],
            guided_step="🎨 Phase 4: WIREFRAMES VALIDATION\nViewing and validating wireframes...",
            guided_step_complete="✅ Wireframes validated successfully.",
            reads=["discovery_validation_3"],
            query="Validate wireframes and UI mockups"
        )
        
        # Phase 5: DESIGN DOCUMENT VALIDATION
        design_config = self.steps_config["design"]
        design_validation_node = Node(
            id="design_validation_5", 
            type=NodeType.DESIGN_VALIDATION.value,
            phase=design_config["phase"],
            steps=design_config["step_numbers"],
            selenium_functions=design_config["selenium_functions"],
            description=design_config["description"],
            guided_step="📐 Phase 5: DESIGN DOCUMENT VALIDATION\nViewing and validating design document...",
            guided_step_complete="✅ Design document validated successfully.",
            reads=["wireframes_validation_4"],
            query="Validate design document and specifications"
        )
        
        # Phase 6: BUILD PROCESS
        build_config = self.steps_config["build"]
        build_process_node = Node(
            id="build_process_6",
            type=NodeType.BUILD_PROCESS.value,
            phase=build_config["phase"],
            steps=build_config["step_numbers"],
            selenium_functions=build_config["selenium_functions"],
            description=build_config["description"],
            guided_step="🔨 Phase 6: BUILD PROCESS\nMonitoring application build process...",
            guided_step_complete="✅ Build process completed successfully.",
            reads=["design_validation_5"],
            query="Monitor and validate build process"
        )
        
        # Phase 7: TEST PLAN VALIDATION
        test_config = self.steps_config["test"]
        test_validation_node = Node(
            id="test_validation_7",
            type=NodeType.TEST_VALIDATION.value,
            phase=test_config["phase"],
            steps=test_config["step_numbers"],
            selenium_functions=test_config["selenium_functions"],
            description=test_config["description"],
            guided_step="🧪 Phase 7: TEST PLAN VALIDATION\nOpening and validating test document...",
            guided_step_complete="✅ Test plan validated successfully.",
            reads=["build_process_6"],
            query="Validate test plan and testing approach"
        )
        
        # Phase 8: PREVIEW APP
        preview_config = self.steps_config["preview"]
        preview_app_node = Node(
            id="preview_app_8",
            type=NodeType.PREVIEW_APP.value,
            phase=preview_config["phase"],
            steps=preview_config["step_numbers"],
            selenium_functions=preview_config["selenium_functions"],
            description=preview_config["description"],
            guided_step="👀 Phase 8: PREVIEW APP\nOpening application preview...",
            guided_step_complete="✅ Application preview validated successfully.",
            reads=["test_validation_7"],
            query="Preview and validate application functionality",
            transition_prompt="Application preview completed. Ready for final confirmation?"
        )
        
        # Phase 9: FINAL CONFIRMATION
        final_config = self.steps_config["final"]
        final_confirmation_node = Node(
            id="final_confirmation_9",
            type=NodeType.FINAL_CONFIRMATION.value,
            phase=final_config["phase"],
            steps=final_config["step_numbers"],
            selenium_functions=final_config["selenium_functions"],
            description=final_config["description"],
            guided_step="🎯 Phase 9: FINAL CONFIRMATION\nPerforming final confirmation and QR code verification...",
            guided_step_complete="✅ QA automation workflow completed successfully!",
            reads=["preview_app_8"],
            query="Perform final confirmation and verify deployment"
        )
        
        # End node
        end_node = Node(
            id="end_workflow",
            type=NodeType.END.value,
            phase="Deploy",
            steps=[],
            description="QA workflow completed successfully",
            message="🎉 QA Automation completed! All phases validated successfully.",
            reads=["final_confirmation_9"]
        )
        
        # Add all nodes
        self.nodes = [
            auth_node,
            requirements_node,
            discovery_validation_node,
            wireframes_validation_node,
            design_validation_node,
            build_process_node,
            test_validation_node,
            preview_app_node,
            final_confirmation_node,
            end_node
        ]
        
        # Define edges (workflow flow) - Clean linear flow only
        self.edges = [
            # Linear success flow
            Edge("authentication_1", "requirements_2", "SUCCESS"),
            Edge("requirements_2", "discovery_validation_3", "SUCCESS"),
            Edge("discovery_validation_3", "wireframes_validation_4", "SUCCESS"),
            Edge("wireframes_validation_4", "design_validation_5", "SUCCESS"),
            Edge("design_validation_5", "build_process_6", "SUCCESS"),
            Edge("build_process_6", "test_validation_7", "SUCCESS"),
            Edge("test_validation_7", "preview_app_8", "SUCCESS"),
            Edge("preview_app_8", "final_confirmation_9", "SUCCESS"),
            Edge("final_confirmation_9", "end_workflow", "SUCCESS"),
        ]
    
    def get_start_node(self) -> Optional[Node]:
        """Get the starting node of the workflow"""
        # Find node with no incoming edges
        target_ids = {edge.target for edge in self.edges}
        for node in self.nodes:
            if node.id not in target_ids:
                return node
        return None
    
    def get_next_nodes(self, current_node_id: str, output: str = "SUCCESS") -> List[Node]:
        """Get next nodes based on current node output"""
        next_node_ids = []
        
        for edge in self.edges:
            if edge.source == current_node_id:
                # If no label or label matches output, include this edge
                if edge.label is None or edge.label == output:
                    next_node_ids.append(edge.target)
        
        # Return corresponding nodes
        return [node for node in self.nodes if node.id in next_node_ids]
    
    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_nodes_by_phase(self, phase: str) -> List[Node]:
        """Get all nodes for a specific phase"""
        return [node for node in self.nodes if node.phase == phase]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation"""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "phase": node.phase,
                    "steps": node.steps,
                    "description": node.description,
                    "message": node.message,
                    "query": node.query,
                    "guided_step": node.guided_step,
                    "guided_step_complete": node.guided_step_complete,
                    "introduction": node.introduction,
                    "transition_prompt": node.transition_prompt,
                    "reads": node.reads,
                    "selenium_functions": getattr(node, 'selenium_functions', [])
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.label,
                    "condition": edge.condition
                }
                for edge in self.edges
            ]
        }
    
    def save_to_file(self, filepath: str):
        """Save graph to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'QAGraph':
        """Load graph from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = cls.__new__(cls)  # Create without calling __init__
        graph.nodes = []
        graph.edges = []
        
        # Load nodes
        for node_data in data["nodes"]:
            node = Node(**node_data)
            graph.nodes.append(node)
        
        # Load edges
        for edge_data in data["edges"]:
            edge = Edge(**edge_data)
            graph.edges.append(edge)
        
        return graph
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of the workflow"""
        phases = {}
        for node in self.nodes:
            if node.phase not in phases:
                phases[node.phase] = []
            phases[node.phase].append({
                "id": node.id,
                "type": node.type,
                "steps": node.steps,
                "description": node.description
            })
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "phases": phases,
            "start_node": self.get_start_node().id if self.get_start_node() else None,
            "workflow_steps": sum(len(node.steps) for node in self.nodes if node.steps)
        }