from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime


class WireframesValidationAgent(BaseAgent):
    async def execute_agent(self, node: QANode):
        """
        Handles the 'WireframesValidationAgent' node - Phase 4: WIREFRAMES VALIDATION
        Gets selenium functions from node and executes them directly
        """
        self.logger.info("---------------------------------------------------------------")
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