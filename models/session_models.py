"""
QA Session Models - Pydantic models for session management
Similar to uno-mcp's AppObject but for QA automation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import time

class QASessionObject(BaseModel):
    """
    Main session object - equivalent to uno-mcp's AppObject
    Stores complete state for a QA automation session
    """
    
    # Core identifiers
    uuid: str = Field(description="Unique session identifier")
    test_name: str = Field(description="Name of the QA test")
    
    # Session metadata
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    current_phase: str = Field(default="authentication")
    current_step: int = Field(default=1)
    total_steps: int = Field(default=14)
    
    # Test execution state
    test_results: Dict[str, Any] = Field(default_factory=dict)
    screenshots: Dict[str, List[Dict]] = Field(default_factory=dict)
    errors: List[Dict] = Field(default_factory=list)
    phase_timings: Dict[str, Dict] = Field(default_factory=dict)
    
    # Browser and automation state
    browser_session: Optional[str] = None
    tab_session: Optional[str] = None
    selenium_state: Dict[str, Any] = Field(default_factory=dict)
    
    # Workflow outputs (similar to uno-mcp)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    workflow_state: Dict[str, Any] = Field(default_factory=dict)
    executed_nodes: List[str] = Field(default_factory=list)
    failed_nodes: List[str] = Field(default_factory=list)
    
    # File paths and directories
    results_dir: str = ""
    screenshots_dir: str = ""
    logs_dir: str = ""
    
    # Statistics
    token_count: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    
    # Configuration
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    project: Optional[str] = None
    authorization: Optional[str] = None
    
    # Session status
    status: str = Field(default="active")  # active, completed, failed, paused
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class QAMemoryItem(BaseModel):
    """
    Memory item for session persistence
    Similar to uno-mcp's MemoryItem
    """
    
    session_id: str = Field(description="Session UUID this memory belongs to")
    type: str = Field(default="qa_session", description="Type of memory item")
    
    # Test information
    test_name: str = ""
    test_results: Dict[str, Any] = Field(default_factory=dict)
    screenshots: Dict[str, List[Dict]] = Field(default_factory=dict)
    errors: List[Dict] = Field(default_factory=list)
    
    # Session metadata
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = Field(default=0.0)
    success_rate: float = Field(default=0.0)
    
    # Workflow information
    executed_nodes: List[str] = Field(default_factory=list)
    failed_nodes: List[str] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # File paths
    results_dir: str = ""
    screenshots_dir: str = ""
    logs_dir: str = ""
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Search and categorization
    tags: List[str] = Field(default_factory=list)
    query: Optional[str] = None
    
    # Configuration
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    project: Optional[str] = None
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class QASessionSummary(BaseModel):
    """
    Summary information for a QA session
    Used for listing and overview purposes
    """
    
    session_id: str
    test_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = Field(default=0.0)
    success_rate: float = Field(default=0.0)
    current_phase: str = ""
    total_steps: int = Field(default=0)
    completed_steps: int = Field(default=0)
    screenshots_count: int = Field(default=0)
    errors_count: int = Field(default=0)
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

def generate_session_uuid() -> str:
    """
    Generate session UUID similar to uno-mcp format
    Format: qa-session-{timestamp}-{uuid_hex}
    """
    timestamp = int(time.time())
    uuid_hex = uuid.uuid4().hex[:8]
    return f"qa-session-{timestamp}-{uuid_hex}"

def generate_browser_uuid() -> str:
    """
    Generate browser session UUID
    Format: browser-{uuid_hex}
    """
    uuid_hex = uuid.uuid4().hex[:6]
    return f"browser-{uuid_hex}"

def generate_test_run_uuid(session_uuid: str, run_number: int = 1) -> str:
    """
    Generate test run UUID within a session
    Format: test-{session_uuid}-{run_number}
    """
    return f"test-{session_uuid}-{run_number:03d}"