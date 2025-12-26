from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime


class DiscoveryValidationAgent(BaseAgent):
    async def execute_agent(self, node: QANode):
        """
        Handles the 'DiscoveryValidationAgent' node - Phase 3: DISCOVERY DOCUMENT VALIDATION
        Gets selenium functions from node and executes them directly
        """
        self.logger.info("---------------------------------------------------------------")
        self.logger.info("📄 Starting DISCOVERY DOCUMENT VALIDATION phase")
        
        try:
            # Access previous results for coordination
            auth_output = self.outputs.get("authentication_1", {})
            requirements_output = self.outputs.get("requirements_2", {})
            
            # Update context
            self.context.current_phase = "discovery"
            
            # Get built-in selenium functions for this agent
            selenium_functions = ['validate_discovery_document']  # Built-in function for discovery validation
            
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
