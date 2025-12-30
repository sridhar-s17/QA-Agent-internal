# QA Agent Session Management

## Overview

QA-Agent-internal now includes hashmap-based session management similar to uno-mcp, enabling concurrent execution of multiple QA automation sessions with complete isolation and O(1) performance.

## Key Features

### 🔗 Hashmap-Based Architecture
- **O(1) Session Access**: Direct UUID lookup for instant session retrieval
- **Concurrent Execution**: Multiple QA tests can run simultaneously without interference
- **Session Isolation**: Each session maintains independent state and resources
- **Memory Efficiency**: Only active sessions stored in RAM, historical data in persistent storage

### 🆔 UUID-Based Session Management
- **Session UUID Format**: `qa-session-{timestamp}-{uuid_hex}`
- **Browser UUID Format**: `browser-{uuid_hex}`
- **Test Run UUID Format**: `test-{session_uuid}-{run_number}`

### 💾 Persistent Memory
- **Session Persistence**: Sessions can be saved and resumed
- **Historical Data**: Access to previous test results and analytics
- **Cross-Session Learning**: Analyze patterns across multiple test runs
- **Automatic Cleanup**: Configurable cleanup of old sessions

## Architecture

### Core Components

```
QA-Agent-internal/
├── core/
│   ├── session_manager.py     # Central hashmap session management
│   ├── memory.py              # Session memory persistence
│   └── context.py             # Enhanced session-aware context
├── models/
│   └── session_models.py      # Session-related Pydantic models
├── utils/
│   └── session_logger.py      # Session-specific logging
├── tools/
│   └── session_manager_cli.py # CLI for session management
└── examples/
    └── concurrent_sessions.py  # Concurrent execution examples
```

### Session Object Structure

```python
class QASessionObject(BaseModel):
    uuid: str                           # Unique session identifier
    test_name: str                      # Test name
    test_results: Dict[str, Any]        # Test execution results
    screenshots: Dict[str, List[Dict]]  # Screenshots by phase
    outputs: Dict[str, Any]             # Workflow outputs
    executed_nodes: List[str]           # Completed workflow nodes
    failed_nodes: List[str]             # Failed workflow nodes
    browser_session: Optional[str]      # Browser instance ID
    results_dir: str                    # Results directory path
    status: str                         # Session status
```

## Usage Examples

### Basic Session Usage

```python
from client import QAClient

# Create client (automatically gets new session)
client = QAClient()
result = await client.run_qa_test("my_test")
```

### Concurrent Sessions

```python
import asyncio
from client import QAClient

# Create multiple clients for concurrent execution
clients = [
    QAClient(user_id="user1", project="auth_tests"),
    QAClient(user_id="user2", project="workflow_tests"),
    QAClient(user_id="user3", project="regression_tests")
]

# Run concurrently
tasks = [
    client.run_qa_test(f"test_{i}")
    for i, client in enumerate(clients)
]

results = await asyncio.gather(*tasks)
```

### Session Resumption

```python
# Start a session
client1 = QAClient()
result1 = await client1.run_qa_test("long_running_test")
session_uuid = result1["context_summary"]["session_id"]

# Resume the same session later
client2 = QAClient(session_uuid=session_uuid)
result2 = await client2.run_qa_test()  # Continues from where it left off
```

### Session Management

```python
from core.session_manager import QASessionManager

# Get session manager
session_manager = QASessionManager()

# List active sessions
active_sessions = session_manager.list_active_sessions()

# Get session details
session = session_manager.get_session(session_uuid)

# Save session to memory
session_manager.save_session(session_uuid)

# Cleanup old sessions
session_manager.cleanup_old_sessions(max_active_sessions=10)
```

## CLI Tools

### Session Manager CLI

```bash
# List all sessions
python tools/session_manager_cli.py list

# Show session details
python tools/session_manager_cli.py show qa-session-1703123456-a1b2c3d4

# Create new session
python tools/session_manager_cli.py create --test-name "my_test" --user-id "user1"

# Show statistics
python tools/session_manager_cli.py stats

# Cleanup old sessions
python tools/session_manager_cli.py cleanup --max-active 10 --days-old 30

# Export session data
python tools/session_manager_cli.py export qa-session-1703123456-a1b2c3d4 --output session.json
```

### Concurrent Sessions Demo

```bash
# Run concurrent sessions example
python examples/concurrent_sessions.py
```

## Configuration

### Environment Variables

```bash
# Results directory (default: "results")
QA_RESULTS_DIR=results

# Memory directory (default: "memory")
QA_MEMORY_DIR=memory

# Maximum active sessions (default: 10)
QA_MAX_ACTIVE_SESSIONS=10
```

### Session Manager Configuration

```python
# Initialize with custom settings
session_manager = QASessionManager(
    memory_dir="custom_memory",
    results_base_dir="custom_results"
)
```

## Benefits

### Performance
- **O(1) Operations**: Session lookup, creation, and updates
- **Memory Efficient**: Only active sessions in RAM
- **Scalable**: Handles hundreds of concurrent sessions

### Reliability
- **Session Isolation**: No interference between concurrent tests
- **Fault Tolerance**: Individual session failures don't affect others
- **Data Persistence**: Sessions survive system restarts

### Maintainability
- **Clean Architecture**: Clear separation of concerns
- **Type Safety**: Pydantic models with validation
- **Comprehensive Logging**: Session-specific log files

### Scalability
- **Horizontal Scaling**: Easy to distribute across machines
- **Multi-Tenant**: Support for multiple users/projects
- **Resource Management**: Automatic cleanup and optimization

## Migration from Legacy System

### Backward Compatibility

The new session management system maintains backward compatibility with existing code:

```python
# Legacy usage still works
context = QAContext("test_name")
context.session_id  # Still available (maps to session_uuid)
context.test_results  # Still available (delegates to session object)
```

### Migration Steps

1. **Existing Code**: No changes required for basic usage
2. **Enhanced Features**: Opt-in to session management features
3. **Concurrent Execution**: Use new QAClient with session parameters
4. **Session Management**: Use CLI tools for advanced session operations

## Monitoring and Analytics

### Session Statistics

```python
# Get session counts
stats = session_manager.get_session_count()
print(f"Active: {stats['active_sessions']}")
print(f"Total: {stats['total_sessions']}")

# Get session summaries
summaries = session_manager.list_all_sessions(limit=50)
for summary in summaries:
    print(f"{summary.session_id}: {summary.success_rate:.1f}%")
```

### Log Analysis

```python
from utils.session_logger import get_session_logs

# Get logs for specific session
logs = get_session_logs(session_uuid, logs_dir, lines=100)
print(logs)
```

## Troubleshooting

### Common Issues

1. **Session Not Found**
   ```python
   # Check if session exists in memory
   session_data = session_manager.memory.load_session(session_uuid)
   ```

2. **Memory Usage**
   ```python
   # Cleanup old sessions
   session_manager.cleanup_old_sessions(max_active_sessions=5)
   ```

3. **Concurrent Access**
   ```python
   # Sessions are thread-safe, but use different session UUIDs for different tests
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("QASessionManager").setLevel(logging.DEBUG)
```

## Future Enhancements

- **Distributed Sessions**: Redis-based session storage for multi-machine deployment
- **Real-time Monitoring**: WebSocket-based session monitoring dashboard
- **Advanced Analytics**: ML-based test failure prediction
- **Session Templates**: Predefined session configurations for common test scenarios
- **API Integration**: REST API for external session management

## Support

For issues or questions about session management:

1. Check the logs in `results/{test_name}_{timestamp}/logs/`
2. Use the CLI tools for session inspection
3. Review session statistics for patterns
4. Enable debug logging for detailed information