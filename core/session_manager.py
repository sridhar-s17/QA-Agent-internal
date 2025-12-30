"""
QA Session Manager - Central hashmap-based session management
Similar to uno-mcp's app_context.py but for QA automation
"""

from typing import Dict, Optional, List, Any
from models.session_models import QASessionObject, QAMemoryItem, QASessionSummary, generate_session_uuid
from core.memory import QAMemoryManager
import logging
from datetime import datetime
import os
from pathlib import Path

class QASessionManager:
    """
    Central session manager using hashmap for O(1) session access.
    Manages multiple concurrent QA automation sessions.
    Similar to uno-mcp's Context class.
    """
    
    def __init__(self, memory_dir: str = "memory", results_base_dir: str = "results"):
        """
        Initialize QA Session Manager
        
        Args:
            memory_dir (str): Directory for memory storage
            results_base_dir (str): Base directory for test results
        """
        # Core hashmap: UUID -> QASessionObject (similar to uno-mcp's self.objects)
        self.sessions: Dict[str, QASessionObject] = {}
        
        # Memory management
        self.memory = QAMemoryManager(memory_dir=memory_dir)
        self.memory_trace: List[QAMemoryItem] = []
        
        # Configuration
        self.results_base_dir = results_base_dir
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.QASessionManager")
        
        # Ensure base directories exist
        Path(results_base_dir).mkdir(parents=True, exist_ok=True)
        
        self.logger.info("QA Session Manager initialized")
    
    def create_session(self, test_name: str = None, session_uuid: str = None, 
                      user_id: str = None, tenant_id: str = None, project: str = None) -> str:
        """
        Create new session and return UUID
        Similar to uno-mcp's add_initial method
        
        Args:
            test_name (str): Name of the test
            session_uuid (str): Specific UUID to use (optional)
            user_id (str): User identifier
            tenant_id (str): Tenant identifier  
            project (str): Project name
            
        Returns:
            str: Session UUID
        """
        try:
            # Generate UUID if not provided
            if not session_uuid:
                session_uuid = generate_session_uuid()
            
            # Generate test name if not provided
            if not test_name:
                test_name = f"qa_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Setup directory structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = os.path.join(self.results_base_dir, f"{test_name}_{timestamp}")
            screenshots_dir = os.path.join(results_dir, "screenshots")
            logs_dir = os.path.join(results_dir, "logs")
            
            # Create directories
            Path(results_dir).mkdir(parents=True, exist_ok=True)
            Path(screenshots_dir).mkdir(parents=True, exist_ok=True)
            Path(logs_dir).mkdir(parents=True, exist_ok=True)
            
            # Create session object
            session_object = QASessionObject(
                uuid=session_uuid,
                test_name=test_name,
                user_id=user_id,
                tenant_id=tenant_id,
                project=project,
                results_dir=results_dir,
                screenshots_dir=screenshots_dir,
                logs_dir=logs_dir,
                status="active"
            )
            
            # Store in hashmap (O(1) operation)
            self.sessions[session_uuid] = session_object
            
            self.logger.info(f"Created session: {session_uuid} - {test_name}")
            return session_uuid
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            raise
    
    def get_session(self, session_uuid: str) -> QASessionObject:
        """
        Get session by UUID (O(1) lookup)
        Similar to uno-mcp's get_object method
        
        Args:
            session_uuid (str): Session UUID
            
        Returns:
            QASessionObject: Session object
        """
        try:
            # Check if session exists in hashmap (O(1))
            if session_uuid in self.sessions:
                return self.sessions[session_uuid]
            
            # Try to load from memory if not in active sessions
            session_data = self.memory.load_session(session_uuid)
            if session_data:
                # Restore session object from memory
                session_object = self._create_session_from_memory(session_data)
                self.sessions[session_uuid] = session_object
                self.logger.info(f"Restored session from memory: {session_uuid}")
                return session_object
            
            # Create new session if not found
            self.logger.warning(f"Session {session_uuid} not found, creating new session")
            new_uuid = self.create_session(session_uuid=session_uuid)
            return self.sessions[new_uuid]
            
        except Exception as e:
            self.logger.error(f"Error getting session {session_uuid}: {e}")
            raise
    
    def add_session_data(self, session_uuid: str, key: str, value: Any):
        """
        Add data to specific session
        Similar to uno-mcp's add_object_data method
        
        Args:
            session_uuid (str): Session UUID
            key (str): Data key
            value (Any): Data value
        """
        try:
            session = self.get_session(session_uuid)
            
            # Use setattr for dynamic attribute setting (like uno-mcp)
            if hasattr(session, key):
                setattr(session, key, value)
            else:
                # Store in outputs dict for custom data
                session.outputs[key] = value
            
            self.logger.debug(f"Added data to session {session_uuid}: {key}")
            
        except Exception as e:
            self.logger.error(f"Error adding data to session {session_uuid}: {e}")
            raise
    
    def get_session_data(self, session_uuid: str, key: str) -> Any:
        """
        Get data from specific session
        Similar to uno-mcp's get_object_data method
        
        Args:
            session_uuid (str): Session UUID
            key (str): Data key
            
        Returns:
            Any: Data value or None if not found
        """
        try:
            if session_uuid in self.sessions:
                session = self.sessions[session_uuid]
                
                # Check if it's a direct attribute
                if hasattr(session, key):
                    return getattr(session, key)
                
                # Check in outputs dict
                return session.outputs.get(key)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting data from session {session_uuid}: {e}")
            return None
    
    def update_session_status(self, session_uuid: str, status: str):
        """
        Update session status
        
        Args:
            session_uuid (str): Session UUID
            status (str): New status (active, completed, failed, paused)
        """
        try:
            session = self.get_session(session_uuid)
            session.status = status
            
            if status in ["completed", "failed"]:
                session.end_time = datetime.now()
            
            self.logger.info(f"Updated session {session_uuid} status to: {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating session status: {e}")
    
    def list_active_sessions(self) -> List[str]:
        """
        List all active session UUIDs
        
        Returns:
            List[str]: List of active session UUIDs
        """
        try:
            return list(self.sessions.keys())
        except Exception as e:
            self.logger.error(f"Error listing active sessions: {e}")
            return []
    
    def get_session_summary(self, session_uuid: str) -> Optional[QASessionSummary]:
        """
        Get session summary information
        
        Args:
            session_uuid (str): Session UUID
            
        Returns:
            Optional[QASessionSummary]: Session summary or None
        """
        try:
            session = self.get_session(session_uuid)
            
            # Calculate duration
            duration = 0.0
            if session.start_time:
                end_time = session.end_time or datetime.now()
                duration = (end_time - session.start_time).total_seconds()
            
            # Calculate completed steps
            completed_steps = len(session.executed_nodes)
            
            # Count screenshots
            screenshots_count = sum(len(shots) for shots in session.screenshots.values())
            
            summary = QASessionSummary(
                session_id=session.uuid,
                test_name=session.test_name,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                duration_seconds=duration,
                success_rate=session.success_rate,
                current_phase=session.current_phase,
                total_steps=session.total_steps,
                completed_steps=completed_steps,
                screenshots_count=screenshots_count,
                errors_count=len(session.errors)
            )
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting session summary for {session_uuid}: {e}")
            return None
    
    def list_all_sessions(self, limit: int = 50) -> List[QASessionSummary]:
        """
        List all sessions (active and historical) with summaries
        
        Args:
            limit (int): Maximum number of sessions to return
            
        Returns:
            List[QASessionSummary]: List of session summaries
        """
        try:
            summaries = []
            
            # Add active sessions
            for session_uuid in self.sessions.keys():
                summary = self.get_session_summary(session_uuid)
                if summary:
                    summaries.append(summary)
            
            # Add historical sessions from memory
            memory_sessions = self.memory.list_sessions(limit=limit)
            for session_data in memory_sessions:
                # Skip if already in active sessions
                if session_data["session_id"] not in self.sessions:
                    summary = QASessionSummary(
                        session_id=session_data["session_id"],
                        test_name=session_data["test_name"],
                        status="completed",  # Historical sessions are completed
                        start_time=datetime.fromisoformat(session_data["start_time"]) if session_data["start_time"] else datetime.now(),
                        end_time=datetime.fromisoformat(session_data["end_time"]) if session_data["end_time"] else None,
                        duration_seconds=session_data["duration_seconds"],
                        success_rate=session_data["success_rate"],
                        completed_steps=session_data["executed_nodes"],
                        screenshots_count=session_data["screenshots_count"],
                        errors_count=session_data["errors_count"]
                    )
                    summaries.append(summary)
            
            # Sort by start time (most recent first)
            summaries.sort(key=lambda x: x.start_time, reverse=True)
            
            return summaries[:limit]
            
        except Exception as e:
            self.logger.error(f"Error listing all sessions: {e}")
            return []
    
    def save_session(self, session_uuid: str):
        """
        Save session to persistent memory
        Similar to uno-mcp's add_memory_item method
        
        Args:
            session_uuid (str): Session UUID to save
        """
        try:
            if session_uuid in self.sessions:
                session = self.sessions[session_uuid]
                self.memory.save_session(session)
                self.logger.info(f"Saved session to memory: {session_uuid}")
            else:
                self.logger.warning(f"Session {session_uuid} not found for saving")
                
        except Exception as e:
            self.logger.error(f"Error saving session {session_uuid}: {e}")
            raise
    
    def cleanup_session(self, session_uuid: str, save_to_memory: bool = True):
        """
        Cleanup specific session
        
        Args:
            session_uuid (str): Session UUID to cleanup
            save_to_memory (bool): Whether to save to memory before cleanup
        """
        try:
            if session_uuid in self.sessions:
                # Save to memory if requested
                if save_to_memory:
                    self.save_session(session_uuid)
                
                # Remove from active sessions hashmap
                del self.sessions[session_uuid]
                
                self.logger.info(f"Cleaned up session: {session_uuid}")
            else:
                self.logger.warning(f"Session {session_uuid} not found for cleanup")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up session {session_uuid}: {e}")
    
    def cleanup_old_sessions(self, max_active_sessions: int = 10):
        """
        Cleanup old active sessions to manage memory
        
        Args:
            max_active_sessions (int): Maximum number of active sessions to keep
        """
        try:
            if len(self.sessions) <= max_active_sessions:
                return
            
            # Sort sessions by start time (oldest first)
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].start_time
            )
            
            # Cleanup oldest sessions
            sessions_to_cleanup = len(self.sessions) - max_active_sessions
            for i in range(sessions_to_cleanup):
                session_uuid, _ = sorted_sessions[i]
                self.cleanup_session(session_uuid, save_to_memory=True)
            
            self.logger.info(f"Cleaned up {sessions_to_cleanup} old sessions")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
    
    def _create_session_from_memory(self, session_data: Dict) -> QASessionObject:
        """
        Create session object from memory data
        Similar to uno-mcp's create_obj_from_memory method
        
        Args:
            session_data (Dict): Session data from memory
            
        Returns:
            QASessionObject: Restored session object
        """
        try:
            # Convert datetime strings back to datetime objects
            start_time = session_data.get("start_time")
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            
            end_time = session_data.get("end_time")
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            session_object = QASessionObject(
                uuid=session_data["uuid"],
                test_name=session_data.get("test_name", ""),
                start_time=start_time or datetime.now(),
                end_time=end_time,
                test_results=session_data.get("test_results", {}),
                screenshots=session_data.get("screenshots", {}),
                errors=session_data.get("errors", []),
                success_rate=session_data.get("success_rate", 0.0),
                executed_nodes=session_data.get("executed_nodes", []),
                failed_nodes=session_data.get("failed_nodes", []),
                outputs=session_data.get("outputs", {}),
                results_dir=session_data.get("results_dir", ""),
                screenshots_dir=session_data.get("screenshots_dir", ""),
                logs_dir=session_data.get("logs_dir", ""),
                tenant_id=session_data.get("tenant_id"),
                user_id=session_data.get("user_id"),
                project=session_data.get("project"),
                status="restored"  # Mark as restored from memory
            )
            
            return session_object
            
        except Exception as e:
            self.logger.error(f"Error creating session from memory: {e}")
            raise
    
    def get_session_count(self) -> Dict[str, int]:
        """
        Get session count statistics
        
        Returns:
            Dict[str, int]: Session count statistics
        """
        try:
            active_count = len(self.sessions)
            total_count = active_count + len(self.memory.items)
            
            return {
                "active_sessions": active_count,
                "total_sessions": total_count,
                "memory_sessions": len(self.memory.items)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session count: {e}")
            return {"active_sessions": 0, "total_sessions": 0, "memory_sessions": 0}