#!/usr/bin/env python3
"""
QA Agent Runner - Simple script to run QA automation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from client import QAClient

async def main():
    """Run QA automation with simple interface"""
    
    print("🤖 QA Agent - Phase 1: AUTHENTICATION & SETUP")
    print("=" * 60)
    print("This will test:")
    print("  Step 1: Browser initialization and login")
    print("  Step 2: Select default prompt")
    print("=" * 60)
    
    # Get test name from user
    test_name = input("Enter test name (or press Enter for auto-generated): ").strip()
    if not test_name:
        test_name = ""
    
    print(f"\n🚀 Starting QA test: {test_name or 'auto-generated'}")
    print("⚠️ Make sure Chrome browser is available and Studio_Automation folder is accessible")
    
    # Create and run client
    client = QAClient()
    
    try:
        result = await client.run_qa_test(test_name, "authentication")        
        return result.get("success", False)
        
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(130)