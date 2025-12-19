"""
QA Workflow Engine - Orchestrates the execution of QA phases
Similar to UNO's Workflow class but focused on QA automation
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio

# No need to import separate agent classes - using handler methods
import sys
import os
# Add project root to path for selenium module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from selenium_automation.automation_core import SeleniumAutomationCore
from core.graph import QAGraph
from models.qa_models import QANode

class QAWorkflow:
    """
    Manages the execution of QA workflow using graph-based approach with UNO-MCP pattern.
    Each node type maps to a handler method within this class for better state management.
    """
    
    # QA Steps are now loaded from external JSON file (qa_steps.json)
    
    def __init__(self, context):
        """Initialize QA Workflow with static graph execution"""
        self.context = context
        self.selenium_core = SeleniumAutomationCore(context)
        
        # Setup logging FIRST (before using self.logger)
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
        
        # Save graph for debugging
        self.graph.save_to_file("qa_workflow_graph.json")
    
    def _build_edges_dict(self) -> Dict[str, List[Any]]:
        """Build adjacency list representation of graph edges"""
        edge_dict = {}
        for edge in self.graph.edges:
            if edge.source not in edge_dict:
                edge_dict[edge.source] = []
            edge_dict[edge.source].append(edge)
        return edge_dict
    
    async def execute_workflow(self, start_node_id: str = None) -> Dict[str, Any]:
        """
        Execute the complete QA workflow using graph-based execution.
        
        Args:
            start_node_id (str): Node ID to start execution from (default: start node)
            
        Returns:
            Dict[str, Any]: Workflow execution result
        """
        self.logger.info("🚀 Starting QA Workflow execution (Graph-based)")
        
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
        Execute workflow graph using breadth-first approach.
        Similar to UNO's execute method but for QA workflow.
        
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
            
            # Execute node
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
        Execute a specific node using dynamic handler dispatch (UNO-MCP pattern).
        
        Args:
            node: Node to execute
            
        Returns:
            Dict[str, Any]: Node execution result
        """
        self.logger.info(f"🔄 Executing node: {node.id} ({node.type})")
        
        # Dynamic dispatch to handler method based on node type (like UNO-MCP)
        node_type = node.type.lower().replace("agent", "")  # "AuthenticationAgent" -> "authentication"
        handler_method = getattr(self, f'_handle_{node_type}', self._handle_default)
        
        try:
            # Execute handler method with full access to workflow state
            result = await handler_method(node)
            
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
        
        # List of implemented handler methods (UNO-MCP pattern)
        implemented_handlers = {
            "AuthenticationAgent": hasattr(self, '_handle_authentication'),
            "RequirementsGatheringAgent": hasattr(self, '_handle_requirementsgathering'),
            "DiscoveryValidationAgent": hasattr(self, '_handle_discoveryvalidation'),
            "WireframesValidationAgent": hasattr(self, '_handle_wireframesvalidation'),
            "DesignValidationAgent": hasattr(self, '_handle_designvalidation'),
            "BuildProcessAgent": hasattr(self, '_handle_buildprocess'),
            "TestValidationAgent": hasattr(self, '_handle_testvalidation'),
            "PreviewAppAgent": hasattr(self, '_handle_previewapp'),
            "FinalConfirmationAgent": hasattr(self, '_handle_finalconfirmation'),
            "EndAgent": hasattr(self, '_handle_end')
        }
        
        return {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "graph_summary": graph_summary,
            "handler_methods": implemented_handlers,
            "qa_steps_config": self.graph.steps_config,  # Use steps from JSON file
            "current_node": self.current_node_id,
            "executed_nodes": self.executed_nodes,
            "failed_nodes": self.failed_nodes,
            "outputs": self.outputs
        }
    
    # ==================== AGENT HANDLER METHODS (UNO-MCP Pattern) ====================
    
    async def _handle_authentication(self, node: QANode) -> Dict[str, Any]:
        """
        Handles the 'AuthenticationAgent' node - Phase 1: AUTHENTICATION & SETUP
        Gets selenium functions from node and executes them directly
        """
        self.logger.info("🚀 Starting AUTHENTICATION & SETUP phase")
        
        try:
            # Update context
            self.context.current_phase = "authentication"
            
            # Get selenium functions from node
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            self.logger.info(f"🔄 Executing selenium functions: {selenium_functions}")
            
            auth_result = {
                "functions_executed": [],
                "browser_session": "active"
            }
            
            # Execute each selenium function directly
            for function_name in selenium_functions:
                self.logger.info(f"🔄 Executing selenium function: {function_name}")
                
                # Execute selenium function
                step_result = await self._execute_selenium_function(function_name)
                
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                # Store function result
                auth_result["functions_executed"].append({
                    "function": function_name,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Store result in workflow outputs for other agents to access
            self.outputs[node.id] = auth_result
            
            # Phase completed successfully
            return self._create_success_result("Authentication & Setup completed successfully", "Discovery")
            
        except Exception as e:
            error_msg = f"Authentication phase failed: {e}"
            self.logger.error(error_msg)
            return self._create_failure_result("Phase execution failed", error_msg)
    
    async def _handle_requirementsgathering(self, node: QANode) -> Dict[str, Any]:
        """
        Handles the 'RequirementsGatheringAgent' node - Phase 2: REQUIREMENTS GATHERING
        Gets selenium functions from node and executes them directly
        """
        self.logger.info("📋 Starting REQUIREMENTS GATHERING phase")
        
        try:
            # Access previous agent results for coordination
            auth_output = self.outputs.get("authentication_1", {})
            self.logger.info(f"Previous auth result: {auth_output}")
            
            # Update context
            self.context.current_phase = "requirements"
            
            # Get selenium functions from node
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            self.logger.info(f"🔄 Executing selenium functions: {selenium_functions}")
            
            requirements_result = {
                "functions_executed": [],
                "questions_answered": 0
            }
            
            # Execute each selenium function directly
            for function_name in selenium_functions:
                self.logger.info(f"🔄 Executing selenium function: {function_name}")
                
                # Execute selenium function
                step_result = await self._execute_selenium_function(function_name)
                
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                # Store function result
                requirements_result["functions_executed"].append({
                    "function": function_name,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Extract questions count if available
                if "answered" in step_result.get("message", "").lower():
                    try:
                        import re
                        match = re.search(r'answered (\d+)', step_result["message"].lower())
                        if match:
                            requirements_result["questions_answered"] = int(match.group(1))
                    except:
                        requirements_result["questions_answered"] = 1
            
            # Store result for next agents
            self.outputs[node.id] = requirements_result
            
            return self._create_success_result("Requirements gathering completed successfully", "Discovery")
            
        except Exception as e:
            error_msg = f"Requirements gathering failed: {e}"
            self.logger.error(error_msg)
            return self._create_failure_result("Requirements phase failed", error_msg)
    
    async def _handle_discoveryvalidation(self, node: QANode) -> Dict[str, Any]:
        """
        Handles the 'DiscoveryValidationAgent' node - Phase 3: DISCOVERY DOCUMENT VALIDATION
        Gets selenium functions from node and executes them directly
        """
        self.logger.info("📄 Starting DISCOVERY DOCUMENT VALIDATION phase")
        
        try:
            # Access previous results for coordination
            auth_output = self.outputs.get("authentication_1", {})
            requirements_output = self.outputs.get("requirements_2", {})
            
            # Update context
            self.context.current_phase = "discovery"
            
            # Get selenium functions from node
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            self.logger.info(f"🔄 Executing selenium functions: {selenium_functions}")
            
            discovery_result = {"functions_executed": [], "document_validated": True}
            
            # Execute each selenium function directly
            for function_name in selenium_functions:
                step_result = await self._execute_selenium_function(function_name)
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                discovery_result["functions_executed"].append({
                    "function": function_name,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Store result
            self.outputs[node.id] = discovery_result
            
            return self._create_success_result("Discovery document validated successfully", "Wireframe")
            
        except Exception as e:
            error_msg = f"Discovery validation failed: {e}"
            self.logger.error(error_msg)
            return self._create_failure_result("Discovery validation failed", error_msg)
    
    async def _handle_wireframesvalidation(self, node: QANode) -> Dict[str, Any]:
        """
        Handles the 'WireframesValidationAgent' node - Phase 4: WIREFRAMES VALIDATION
        Gets selenium functions from node and executes them directly
        """
        self.logger.info("🎨 Starting WIREFRAMES VALIDATION phase")
        
        try:
            self.context.current_phase = "wireframes"
            
            # Get selenium functions from node
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            wireframes_result = {"functions_executed": [], "wireframes_validated": True}
            
            # Execute each selenium function directly
            for function_name in selenium_functions:
                step_result = await self._execute_selenium_function(function_name)
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                wireframes_result["functions_executed"].append({
                    "function": function_name,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
            
            self.outputs[node.id] = wireframes_result
            
            return self._create_success_result("Wireframes validated successfully", "Specification")
            
        except Exception as e:
            error_msg = f"Wireframes validation failed: {e}"
            self.logger.error(error_msg)
            return self._create_failure_result("Wireframes validation failed", error_msg)
    
    async def _handle_designvalidation(self, node: QANode) -> Dict[str, Any]:
        """Handles the 'DesignValidationAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("📐 Starting DESIGN DOCUMENT VALIDATION phase")
        
        try:
            self.context.current_phase = "design"
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            design_result = {"functions_executed": [], "design_validated": True}
            
            for function_name in selenium_functions:
                step_result = await self._execute_selenium_function(function_name)
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                design_result["functions_executed"].append({
                    "function": function_name, "result": step_result, "timestamp": datetime.now().isoformat()
                })
            
            self.outputs[node.id] = design_result
            return self._create_success_result("Design document validated successfully", "Build")
            
        except Exception as e:
            return self._create_failure_result("Design validation failed", str(e))
    
    async def _handle_buildprocess(self, node: QANode) -> Dict[str, Any]:
        """Handles the 'BuildProcessAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("🔨 Starting BUILD PROCESS phase")
        
        try:
            self.context.current_phase = "build"
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            build_result = {"functions_executed": [], "build_completed": True}
            
            for function_name in selenium_functions:
                step_result = await self._execute_selenium_function(function_name)
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                build_result["functions_executed"].append({
                    "function": function_name, "result": step_result, "timestamp": datetime.now().isoformat()
                })
            
            self.outputs[node.id] = build_result
            return self._create_success_result("Build process completed successfully", "Test")
            
        except Exception as e:
            return self._create_failure_result("Build process failed", str(e))
    
    async def _handle_testvalidation(self, node: QANode) -> Dict[str, Any]:
        """Handles the 'TestValidationAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("🧪 Starting TEST PLAN VALIDATION phase")
        
        try:
            self.context.current_phase = "test"
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            test_result = {"functions_executed": [], "test_plan_validated": True}
            
            for function_name in selenium_functions:
                step_result = await self._execute_selenium_function(function_name)
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                test_result["functions_executed"].append({
                    "function": function_name, "result": step_result, "timestamp": datetime.now().isoformat()
                })
            
            self.outputs[node.id] = test_result
            return self._create_success_result("Test plan validated successfully", "Test")
            
        except Exception as e:
            return self._create_failure_result("Test validation failed", str(e))
    
    async def _handle_previewapp(self, node: QANode) -> Dict[str, Any]:
        """Handles the 'PreviewAppAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("👀 Starting PREVIEW APP phase")
        
        try:
            self.context.current_phase = "preview"
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            preview_result = {"functions_executed": [], "preview_validated": True}
            
            for function_name in selenium_functions:
                step_result = await self._execute_selenium_function(function_name)
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                preview_result["functions_executed"].append({
                    "function": function_name, "result": step_result, "timestamp": datetime.now().isoformat()
                })
            
            self.outputs[node.id] = preview_result
            return self._create_success_result("Application preview validated successfully", "Deploy")
            
        except Exception as e:
            return self._create_failure_result("Preview validation failed", str(e))
    
    async def _handle_finalconfirmation(self, node: QANode) -> Dict[str, Any]:
        """Handles the 'FinalConfirmationAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("🎯 Starting FINAL CONFIRMATION phase")
        
        try:
            self.context.current_phase = "final"
            selenium_functions = getattr(node, 'selenium_functions', [])
            if not selenium_functions:
                return self._create_failure_result("No selenium functions found in node", "Missing selenium_functions")
            
            final_result = {"functions_executed": [], "workflow_completed": True}
            
            for function_name in selenium_functions:
                step_result = await self._execute_selenium_function(function_name)
                if not step_result["success"]:
                    return self._create_failure_result(f"Function '{function_name}' failed", step_result["message"])
                
                final_result["functions_executed"].append({
                    "function": function_name, "result": step_result, "timestamp": datetime.now().isoformat()
                })
            
            self.outputs[node.id] = final_result
            return self._create_success_result("QA automation workflow completed successfully!", "Deploy")
            
        except Exception as e:
            return self._create_failure_result("Final confirmation failed", str(e))
    
    async def _handle_end(self, node: QANode) -> Dict[str, Any]:
        """
        Handles the 'EndAgent' node - Workflow completion
        """
        self.logger.info("🏁 Workflow completed successfully")
        
        # Generate final summary with access to all outputs
        summary = {
            "total_phases": len([k for k in self.outputs.keys() if k != "end_workflow"]),
            "executed_nodes": self.executed_nodes,
            "workflow_outputs": self.outputs,
            "completion_time": datetime.now().isoformat()
        }
        
        return {
            "phase": "End",
            "type": "completion",
            "message": "🎉 QA Automation completed! All phases validated successfully.",
            "summary": summary
        }
    
    async def _handle_default(self, node: QANode) -> Dict[str, Any]:
        """
        Default handler for unknown node types
        """
        return {
            "type": "error",
            "message": f"Handler for node type {node.type} not implemented yet"
        }
    
    # ==================== SELENIUM FUNCTION EXECUTION ====================
    
    async def _execute_selenium_function(self, function_name: str) -> Dict[str, Any]:
        """
        Execute selenium function directly
        
        Args:
            function_name: Name of the selenium function to execute
            
        Returns:
            Dict[str, Any]: Function execution result
        """
        try:
            # Get selenium method dynamically (like UNO's dynamic execution)
            if hasattr(self.selenium_core, function_name):
                selenium_method = getattr(self.selenium_core, function_name)
                
                # Execute selenium method
                if function_name in ["initialize_browser"]:
                    # Methods that return boolean
                    success = selenium_method()
                    message = f"{function_name} completed" if success else f"{function_name} failed"
                    return {"success": success, "message": message}
                else:
                    # Methods that return (success, message) tuple
                    success, message = selenium_method()
                    return {"success": success, "message": message}
            else:
                return {"success": False, "message": f"Selenium function '{function_name}' not found"}
                
        except Exception as e:
            return {"success": False, "message": f"Selenium function '{function_name}' failed: {e}"}
    

    

    

    
    # ==================== HELPER METHODS ====================
    
    def _create_success_result(self, message: str, next_phase: str) -> Dict[str, Any]:
        """Create success result dictionary"""
        return {
            "phase": self.context.current_phase,
            "type": "success",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "next_phase": next_phase,
            "workflow_outputs": self.outputs  # Include all outputs for coordination
        }
    
    def _create_failure_result(self, error_type: str, message: str) -> Dict[str, Any]:
        """Create failure result dictionary"""
        return {
            "phase": self.context.current_phase,
            "type": "error",
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "next_phase": None,  # Stop execution on failure
            "workflow_outputs": self.outputs
        }