from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime


class RequirementsGatheringAgent(BaseAgent):
    async def execute_agent(self,node:QANode):
        self.logger.info("---------------------------------------------------------------")
        self.logger.info("📋 Starting REQUIREMENTS GATHERING phase")
        
        try:
            # Access previous agent results for coordination
            auth_output = self.outputs.get("authentication_1", {})
            self.logger.info(f"Previous auth result: {auth_output}")
            
            # Update context
            self.context.current_phase = "requirements"
            
            # Get built-in selenium functions for this agent
            selenium_functions = ['answer_all_questions']  # Built-in function for requirements gathering
            
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