from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime


class BuildProcessAgent(BaseAgent):
    async def execute_agent(self, node: QANode):
        """Handles the 'BuildProcessAgent' node - Gets selenium functions from node and executes them directly"""
        self.logger.info("---------------------------------------------------------------")
        self.logger.info("🔨 Starting BUILD PROCESS phase")
        
        try:
            self.context.current_phase = "build"
            
            # Get built-in selenium functions for this agent
            selenium_functions = ['monitor_build_process']  # Built-in function for build process
            
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
