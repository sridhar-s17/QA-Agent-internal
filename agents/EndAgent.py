from agents.agent import BaseAgent
from models.qa_models import QANode
from datetime import datetime


class EndAgent(BaseAgent):
    async def execute_agent(self, node: QANode):
        """
        Handles the 'EndAgent' node - Workflow completion
        """
        self.logger.info("---------------------------------------------------------------")
        self.logger.info("🏁 Workflow completed successfully")
        
        # Generate final summary with access to all outputs
        summary = {
            "total_phases": len([k for k in self.outputs.keys() if k != "end_workflow"]),
            "executed_nodes": getattr(self.context, 'executed_nodes', []),
            "workflow_outputs": self.outputs,
            "completion_time": datetime.now().isoformat()
        }
        
        return {
            "phase": "End",
            "type": "success",
            "message": "🎉 QA Automation completed! All phases validated successfully.",
            "summary": summary
        }