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
    Dynamic client for executing QA automation workflow with session management.
    Uses hashmap-based session management for concurrent execution support.
    """
    
    def __init__(self, session_uuid: str = None, user_id: str = None, 
                 tenant_id: str = None, project: str = None):
        """
        Initialize QA Client with optional session management
        
        Args:
            session_uuid (str): Existing session UUID to use (optional)
            user_id (str): User identifier
            tenant_id (str): Tenant identifier
            project (str): Project name
        """
        self.session_uuid = session_uuid
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.project = project
        self.setup_logging()
        self.logger = logging.getLogger(f"{__name__}.QAClient")
        
    def setup_logging(self):
        """Setup initial console logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                # Initial log file - will be updated later
                logging.FileHandler('master_agent.log', encoding='utf-8')
            ]
        )
    
    def update_logging_for_context(self, context):
        """Update logging to use context's logs directory"""
        # Remove existing file handler
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                root_logger.removeHandler(handler)
                handler.close()
        
        # Add new file handler with context path
        log_file_path = os.path.join(context.logs_dir, 'master_agent.log')
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(file_handler)
        
        self.logger.info(f"📝 Updated master log file to: {log_file_path}")
        return log_file_path
    
    async def run_qa_test(self, test_name: str = None) -> Dict[str, Any]:
        """Run QA automation test with session management"""
        self.logger.info("🚀 QA Agent Client Starting (Session-Aware)")
        self.logger.info("📋 Hashmap Session Management Mode")
        self.logger.info("="*60)
        
        # Create session-aware context
        if not test_name:
            test_name = f"qa_automation_"
        
        context = QAContext(
            session_uuid=self.session_uuid,
            test_name=test_name,
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            project=self.project
        )
        
        # Update logging to use context's session-specific logs
        self.update_logging_for_context(context)
        
        self.logger.info(f"📋 Test Name: {test_name}")
        self.logger.info(f"🆔 Session UUID: {context.session_uuid}")
        self.logger.info(f"📁 Results Directory: {context.results_dir}")
        self.logger.info(f"📁 Logs Directory: {context.logs_dir}")
        
        # Check if resuming existing session
        is_resumed = context.resume_session()
        if is_resumed:
            self.logger.info("🔄 Resuming existing session")
        else:
            self.logger.info("🆕 Starting new session")
        
        try:
            # Create workflow with session-aware context
            workflow = QAWorkflow(context=context)
            
            # Display session and graph info
            session_summary = context.session_manager.get_session_summary(context.session_uuid)
            if session_summary:
                self.logger.info(f"📊 Session Status: {session_summary.status}")
                self.logger.info(f"📈 Current Success Rate: {session_summary.success_rate:.1f}%")
            
            graph_summary = workflow.graph.get_workflow_summary()
            self.logger.info(f"📊 Static Graph: {graph_summary['total_nodes']} nodes, {graph_summary['total_edges']} edges")
            
            # Get start node
            start_node = workflow.graph.get_start_node()
            start_node_id = start_node.id
            self.logger.info(f"🎯 Starting from node: {start_node_id}")
            
            # Execute workflow
            self.logger.info("🔄 Starting workflow execution...")
            result = await workflow.execute_workflow(start_node_id)
            
            # Display results
            self._display_results(result, context)
            return result
            
        except Exception as e:
            error_msg = f"QA test execution failed: {e}"
            self.logger.error(error_msg)
            
            # Update session status on error
            if 'context' in locals():
                context.session_manager.update_session_status(context.session_uuid, "failed")
            
            return {"success": False, "message": error_msg}
    

    

    
    def _display_results(self, result: Dict[str, Any], context: QAContext):
        """Display test results in a formatted way with session information"""
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
        self.logger.info(f"🆔 Session UUID: {context.session_uuid}")
        
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
        
        # Display session management info
        session_summary = context.session_manager.get_session_summary(context.session_uuid)
        if session_summary:
            self.logger.info(f"📊 Session Status: {session_summary.status}")
            self.logger.info(f"🕐 Session Duration: {session_summary.duration_seconds:.1f}s")
        
        self.logger.info("="*60)

def main():
    """Main function for QA automation with session management"""
    print("🤖 QA Agent - Automated Testing Framework")
    print("📋 Hashmap Session Management")
    print("=" * 60)
    
    # Create client with optional session management
    client = QAClient()
    
    try:
        print(f"📋 Using session-aware QA execution")
        
        # Run QA workflow
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