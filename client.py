"""
QA Agent Client - Direct client for running QA automation workflow
No FastAPI needed - direct execution approach
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
from typing import Dict, Any
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.context import QAContext
from core.workflow import QAWorkflow
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QAClient:
    """
    Direct client for executing QA automation workflow.
    Provides a simple interface to run the complete test suite.
    """
    
    def __init__(self):
        """Initialize QA Client"""
        self.setup_logging()
        self.logger = logging.getLogger(f"{__name__}.QAClient")
        
    def setup_logging(self):
        """Setup console logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    async def run_qa_test(self, test_name: str = "", start_phase: str = "authentication") -> Dict[str, Any]:
        """
        Run QA automation test.
        
        Args:
            test_name (str): Name for the test session
            start_phase (str): Phase to start from (default: authentication)
            
        Returns:
            Dict: Test execution results
        """
        self.logger.info("🚀 QA Agent Client Starting")
        self.logger.info("="*60)
        
        # Create test context
        if not test_name:
            test_name = f"qa_automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        context = QAContext(test_name)
        self.logger.info(f"📋 Test Name: {test_name}")
        self.logger.info(f"🆔 Session ID: {context.session_id}")
        self.logger.info(f"📁 Results Directory: {context.results_dir}")
        
        try:
            # Create and execute workflow
            workflow = QAWorkflow(context)
            
            # Display workflow information
            workflow_info = workflow.get_workflow_info()
            self.logger.info(f"📊 Total Nodes: {workflow_info['total_nodes']}")
            self.logger.info(f"🎯 Starting Phase: {start_phase}")
            
            # Execute workflow
            self.logger.info("🔄 Starting workflow execution...")
            
            # Map phase names to node IDs
            phase_to_node = {
                "authentication": "authentication_1",
                "requirements": "requirements_2", 
                "discovery": "discovery_validation_3",
                "wireframes": "wireframes_validation_4",
                "design": "design_validation_5",
                "build": "build_process_6",
                "test": "test_validation_7",
                "preview": "preview_app_8",
                "final": "final_confirmation_9"
            }
            
            start_node_id = phase_to_node.get(start_phase, start_phase)
            self.logger.info(f"🎯 Starting from node: {start_node_id}")
            
            result = await workflow.execute_workflow(start_node_id)
            
            # Display results
            self._display_results(result)
            
            return result
            
        except Exception as e:
            error_msg = f"QA test execution failed: {e}"
            self.logger.error(error_msg)
            context.add_error("client", error_msg)
            
            return {
                "success": False,
                "message": error_msg,
                "context_summary": context.get_test_summary()
            }
    
    def _display_results(self, result: Dict[str, any]):
        """Display test results in a formatted way"""
        self.logger.info("="*60)
        self.logger.info("📊 QA TEST RESULTS")
        self.logger.info("="*60)
        
        success = result.get("success", False)
        message = result.get("message", "No message")
        
        if success:
            self.logger.info("✅ TEST STATUS: PASSED")
        else:
            self.logger.error("❌ TEST STATUS: FAILED")
        
        self.logger.info(f"📝 Message: {message}")
        
        # Display execution details
        executed_phases = result.get("executed_phases", [])
        failed_phases = result.get("failed_phases", [])
        total_phases = result.get("total_phases", 0)
        success_rate = result.get("success_rate", 0)
        
        self.logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        self.logger.info(f"✅ Completed Phases: {len(executed_phases)}/{total_phases}")
        
        if executed_phases:
            self.logger.info(f"📋 Executed: {', '.join(executed_phases)}")
        
        if failed_phases:
            self.logger.error(f"❌ Failed: {', '.join(failed_phases)}")
        
        # Display timing information
        duration = result.get("duration_seconds", 0)
        self.logger.info(f"⏱️ Total Duration: {duration:.1f} seconds")
        
        # Display context summary
        context_summary = result.get("context_summary", {})
        if context_summary:
            results_dir = context_summary.get("results_dir", "")
            screenshots_count = context_summary.get("screenshots_count", 0)
            errors_count = context_summary.get("errors_count", 0)
            
            self.logger.info(f"📁 Results Directory: {results_dir}")
            self.logger.info(f"📸 Screenshots Captured: {screenshots_count}")
            self.logger.info(f"⚠️ Errors Encountered: {errors_count}")
        
        self.logger.info("="*60)

def main():
    """Main entry point for QA Client"""
    print("🤖 QA Agent - Automated Testing Framework")
    print("=" * 50)
    
    # Parse command line arguments (simple approach)
    test_name = ""
    start_phase = "authentication"
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
    if len(sys.argv) > 2:
        start_phase = sys.argv[2]
    
    # Create and run client
    client = QAClient()
    
    try:
        # Run the test
        result = asyncio.run(client.run_qa_test(test_name, start_phase))
        
        # Exit with appropriate code
        exit_code = 0 if result.get("success", False) else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()