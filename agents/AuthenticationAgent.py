from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime

class AuthenticationAgent(BaseAgent):
    async def execute_agent(self,node:QANode):
        self.logger.info("---------------------------------------------------------------")
        self.logger.info(f"🚀 Starting AUTHENTICATION & SETUP phase")
        
        try:
            # Update context
            self.context.current_phase = "authentication"
            
            # Get selenium functions from node
            selenium_functions = ['execute_authentication_phase']            
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
