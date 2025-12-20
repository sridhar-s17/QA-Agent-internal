
from abc import ABC,abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os

class BaseAgent(ABC):
    def __init__(self, selenium_instance,context,outputs,task,name):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set logger level
        self.logger.propagate = False
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Use context's logs directory for the log file
        log_file_path = os.path.join(context.logs_dir, 'agents_activity.log')
        
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)  # Set handler level
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)  # Set handler level
        
        # Prevent adding multiple handlers if you create the agent twice
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
        # Log the initialization with new path
        self.logger.info(f"🚀 {self.__class__.__name__} initialized - Log file: {log_file_path}")
        
        self.task = task
        self.selenium = selenium_instance
        self.name=name
        self.context=context
        self.outputs=outputs
        
        # Set the logger for selenium instance to use BaseAgent's logger
        if hasattr(self.selenium, 'set_logger'):
            self.selenium.set_logger(self.logger)

    async def _execute_selenium_function(self, function_name: str) -> Dict[str, Any]:
        """
        Execute selenium function directly using BaseAgent's logger
        
        Args:
            function_name: Name of the selenium function to execute
            
        Returns:
            Dict[str, Any]: Function execution result
        """
        try:
            # Set the logger for selenium instance if not already set
            if hasattr(self.selenium, 'logger') and self.selenium.logger != self.logger:
                self.selenium.logger = self.logger
            
            # Get selenium method dynamically (like UNO's dynamic execution)
            if hasattr(self.selenium, function_name):
                selenium_method = getattr(self.selenium, function_name)
                success, message = selenium_method()
                return {"success": success, "message": message}
            else:
                return {"success": False, "message": f"Selenium function '{function_name}' not found"}
                
        except Exception as e:
            return {"success": False, "message": f"Selenium function '{function_name}' failed: {e}"}

    def _create_failure_result(self, error_type: str, message: str) -> Dict[str, Any]:
        """Create failure result dictionary"""
        return {
            "phase": self.context.current_phase,
            "type": "error",
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "next_phase": None,  # Stop execution on failure
            "workflow_outputs": self.outputs
        }
    def _create_success_result(self, message: str, next_phase: str) -> Dict[str, Any]:
        """Create success result dictionary"""
        return {
            "phase": self.context.current_phase,
            "type": "success",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "next_phase": next_phase,
            "workflow_outputs": self.outputs  # Include all outputs for coordination
        }

    def test_logging(self):
        """Test method to verify logging is working correctly"""
        self.logger.info("🧪 Testing agent logging - this should appear in both console and results/logs/agents_activity.log")
        self.logger.warning("⚠️ Testing warning level logging")
        self.logger.error("❌ Testing error level logging")
        
        # Check if log file exists and is writable
        log_file_path = os.path.join(self.context.logs_dir, 'agents_activity.log')
        
        if os.path.exists(log_file_path):
            self.logger.info(f"✅ Log file exists at: {log_file_path}")
            try:
                with open(log_file_path, 'a') as f:
                    f.write(f"# Test write at {datetime.now().isoformat()}\n")
                self.logger.info("✅ Log file is writable")
            except Exception as e:
                self.logger.error(f"❌ Log file write test failed: {e}")
        else:
            self.logger.error(f"❌ Log file does not exist at: {log_file_path}")

    @abstractmethod
    async def execute_agent(self, node):
        pass

