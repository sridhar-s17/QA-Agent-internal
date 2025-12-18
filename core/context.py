"""
QA Agent Context - Manages test session state and data flow
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

class QAContext:
    """
    Manages QA test session context, storing test data, results, and session information.
    Similar to UNO's AgentContext but focused on QA automation.
    """
    
    def __init__(self, test_name: str = ""):
        """
        Initialize QA context for a test session.
        
        Args:
            test_name (str): Name of the test being executed
        """
        self.session_id: str = str(uuid.uuid4())
        self.test_name: str = test_name or f"qa_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time: datetime = datetime.now()
        
        # Test execution state
        self.current_phase: str = "authentication"
        self.current_step: int = 1
        self.total_steps: int = 14
        
        # Test results storage
        self.test_results: Dict[str, Any] = {}
        self.screenshots: Dict[str, str] = {}  # phase -> screenshot_path
        self.errors: list = []
        self.phase_timings: Dict[str, Dict[str, datetime]] = {}
        
        # Browser session info
        self.browser_session: Optional[str] = None
        self.tab_session: Optional[str] = None
        
        # Agent outputs (similar to UNO's workflow outputs)
        self.outputs: Dict[str, Any] = {}
        
        # Setup results directory
        self._setup_results_directory()
    
    def _setup_results_directory(self):
        """Setup directory structure for test results"""
        base_dir = os.getenv("QA_RESULTS_DIR", "results")
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        self.results_dir = os.path.join(base_dir, f"{self.test_name}_{timestamp}")
        self.screenshots_dir = os.path.join(self.results_dir, "screenshots")
        self.logs_dir = os.path.join(self.results_dir, "logs")
        
        # Create directories
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def start_phase(self, phase_name: str):
        """Mark the start of a test phase"""
        self.current_phase = phase_name
        if phase_name not in self.phase_timings:
            self.phase_timings[phase_name] = {}
        self.phase_timings[phase_name]["start"] = datetime.now()
    
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
    
    def add_screenshot(self, phase: str, screenshot_path: str, description: str = ""):
        """Add screenshot information"""
        if phase not in self.screenshots:
            self.screenshots[phase] = []
        
        self.screenshots[phase].append({
            "path": screenshot_path,
            "timestamp": datetime.now().isoformat(),
            "description": description
        })
    
    def add_error(self, phase: str, error_message: str, screenshot_path: str = None):
        """Add error information"""
        error_info = {
            "phase": phase,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "screenshot": screenshot_path
        }
        self.errors.append(error_info)
    
    def set_browser_session(self, session_id: str, tab_id: str = None):
        """Set browser session information"""
        self.browser_session = session_id
        self.tab_session = tab_id or f"tab_{datetime.now().strftime('%H%M%S')}"
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get comprehensive test summary"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate success rate
        successful_phases = sum(1 for phase_data in self.phase_timings.values() 
                              if phase_data.get("success", False))
        total_phases = len(self.phase_timings)
        success_rate = (successful_phases / total_phases * 100) if total_phases > 0 else 0
        
        return {
            "session_id": self.session_id,
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
            "browser_session": self.browser_session,
            "tab_session": self.tab_session,
            "results_dir": self.results_dir
        }
    
    def save_results(self):
        """Save test results to JSON file"""
        results_file = os.path.join(self.results_dir, "test_results.json")
        
        results_data = {
            "summary": self.get_test_summary(),
            "phase_timings": self.phase_timings,
            "screenshots": self.screenshots,
            "errors": self.errors,
            "outputs": self.outputs,
            "test_results": self.test_results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        return results_file