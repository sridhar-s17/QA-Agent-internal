from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime


class FinalConfirmationAgent(BaseAgent):
    async def execute_agent(self, node: QANode):
        """Handles the 'FinalConfirmationAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("---------------------------------------------------------------")
        self.logger.info("🎯 Starting FINAL CONFIRMATION phase")
        
        try:
            self.context.current_phase = "final"
            
            # Get built-in selenium functions for this agent
            selenium_functions = ['final_confirmation']  # Built-in function for final confirmation
            
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