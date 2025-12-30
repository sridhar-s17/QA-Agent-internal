"""
QA Agent Context - Manages test session state and data flow
Enhanced with hashmap-based session management similar to uno-mcp
"""

import uuid
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

class QAContext:
    """
    Manages QA test session context, storing test data, results, and session information.
    Enhanced with session manager integration for concurrent execution support.
    Similar to UNO's AgentContext but with hashmap-based session management.
    """
    
    def __init__(self, session_uuid: str = None, test_name: str = "", 
                 user_id: str = None, tenant_id: str = None, project: str = None):
        """
        Initialize QA context for a test session.
        
        Args:
            session_uuid (str): Existing session UUID to use (optional)
            test_name (str): Name of the test being executed
            user_id (str): User identifier
            tenant_id (str): Tenant identifier
            project (str): Project name
        """
        # Import here to avoid circular imports
        from core.session_manager import QASessionManager
        
        # Get or create session manager instance (singleton pattern)
        if not hasattr(QAContext, '_session_manager'):
            QAContext._session_manager = QASessionManager()
        
        self.session_manager = QAContext._session_manager
        
        # Create or get existing session
        if session_uuid:
            self.session_uuid = session_uuid
            self.session_object = self.session_manager.get_session(session_uuid)
        else:
            self.session_uuid = self.session_manager.create_session(
                test_name=test_name,
                user_id=user_id,
                tenant_id=tenant_id,
                project=project
            )
            self.session_object = self.session_manager.get_session(self.session_uuid)
        
        # Setup session logger
        from utils.session_logger import setup_session_logger
        self.logger = setup_session_logger(
            session_uuid=self.session_uuid,
            logs_dir=self.session_object.logs_dir,
            logger_name=f"QAContext.{self.session_uuid}"
        )
        
        # Legacy compatibility properties (delegate to session object)
        self._setup_legacy_properties()
    
    
    def _setup_legacy_properties(self):
        """Setup legacy property access for backward compatibility"""
        # Legacy properties that delegate to session object
        pass
    
    @property
    def session_id(self) -> str:
        """Legacy property for session_id (maps to session_uuid)"""
        return self.session_uuid
    
    @property
    def test_name(self) -> str:
        """Test name from session object"""
        return self.session_object.test_name
    
    @property
    def start_time(self) -> datetime:
        """Start time from session object"""
        return self.session_object.start_time
    
    @property
    def current_phase(self) -> str:
        """Current phase from session object"""
        return self.session_object.current_phase
    
    @current_phase.setter
    def current_phase(self, value: str):
        """Set current phase in session object"""
        self.session_object.current_phase = value
    
    @property
    def current_step(self) -> int:
        """Current step from session object"""
        return self.session_object.current_step
    
    @current_step.setter
    def current_step(self, value: int):
        """Set current step in session object"""
        self.session_object.current_step = value
    
    @property
    def total_steps(self) -> int:
        """Total steps from session object"""
        return self.session_object.total_steps
    
    @total_steps.setter
    def total_steps(self, value: int):
        """Set total steps in session object"""
        self.session_object.total_steps = value
    
    @property
    def test_results(self) -> Dict[str, Any]:
        """Test results from session object"""
        return self.session_object.test_results
    
    @property
    def screenshots(self) -> Dict[str, Any]:
        """Screenshots from session object"""
        return self.session_object.screenshots
    
    @property
    def errors(self) -> List[Dict]:
        """Errors from session object"""
        return self.session_object.errors
    
    @property
    def phase_timings(self) -> Dict[str, Dict]:
        """Phase timings from session object"""
        return self.session_object.phase_timings
    
    @property
    def browser_session(self) -> Optional[str]:
        """Browser session from session object"""
        return self.session_object.browser_session
    
    @browser_session.setter
    def browser_session(self, value: Optional[str]):
        """Set browser session in session object"""
        self.session_object.browser_session = value
    
    @property
    def tab_session(self) -> Optional[str]:
        """Tab session from session object"""
        return self.session_object.tab_session
    
    @tab_session.setter
    def tab_session(self, value: Optional[str]):
        """Set tab session in session object"""
        self.session_object.tab_session = value
    
    @property
    def outputs(self) -> Dict[str, Any]:
        """Outputs from session object"""
        return self.session_object.outputs
    
    @property
    def results_dir(self) -> str:
        """Results directory from session object"""
        return self.session_object.results_dir
    
    @property
    def screenshots_dir(self) -> str:
        """Screenshots directory from session object"""
        return self.session_object.screenshots_dir
    
    @property
    def logs_dir(self) -> str:
        """Logs directory from session object"""
        return self.session_object.logs_dir
    
    def _setup_results_directory(self):
        """Legacy method - now handled by session manager"""
        # Directory setup is now handled by session manager
        # This method is kept for backward compatibility
        pass
    
    
    def start_phase(self, phase_name: str):
        """Mark the start of a test phase"""
        self.current_phase = phase_name
        if phase_name not in self.phase_timings:
            self.phase_timings[phase_name] = {}
        self.phase_timings[phase_name]["start"] = datetime.now()
        
        # Log phase start
        self.logger.info(f"🔄 Starting phase: {phase_name}")
    
    def end_phase(self, phase_name: str, success: bool = True):
        """Mark the end of a test phase"""
        if phase_name in self.phase_timings:
            self.phase_timings[phase_name]["end"] = datetime.now()
            self.phase_timings[phase_name]["success"] = success
            
            # Calculate duration
            start_time = self.phase_timings[phase_name]["start"]
            end_time = self.phase_timings[phase_name]["end"]
            duration = (end_time - start_time).total_seconds()
            self.phase_timings[phase_name]["duration_seconds"] = duration
            
            # Log phase completion
            status = "✅ Completed" if success else "❌ Failed"
            self.logger.info(f"{status} phase: {phase_name} ({duration:.2f}s)")
    
    def add_screenshot(self, phase: str, screenshot_path: str, description: str = ""):
        """Add screenshot information with phase organization"""
        if phase not in self.screenshots:
            self.screenshots[phase] = []
        
        # Extract relative path for better readability in results
        try:
            relative_path = os.path.relpath(screenshot_path, self.results_dir)
        except:
            relative_path = screenshot_path
        
        screenshot_info = {
            "path": screenshot_path,
            "relative_path": relative_path,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "filename": os.path.basename(screenshot_path)
        }
        
        self.screenshots[phase].append(screenshot_info)
        
        # Log screenshot capture
        self.logger.info(f"📸 Screenshot captured for {phase}: {os.path.basename(screenshot_path)}")
    
    def get_screenshots_by_phase(self, phase: str) -> list:
        """Get all screenshots for a specific phase"""
        return self.screenshots.get(phase, [])
    
    def get_all_phases_with_screenshots(self) -> list:
        """Get list of all phases that have screenshots"""
        return list(self.screenshots.keys())
    
    def get_screenshot_summary(self) -> Dict[str, Any]:
        """Get summary of screenshots organized by phase"""
        summary = {}
        for phase, screenshots in self.screenshots.items():
            summary[phase] = {
                "count": len(screenshots),
                "files": [shot["filename"] for shot in screenshots],
                "descriptions": [shot["description"] for shot in screenshots]
            }
        return summary
    
    def add_error(self, phase: str, error_message: str, screenshot_path: str = None):
        """Add error information"""
        error_info = {
            "phase": phase,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "screenshot": screenshot_path
        }
        self.errors.append(error_info)
        
        # Log error
        self.logger.error(f"❌ Error in {phase}: {error_message}")
    
    def set_browser_session(self, session_id: str, tab_id: str = None):
        """Set browser session information"""
        self.browser_session = session_id
        self.tab_session = tab_id or f"tab_{datetime.now().strftime('%H%M%S')}"
        
        # Log browser session info
        self.logger.info(f"🌐 Browser session: {session_id}, Tab: {self.tab_session}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get comprehensive test summary with screenshot organization"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate success rate
        successful_phases = sum(1 for phase_data in self.phase_timings.values() 
                              if phase_data.get("success", False))
        total_phases = len(self.phase_timings)
        success_rate = (successful_phases / total_phases * 100) if total_phases > 0 else 0
        
        # Update session object success rate
        self.session_object.success_rate = success_rate
        
        summary = {
            "session_id": self.session_uuid,
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_seconds": total_duration,
            "current_phase": self.current_phase,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "success_rate": success_rate,
            "successful_phases": successful_phases,
            "total_phases": total_phases,
            "errors_count": len(self.errors),
            "screenshots_count": sum(len(shots) for shots in self.screenshots.values()),
            "screenshots_by_phase": self.get_screenshot_summary(),
            "browser_session": self.browser_session,
            "tab_session": self.tab_session,
            "results_dir": self.results_dir,
            "screenshots_dir": self.screenshots_dir,
            "logs_dir": self.logs_dir
        }
        
        return summary
    
    def save_results(self):
        """Save test results to JSON file and session memory"""
        try:
            # Save to local JSON file (legacy compatibility)
            results_file = os.path.join(self.results_dir, "test_results.json")
            
            results_data = {
                "summary": self.get_test_summary(),
                "phase_timings": self.phase_timings,
                "screenshots": self.screenshots,
                "errors": self.errors,
                "outputs": self.outputs,
                "test_results": self.test_results
            }
            
            # Custom JSON encoder to handle datetime objects
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False, default=json_serializer)
            
            # Save to session memory
            self.session_manager.save_session(self.session_uuid)
            
            self.logger.info(f"💾 Results saved to: {results_file}")
            return results_file
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise
    
    def cleanup_session(self, save_to_memory: bool = True):
        """Cleanup session resources"""
        try:
            if save_to_memory:
                self.save_results()
            
            # Update session status
            self.session_manager.update_session_status(self.session_uuid, "completed")
            
            # Optionally cleanup from active sessions
            # self.session_manager.cleanup_session(self.session_uuid, save_to_memory=False)
            
            self.logger.info(f"🧹 Session cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during session cleanup: {e}")
    
    def resume_session(self) -> bool:
        """
        Resume session from memory if it exists
        
        Returns:
            bool: True if session was resumed, False if starting fresh
        """
        try:
            # Check if session exists in memory
            session_data = self.session_manager.memory.load_session(self.session_uuid)
            
            if session_data:
                self.logger.info(f"🔄 Resuming session from memory: {self.session_uuid}")
                return True
            else:
                self.logger.info(f"🆕 Starting fresh session: {self.session_uuid}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error resuming session: {e}")
            return False