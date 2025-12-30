"""
QA Memory Manager - Session-based memory persistence
Similar to uno-mcp's memory.py but for QA sessions
"""

from typing import List, Dict, Any, Optional
from models.session_models import QAMemoryItem, QASessionObject
import json
import os
from datetime import datetime
import logging
from pathlib import Path

class QAMemoryManager:
    """
    Manages persistent storage and retrieval of QA session data
    Provides session-based memory management similar to uno-mcp
    """
    
    def __init__(self, memory_dir: str = "memory", s3_config: Dict = None):
        """
        Initialize QA Memory Manager
        
        Args:
            memory_dir (str): Directory for local memory storage
            s3_config (Dict): S3 configuration for cloud storage (optional)
        """
        self.memory_dir = memory_dir
        self.s3_config = s3_config
        self.items: List[QAMemoryItem] = []
        self.logger = logging.getLogger(f"{__name__}.QAMemoryManager")
        
        # Create memory directory if it doesn't exist
        Path(self.memory_dir).mkdir(parents=True, exist_ok=True)
        
        # Load existing memory items
        self.load_all_memories()
    
    def add_session_memory(self, session_object: QASessionObject) -> QAMemoryItem:
        """
        Add memory item for specific session
        
        Args:
            session_object (QASessionObject): Session object to store in memory
            
        Returns:
            QAMemoryItem: Created memory item
        """
        try:
            # Create memory item from session object
            memory_item = QAMemoryItem(
                session_id=session_object.uuid,
                test_name=session_object.test_name,
                test_results=session_object.test_results,
                screenshots=session_object.screenshots,
                errors=session_object.errors,
                start_time=session_object.start_time,
                end_time=session_object.end_time,
                success_rate=session_object.success_rate,
                executed_nodes=session_object.executed_nodes,
                failed_nodes=session_object.failed_nodes,
                outputs=session_object.outputs,
                results_dir=session_object.results_dir,
                screenshots_dir=session_object.screenshots_dir,
                logs_dir=session_object.logs_dir,
                tenant_id=session_object.tenant_id,
                user_id=session_object.user_id,
                project=session_object.project,
                tags=[session_object.current_phase, session_object.test_name],
                updated_at=datetime.now()
            )
            
            # Add to in-memory list
            self.items.append(memory_item)
            
            # Save to persistent storage
            self._save_memory_item(memory_item)
            
            self.logger.info(f"Added memory for session: {session_object.uuid}")
            return memory_item
            
        except Exception as e:
            self.logger.error(f"Error adding session memory: {e}")
            raise
    
    def get_session_memory(self, session_uuid: str) -> Optional[QAMemoryItem]:
        """
        Get memory for specific session
        
        Args:
            session_uuid (str): Session UUID to retrieve
            
        Returns:
            Optional[QAMemoryItem]: Memory item if found, None otherwise
        """
        try:
            # First check in-memory items
            for item in self.items:
                if item.session_id == session_uuid:
                    return item
            
            # If not in memory, try to load from storage
            memory_item = self._load_memory_item(session_uuid)
            if memory_item:
                self.items.append(memory_item)
                return memory_item
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting session memory for {session_uuid}: {e}")
            return None
    
    def search_session_memory(self, session_uuid: str = None, query: str = None, 
                            tags: List[str] = None, limit: int = 10) -> List[QAMemoryItem]:
        """
        Search memory items with various filters
        
        Args:
            session_uuid (str): Filter by specific session
            query (str): Search in test names and results
            tags (List[str]): Filter by tags
            limit (int): Maximum number of results
            
        Returns:
            List[QAMemoryItem]: Matching memory items
        """
        try:
            results = []
            
            for item in self.items:
                # Filter by session if specified
                if session_uuid and item.session_id != session_uuid:
                    continue
                
                # Filter by tags if specified
                if tags and not any(tag in item.tags for tag in tags):
                    continue
                
                # Search in text fields if query specified
                if query:
                    search_text = f"{item.test_name} {item.session_id}".lower()
                    if query.lower() not in search_text:
                        continue
                
                results.append(item)
                
                # Limit results
                if len(results) >= limit:
                    break
            
            # Sort by updated_at (most recent first)
            results.sort(key=lambda x: x.updated_at, reverse=True)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching session memory: {e}")
            return []
    
    def save_session(self, session_object: QASessionObject):
        """
        Save session data to persistent storage
        
        Args:
            session_object (QASessionObject): Session to save
        """
        try:
            # Update existing memory item or create new one
            existing_memory = self.get_session_memory(session_object.uuid)
            
            if existing_memory:
                # Update existing memory item
                existing_memory.test_results = session_object.test_results
                existing_memory.screenshots = session_object.screenshots
                existing_memory.errors = session_object.errors
                existing_memory.end_time = session_object.end_time
                existing_memory.success_rate = session_object.success_rate
                existing_memory.executed_nodes = session_object.executed_nodes
                existing_memory.failed_nodes = session_object.failed_nodes
                existing_memory.outputs = session_object.outputs
                existing_memory.updated_at = datetime.now()
                
                self._save_memory_item(existing_memory)
            else:
                # Create new memory item
                self.add_session_memory(session_object)
            
            self.logger.info(f"Saved session: {session_object.uuid}")
            
        except Exception as e:
            self.logger.error(f"Error saving session {session_object.uuid}: {e}")
            raise
    
    def load_session(self, session_uuid: str) -> Optional[Dict]:
        """
        Load session data from persistent storage
        
        Args:
            session_uuid (str): Session UUID to load
            
        Returns:
            Optional[Dict]: Session data if found, None otherwise
        """
        try:
            memory_item = self.get_session_memory(session_uuid)
            
            if memory_item:
                # Convert memory item back to session data format
                session_data = {
                    "uuid": memory_item.session_id,
                    "test_name": memory_item.test_name,
                    "test_results": memory_item.test_results,
                    "screenshots": memory_item.screenshots,
                    "errors": memory_item.errors,
                    "start_time": memory_item.start_time,
                    "end_time": memory_item.end_time,
                    "success_rate": memory_item.success_rate,
                    "executed_nodes": memory_item.executed_nodes,
                    "failed_nodes": memory_item.failed_nodes,
                    "outputs": memory_item.outputs,
                    "results_dir": memory_item.results_dir,
                    "screenshots_dir": memory_item.screenshots_dir,
                    "logs_dir": memory_item.logs_dir,
                    "tenant_id": memory_item.tenant_id,
                    "user_id": memory_item.user_id,
                    "project": memory_item.project
                }
                
                return session_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading session {session_uuid}: {e}")
            return None
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all sessions with summary information
        
        Args:
            limit (int): Maximum number of sessions to return
            
        Returns:
            List[Dict[str, Any]]: List of session summaries
        """
        try:
            summaries = []
            
            for item in self.items[:limit]:
                duration = 0
                if item.start_time and item.end_time:
                    duration = (item.end_time - item.start_time).total_seconds()
                
                summary = {
                    "session_id": item.session_id,
                    "test_name": item.test_name,
                    "start_time": item.start_time.isoformat() if item.start_time else None,
                    "end_time": item.end_time.isoformat() if item.end_time else None,
                    "duration_seconds": duration,
                    "success_rate": item.success_rate,
                    "executed_nodes": len(item.executed_nodes),
                    "failed_nodes": len(item.failed_nodes),
                    "screenshots_count": sum(len(shots) for shots in item.screenshots.values()),
                    "errors_count": len(item.errors),
                    "tags": item.tags
                }
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            self.logger.error(f"Error listing sessions: {e}")
            return []
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """
        Cleanup old session memories
        
        Args:
            days_old (int): Remove sessions older than this many days
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            removed_count = 0
            self.items = [
                item for item in self.items 
                if item.created_at > cutoff_date
            ]
            
            # Also remove from storage
            for filename in os.listdir(self.memory_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.memory_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        removed_count += 1
            
            self.logger.info(f"Cleaned up {removed_count} old session memories")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
    
    def _save_memory_item(self, memory_item: QAMemoryItem):
        """Save memory item to persistent storage"""
        try:
            filename = f"{memory_item.session_id}.json"
            filepath = os.path.join(self.memory_dir, filename)
            
            # Convert to dict and handle datetime serialization
            data = memory_item.model_dump()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
        except Exception as e:
            self.logger.error(f"Error saving memory item to {filepath}: {e}")
            raise
    
    def _load_memory_item(self, session_uuid: str) -> Optional[QAMemoryItem]:
        """Load memory item from persistent storage"""
        try:
            filename = f"{session_uuid}.json"
            filepath = os.path.join(self.memory_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return QAMemoryItem(**data)
            
        except Exception as e:
            self.logger.error(f"Error loading memory item from {filepath}: {e}")
            return None
    
    def load_all_memories(self):
        """Load all memory items from storage"""
        try:
            if not os.path.exists(self.memory_dir):
                return
            
            for filename in os.listdir(self.memory_dir):
                if filename.endswith('.json'):
                    session_uuid = filename[:-5]  # Remove .json extension
                    memory_item = self._load_memory_item(session_uuid)
                    if memory_item and memory_item not in self.items:
                        self.items.append(memory_item)
            
            # Sort by created_at (most recent first)
            self.items.sort(key=lambda x: x.created_at, reverse=True)
            
            self.logger.info(f"Loaded {len(self.items)} memory items from storage")
            
        except Exception as e:
            self.logger.error(f"Error loading all memories: {e}")