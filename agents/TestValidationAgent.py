from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime


class TestValidationAgent(BaseAgent):
    async def execute_agent(self, node: QANode):
        """Handles the 'TestValidationAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("---------------------------------------------------------------")
        self.logger.info("🧪 Starting TEST PLAN VALIDATION phase")
        
        try:
            self.context.current_phase = "test"
            
            # Get built-in selenium functions for this agent
            selenium_functions = ['validate_test_document']  # Built-in function for test validation
            
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