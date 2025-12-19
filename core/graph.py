"""
QA Graph - Static workflow graph for QA automation
Uses Pydantic models for consistency and validation.
"""

from typing import List, Dict, Any, Optional
import json
import os
from enum import Enum
import sys

# Import Pydantic models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.qa_models import QANode, QAEdge

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
    END = "EndAgent"

class QAGraph:
    """QA workflow graph using Pydantic models"""
    
    def __init__(self):
        """Initialize QA graph with static workflow"""
        self.nodes: List[QANode] = []
        self.edges: List[QAEdge] = []
        self.steps_config = self._load_steps_config()
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
        auth_node = QANode(
            id="authentication_1",
            type=NodeType.AUTHENTICATION.value,
            phase=auth_config["phase"],
            reads=[],  # Start node has no dependencies
            selenium_functions=auth_config["selenium_functions"] # Get first selenium function
        )
        
        # Phase 2: REQUIREMENTS GATHERING  
        requirements_config = self.steps_config["requirements"]
        requirements_node = QANode(
            id="requirements_2",
            type=NodeType.REQUIREMENTS_GATHERING.value,
            phase=requirements_config["phase"],
            reads=["authentication_1"],
            selenium_functions=requirements_config["selenium_functions"]
        )
        
        # Phase 3: DISCOVERY DOCUMENT VALIDATION
        discovery_config = self.steps_config["discovery"]
        discovery_validation_node = QANode(
            id="discovery_validation_3",
            type=NodeType.DISCOVERY_VALIDATION.value,
            phase=discovery_config["phase"],
            reads=["requirements_2"],
            selenium_functions=discovery_config["selenium_functions"]
        )
        
        # Phase 4: WIREFRAMES VALIDATION
        wireframes_config = self.steps_config["wireframes"]
        wireframes_validation_node = QANode(
            id="wireframes_validation_4",
            type=NodeType.WIREFRAMES_VALIDATION.value,
            phase=wireframes_config["phase"],
            reads=["discovery_validation_3"],
            selenium_functions=wireframes_config["selenium_functions"]
        )
        
        # Phase 5: DESIGN DOCUMENT VALIDATION
        design_config = self.steps_config["design"]
        design_validation_node = QANode(
            id="design_validation_5", 
            type=NodeType.DESIGN_VALIDATION.value,
            phase=design_config["phase"],
            reads=["wireframes_validation_4"],
            selenium_functions=design_config["selenium_functions"]
        )
        
        # Phase 6: BUILD PROCESS
        build_config = self.steps_config["build"]
        build_process_node = QANode(
            id="build_process_6",
            type=NodeType.BUILD_PROCESS.value,
            phase=build_config["phase"],
            reads=["design_validation_5"],
            selenium_functions=build_config["selenium_functions"]
        )
        
        # Phase 7: TEST PLAN VALIDATION
        test_config = self.steps_config["test"]
        test_validation_node = QANode(
            id="test_validation_7",
            type=NodeType.TEST_VALIDATION.value,
            phase=test_config["phase"],
            reads=["build_process_6"],
            selenium_functions=test_config["selenium_functions"]
        )
        
        # Phase 8: PREVIEW APP
        preview_config = self.steps_config["preview"]
        preview_app_node = QANode(
            id="preview_app_8",
            type=NodeType.PREVIEW_APP.value,
            phase=preview_config["phase"],
            reads=["test_validation_7"],
            selenium_functions=preview_config["selenium_functions"]
        )
        
        # Phase 9: FINAL CONFIRMATION
        final_config = self.steps_config["final"]
        final_confirmation_node = QANode(
            id="final_confirmation_9",
            type=NodeType.FINAL_CONFIRMATION.value,
            phase=final_config["phase"],
            reads=["preview_app_8"],
            selenium_functions=final_config["selenium_functions"]
        )
        
        # End node (no selenium function needed)
        end_node = QANode(
            id="end_workflow",
            type=NodeType.END.value,
            phase="Deploy",
            reads=["final_confirmation_9"]
            # No selenium_function for end node
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
        print(self.nodes)
        # Define edges (workflow flow)
        self.edges = [
            # Linear success flow using QAEdge (Pydantic model)
            QAEdge(source="authentication_1", target="requirements_2"),
            QAEdge(source="requirements_2", target="discovery_validation_3"),
            QAEdge(source="discovery_validation_3", target="wireframes_validation_4"),
            QAEdge(source="wireframes_validation_4", target="design_validation_5"),
            QAEdge(source="design_validation_5", target="build_process_6"),
            QAEdge(source="build_process_6", target="test_validation_7"),
            QAEdge(source="test_validation_7", target="preview_app_8"),
            QAEdge(source="preview_app_8", target="final_confirmation_9"),
            QAEdge(source="final_confirmation_9", target="end_workflow"),
        ]
    
    def get_start_node(self) -> Optional[QANode]:
        """Get the starting node of the workflow"""
        # Find node with no incoming edges
        target_ids = {edge.target for edge in self.edges}
        for node in self.nodes:
            if node.id not in target_ids:
                return node
        return None
    
    def get_next_nodes(self, current_node_id: str, output: str = "SUCCESS") -> List[QANode]:
        """Get next nodes based on current node output"""
        next_node_ids = []
        
        for edge in self.edges:
            if edge.source == current_node_id:
                # If no label or label matches output, include this edge
                if edge.label is None or edge.label == output:
                    next_node_ids.append(edge.target)
        
        # Return corresponding nodes
        return [node for node in self.nodes if node.id in next_node_ids]
    
    def get_node_by_id(self, node_id: str) -> Optional[QANode]:
        """Get node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_nodes_by_phase(self, phase: str) -> List[QANode]:
        """Get all nodes for a specific phase"""
        return [node for node in self.nodes if node.phase == phase]
    
    def save_to_file(self, filepath: str):
        """Save graph to JSON file using Pydantic model_dump"""
        data = {
            "nodes": [node.model_dump() for node in self.nodes],
            "edges": [edge.model_dump() for edge in self.edges]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'QAGraph':
        """Load graph from JSON file using Pydantic models"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = cls.__new__(cls)  # Create without calling __init__
        graph.nodes = []
        graph.edges = []
        
        # Load nodes using QANode (Pydantic model)
        for node_data in data["nodes"]:
            node = QANode(**node_data)
            graph.nodes.append(node)
        
        # Load edges using QAEdge (Pydantic model)
        for edge_data in data["edges"]:
            edge = QAEdge(**edge_data)
            graph.edges.append(edge)
        
        return graph
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of the workflow"""
        phases = {}
        for node in self.nodes:
            if node.phase not in phases:
                phases[node.phase] = []
            phases[node.phase].append({"id": node.id, "type": node.type})
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "phases": phases,
            "start_node": self.get_start_node().id if self.get_start_node() else None
        }