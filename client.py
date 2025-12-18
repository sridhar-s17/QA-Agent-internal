"""
QA Agent Client - Dynamic client using QAGraph and QAWorkflow capabilities
Leverages existing graph methods instead of static mappings
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
from typing import Dict, Any
from datetime import datetime

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
    Dynamic client for executing QA automation workflow.
    Uses existing QAGraph and QAWorkflow capabilities for flexible execution.
    """
    
    def __init__(self):
        """Initialize QA Client"""
        self.setup_logging()
        self.logger = logging.getLogger(f"{__name__}.QAClient")
        
        # Create a single workflow instance for graph operations
        # This is lightweight since it only loads the graph structure
        self._graph_context = QAContext("graph_operations")
        self._workflow = QAWorkflow(self._graph_context)
        
    def setup_logging(self):
        """Setup console logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    async def run_qa_test(self, test_name: str = "", start_phase: str = None) -> Dict[str, Any]:
        """
        Run QA automation test - Simple and direct approach.
        
        Args:
            test_name (str): Name for the test session
            start_phase (str): Phase to start from (uses graph.get_start_node() if None)
            
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
        self.logger.info(f"� Ressults Directory: {context.results_dir}")
        
        try:
            # Create workflow
            workflow = QAWorkflow(context)
            start_node = workflow.graph.get_start_node()
            start_node_id = start_node.id
            self.logger.info(f"🎯 Starting from default node: {start_node_id}")
            
            # Execute workflow - that's it!
            self.logger.info("🔄 Starting workflow execution...")
            result = await workflow.execute_workflow(start_node_id)
            
            # Display results
            self._display_results(result)
            return result
            
        except Exception as e:
            error_msg = f"QA test execution failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "message": error_msg}
    

    

    
    def _display_results(self, result: Dict[str, Any]):
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
        executed_nodes = result.get("executed_nodes", [])
        failed_nodes = result.get("failed_nodes", [])
        total_nodes = result.get("total_nodes", 0)
        success_rate = result.get("success_rate", 0)
        
        self.logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        self.logger.info(f"✅ Completed Nodes: {len(executed_nodes)}/{total_nodes}")
        
        if executed_nodes:
            self.logger.info(f"📋 Executed: {', '.join(executed_nodes)}")
        
        if failed_nodes:
            self.logger.error(f"❌ Failed: {', '.join(failed_nodes)}")
        
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
    """Simple main function - just run the QA test"""
    print("🤖 QA Agent - Automated Testing Framework")
    print("=" * 50)
    
    # Create client
    client = QAClient()
    
    try:
        # Run full QA workflow - simple!
        result = asyncio.run(client.run_qa_test())
        
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