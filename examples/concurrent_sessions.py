#!/usr/bin/env python3
"""
Example: Concurrent QA Sessions
Demonstrates running multiple QA automation sessions simultaneously
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from client import QAClient

async def run_concurrent_sessions():
    """Run multiple QA sessions concurrently"""
    
    print("🚀 Starting Concurrent QA Sessions Demo")
    print("=" * 60)
    
    # Create multiple clients for different test scenarios
    clients = [
        QAClient(user_id="user1", project="authentication_tests"),
        QAClient(user_id="user2", project="workflow_tests"),
        QAClient(user_id="user3", project="regression_tests")
    ]
    
    # Define test scenarios
    test_scenarios = [
        "authentication_flow_test",
        "complete_workflow_test", 
        "regression_validation_test"
    ]
    
    print(f"📋 Running {len(clients)} concurrent sessions:")
    for i, scenario in enumerate(test_scenarios):
        print(f"  Session {i+1}: {scenario}")
    
    print("\n🔄 Starting concurrent execution...")
    
    # Create tasks for concurrent execution
    tasks = []
    for i, (client, scenario) in enumerate(zip(clients, test_scenarios)):
        task = asyncio.create_task(
            client.run_qa_test(test_name=scenario),
            name=f"Session-{i+1}-{scenario}"
        )
        tasks.append(task)
    
    # Wait for all sessions to complete
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 CONCURRENT SESSIONS RESULTS")
        print("=" * 60)
        
        success_count = 0
        for i, (result, scenario) in enumerate(zip(results, test_scenarios)):
            if isinstance(result, Exception):
                print(f"❌ Session {i+1} ({scenario}): FAILED - {result}")
            elif result.get("success", False):
                print(f"✅ Session {i+1} ({scenario}): PASSED")
                success_count += 1
            else:
                print(f"❌ Session {i+1} ({scenario}): FAILED - {result.get('message', 'Unknown error')}")
        
        print(f"\n📈 Overall Success Rate: {success_count}/{len(tasks)} ({success_count/len(tasks)*100:.1f}%)")
        
        return success_count == len(tasks)
        
    except Exception as e:
        print(f"\n💥 Concurrent execution failed: {e}")
        return False

async def run_session_resumption_demo():
    """Demonstrate session resumption capability"""
    
    print("\n🔄 Session Resumption Demo")
    print("=" * 40)
    
    # Start a session
    client1 = QAClient(user_id="demo_user", project="resumption_test")
    
    print("🆕 Starting initial session...")
    try:
        # This might fail or be interrupted
        result1 = await client1.run_qa_test("resumption_demo_test")
        session_uuid = result1.get("context_summary", {}).get("session_id")
        
        if session_uuid:
            print(f"📋 Session UUID: {session_uuid}")
            
            # Create new client with same session UUID
            print("🔄 Resuming session with new client...")
            client2 = QAClient(session_uuid=session_uuid)
            result2 = await client2.run_qa_test()
            
            print("✅ Session resumption demo completed")
            return result2.get("success", False)
        else:
            print("⚠️ Could not extract session UUID")
            return False
            
    except Exception as e:
        print(f"❌ Session resumption demo failed: {e}")
        return False

async def main():
    """Main demo function"""
    
    print("🤖 QA Agent - Session Management Demo")
    print("🔗 Hashmap-based Concurrent Execution")
    print("=" * 60)
    
    try:
        # Run concurrent sessions demo
        concurrent_success = await run_concurrent_sessions()
        
        # Run session resumption demo
        resumption_success = await run_session_resumption_demo()
        
        # Overall result
        overall_success = concurrent_success and resumption_success
        
        print("\n" + "=" * 60)
        print("🏁 DEMO SUMMARY")
        print("=" * 60)
        print(f"🔄 Concurrent Sessions: {'✅ PASSED' if concurrent_success else '❌ FAILED'}")
        print(f"🔄 Session Resumption: {'✅ PASSED' if resumption_success else '❌ FAILED'}")
        print(f"🎯 Overall Demo: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
        
        return overall_success
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted")
        sys.exit(130)