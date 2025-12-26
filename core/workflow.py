"""
QA Workflow Engine - Orchestrates the execution of QA phases
Uses distributed agent pattern for better maintainability
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio

import sys
import os
# Add project root to path for selenium module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from agents.AuthenticationAgent import AuthenticationAgent
from agents.RequirementsGatheringAgent import RequirementsGatheringAgent
from agents.DiscoveryValidationAgent import DiscoveryValidationAgent
from agents.WireframesValidationAgent import WireframesValidationAgent
from agents.DesignValidationAgent import DesignValidationAgent
from agents.BuildProcessAgent import BuildProcessAgent
from agents.TestValidationAgent import TestValidationAgent
from agents.PreviewAppAgent import PreviewAppAgent
from agents.FinalConfirmationAgent import FinalConfirmationAgent
from agents.EndAgent import EndAgent
from selenium_automation.automation_core import SeleniumAutomationCore
from core.graph import QAGraph
from models.qa_models import QANode

class QAWorkflow:
    """
    Manages the execution of QA workflow using distributed agent pattern.
    Each node type is handled by a dedicated agent class for better maintainability.
    """
    
    def __init__(self, context):
        """Initialize QA Workflow with distributed agents"""
        self.context = context
        self.selenium_core = SeleniumAutomationCore(context)
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.QAWorkflow")
        
        # Initialize static QA graph
        self.logger.info("📋 Using static QA graph")
        self.graph = QAGraph()
        
        self.nodes = {node.id: node for node in self.graph.nodes}
        self.edges = self._build_edges_dict()
        
        # Execution state
        self.outputs = {}  # Store outputs from each node
        self.current_node_id = None
        self.executed_nodes = []
        self.failed_nodes = []
        
        # Initialize all agents
        self.agents = {
            "AuthenticationAgent": AuthenticationAgent(self.selenium_core, self.context, self.outputs, "Authentication and setup", "AuthenticationAgent"),
            "RequirementsGatheringAgent": RequirementsGatheringAgent(self.selenium_core, self.context, self.outputs, "Requirements gathering", "RequirementsGatheringAgent"),
            "DiscoveryValidationAgent": DiscoveryValidationAgent(self.selenium_core, self.context, self.outputs, "Discovery validation", "DiscoveryValidationAgent"),
            "WireframesValidationAgent": WireframesValidationAgent(self.selenium_core, self.context, self.outputs, "Wireframes validation", "WireframesValidationAgent"),
            "DesignValidationAgent": DesignValidationAgent(self.selenium_core, self.context, self.outputs, "Design validation", "DesignValidationAgent"),
            "BuildProcessAgent": BuildProcessAgent(self.selenium_core, self.context, self.outputs, "Build process", "BuildProcessAgent"),
            "TestValidationAgent": TestValidationAgent(self.selenium_core, self.context, self.outputs, "Test validation", "TestValidationAgent"),
            "PreviewAppAgent": PreviewAppAgent(self.selenium_core, self.context, self.outputs, "Preview app", "PreviewAppAgent"),
            "FinalConfirmationAgent": FinalConfirmationAgent(self.selenium_core, self.context, self.outputs, "Final confirmation", "FinalConfirmationAgent"),
            "EndAgent": EndAgent(self.selenium_core, self.context, self.outputs, "End workflow", "EndAgent")
        }
        
        # Save graph for debugging
        self.graph.save_to_file("qa_workflow_graph.json")
    
    def _build_edges_dict(self) -> Dict[str, List[Any]]:
        """Build adjacency list representation of graph edges"""
        edge_dict = {}
        for edge in self.graph.edges:
            if edge.source not in edge_dict:
                edge_dict[edge.source] = []
            edge_dict[edge.source].append(edge)
        print(edge_dict)
        return edge_dict
    
    async def execute_workflow(self, start_node_id: str = None) -> Dict[str, Any]:
        """
        Execute the complete QA workflow using distributed agents.
        
        Args:
            start_node_id (str): Node ID to start execution from (default: start node)
            
        Returns:
            Dict[str, Any]: Workflow execution result
        """
        self.logger.info("🚀 Starting QA Workflow execution (Distributed Agents)")
        
        workflow_start_time = datetime.now()
        
        try:
            # Find start node
            if not start_node_id:
                start_node = self.graph.get_start_node()
                if not start_node:
                    raise ValueError("No start node found in graph")
                start_node_id = start_node.id
            
            self.logger.info(f"📋 Total nodes: {len(self.graph.nodes)}")
            self.logger.info(f"🎯 Starting from node: {start_node_id}")
            
            # Execute workflow using breadth-first execution
            ready_nodes = [start_node_id]
            is_end_node = await self._execute_graph(ready_nodes)
            
            if is_end_node:
                return self._create_workflow_result(
                    success=True,
                    message="QA Workflow completed successfully",
                    start_time=workflow_start_time
                )
            else:
                return self._create_workflow_result(
                    success=False,
                    message="Workflow execution incomplete",
                    start_time=workflow_start_time
                )
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {e}"
            self.logger.error(error_msg)
            return self._create_workflow_result(
                success=False,
                message=error_msg,
                start_time=workflow_start_time
            )
        finally:
            # Save results and cleanup
            await self._cleanup_workflow()
    
    async def _execute_graph(self, ready_nodes: List[str]) -> bool:
        """
        Execute workflow graph using breadth-first approach with distributed agents.
        
        Args:
            ready_nodes: List of node IDs ready for execution
            
        Returns:
            bool: True if reached end node, False otherwise
        """
        while ready_nodes:
            current_node_id = ready_nodes.pop(0)
            current_node = self.nodes.get(current_node_id)
            
            if not current_node:
                self.logger.error(f"Node '{current_node_id}' not found. Skipping.")
                continue
            
            self.logger.info(f"🔄 Executing Node: {current_node_id} ({current_node.type})")
            
            # Add guided step to context if present
            if current_node.guided_step:
                self.context.test_results[f"{current_node_id}_guided_step"] = current_node.guided_step
            
            if current_node.introduction:
                self.context.test_results[f"{current_node_id}_introduction"] = current_node.introduction
            
            # Execute node using distributed agent
            try:
                response = await self._execute_node(current_node)
                self.logger.info(f"📊 Response from Node: {current_node_id} - {response.get('type', 'unknown')}")
                
                # Store response
                self.outputs[current_node_id] = response.get("message", "SUCCESS")
                self.context.test_results[current_node_id] = response
                self.current_node_id = current_node_id
                
                # Check if this is an end node
                if current_node.type == "EndAgent":
                    self.logger.info("🏁 Reached end node - workflow completed")
                    return True
                
                # Check if execution should break (error or confirmation needed)
                if response.get("type") == "error":
                    self.logger.error(f"❌ Node {current_node_id} failed: {response.get('message')}")
                    self.failed_nodes.append(current_node_id)
                    return False
                
                # Add guided step complete message
                if current_node.guided_step_complete:
                    self.context.test_results[f"{current_node_id}_complete"] = current_node.guided_step_complete
                
                # Get next nodes to execute based on response type
                output_status = "SUCCESS" if response.get("type") == "success" else "FAILURE"
                next_nodes = self.graph.get_next_nodes(current_node_id, output_status)
                
                self.logger.info(f"🔗 Next nodes from {current_node_id} with status {output_status}: {[n.id for n in next_nodes]}")
                ready_nodes.extend([node.id for node in next_nodes])
                
                self.executed_nodes.append(current_node_id)
                
            except Exception as e:
                error_msg = f"Node {current_node_id} execution failed: {e}"
                self.logger.error(error_msg)
                self.failed_nodes.append(current_node_id)
                return False
        
        return False  # No more nodes to execute but didn't reach end
    
    async def _execute_node(self, node: QANode) -> Dict[str, Any]:
        """
        Execute a specific node using distributed agent pattern.
        
        Args:
            node: Node to execute
            
        Returns:
            Dict[str, Any]: Node execution result
        """
        self.logger.info(f"🔄 Executing node: {node.id} ({node.type})")
        
        try:
            # Check if agent exists for this node type
            if node.type not in self.agents:
                return {
                    "type": "error",
                    "message": f"Agent {node.type} not found in agents dictionary",
                    "node": node.id
                }
            print(f"node type ---->{node.type}")
            # Execute agent
            agent = self.agents[node.type]
            result = await agent.execute_agent(node)
            
            self.logger.info(f"📊 Node {node.id} result: {result.get('type', 'unknown')}")
            return result
            
        except Exception as e:
            error_msg = f"Node {node.id} execution failed: {e}"
            self.logger.error(error_msg)
            return {
                "type": "error",
                "message": error_msg,
                "node": node.id
            }
    

    async def _cleanup_workflow(self):
        """Cleanup workflow resources"""
        try:
            self.logger.info("🧹 Cleaning up workflow resources...")
            
            # Save test results
            results_file = self.context.save_results()
            self.logger.info(f"💾 Test results saved to: {results_file}")
            
            # Cleanup selenium
            self.selenium_core.cleanup()
            
            self.logger.info("✅ Workflow cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Cleanup warning: {e}")
    
    def _create_workflow_result(self, success: bool, message: str, 
                              failed_node: str = None, start_time: datetime = None) -> Dict[str, Any]:
        """Create workflow execution result"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() if start_time else 0
        
        return {
            "success": success,
            "message": message,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "executed_nodes": self.executed_nodes,
            "failed_nodes": self.failed_nodes,
            "failed_node": failed_node,
            "total_nodes": len(self.graph.nodes),
            "completed_nodes": len(self.executed_nodes),
            "success_rate": (len(self.executed_nodes) / len(self.graph.nodes)) * 100,
            "context_summary": self.context.get_test_summary(),
            "graph_summary": self.graph.get_workflow_summary()
        }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow"""
        graph_summary = self.graph.get_workflow_summary()
        
        return {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "graph_summary": graph_summary,
            "qa_steps_config": self.graph.steps_config,
            "current_node": self.current_node_id,
            "executed_nodes": self.executed_nodes,
            "failed_nodes": self.failed_nodes,
            "outputs": self.outputs,
            "available_agents": list(self.agents.keys())
        }
