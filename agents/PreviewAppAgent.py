from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime


class PreviewAppAgent(BaseAgent):
    async def execute_agent(self, node: QANode):
        """Handles the 'PreviewAppAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("---------------------------------------------------------------")
        self.logger.info("👀 Starting PREVIEW APP phase")
        
        try:
            self.context.current_phase = "preview"
            
            # Get built-in selenium functions for this agent
            selenium_functions = ['validate_app_preview']  # Built-in function for app preview
            
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