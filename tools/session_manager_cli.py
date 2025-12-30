#!/usr/bin/env python3
"""
Session Manager CLI - Command line tool for managing QA sessions
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.session_manager import QASessionManager
from models.session_models import generate_session_uuid

def list_sessions(args):
    """List all sessions"""
    session_manager = QASessionManager()
    
    if args.active_only:
        sessions = session_manager.list_active_sessions()
        print(f"📋 Active Sessions ({len(sessions)}):")
        for session_uuid in sessions:
            summary = session_manager.get_session_summary(session_uuid)
            if summary:
                print(f"  🆔 {session_uuid}")
                print(f"     📝 {summary.test_name}")
                print(f"     📊 Status: {summary.status}")
                print(f"     📈 Success Rate: {summary.success_rate:.1f}%")
                print()
    else:
        summaries = session_manager.list_all_sessions(limit=args.limit)
        print(f"📋 All Sessions ({len(summaries)}):")
        for summary in summaries:
            status_icon = "✅" if summary.status == "completed" else "🔄" if summary.status == "running" else "❌"
            print(f"  {status_icon} {summary.session_id}")
            print(f"     📝 {summary.test_name}")
            print(f"     📊 Status: {summary.status}")
            print(f"     📈 Success Rate: {summary.success_rate:.1f}%")
            print(f"     🕐 Duration: {summary.duration_seconds:.1f}s")
            print()

def show_session(args):
    """Show detailed session information"""
    session_manager = QASessionManager()
    
    try:
        session = session_manager.get_session(args.session_uuid)
        summary = session_manager.get_session_summary(args.session_uuid)
        
        print(f"📋 Session Details: {args.session_uuid}")
        print("=" * 60)
        print(f"📝 Test Name: {session.test_name}")
        print(f"📊 Status: {session.status}")
        print(f"🕐 Start Time: {session.start_time}")
        print(f"🕐 End Time: {session.end_time or 'Running'}")
        print(f"📈 Success Rate: {session.success_rate:.1f}%")
        print(f"📁 Results Dir: {session.results_dir}")
        print(f"📸 Screenshots: {sum(len(shots) for shots in session.screenshots.values())}")
        print(f"❌ Errors: {len(session.errors)}")
        print(f"✅ Executed Nodes: {len(session.executed_nodes)}")
        print(f"❌ Failed Nodes: {len(session.failed_nodes)}")
        
        if args.verbose:
            print("\n📋 Executed Nodes:")
            for node in session.executed_nodes:
                print(f"  ✅ {node}")
            
            if session.failed_nodes:
                print("\n❌ Failed Nodes:")
                for node in session.failed_nodes:
                    print(f"  ❌ {node}")
            
            if session.errors:
                print("\n⚠️ Errors:")
                for error in session.errors[-5:]:  # Show last 5 errors
                    print(f"  📅 {error.get('timestamp', 'Unknown')}")
                    print(f"  📝 {error.get('message', 'No message')}")
                    print()
        
    except Exception as e:
        print(f"❌ Error retrieving session: {e}")

def cleanup_sessions(args):
    """Cleanup old sessions"""
    session_manager = QASessionManager()
    
    if args.confirm or input("⚠️ This will cleanup old sessions. Continue? (y/N): ").lower() == 'y':
        try:
            # Cleanup old active sessions
            session_manager.cleanup_old_sessions(max_active_sessions=args.max_active)
            
            # Cleanup old memory
            session_manager.memory.cleanup_old_sessions(days_old=args.days_old)
            
            print(f"✅ Cleanup completed")
            print(f"📊 Max active sessions: {args.max_active}")
            print(f"🗑️ Removed sessions older than {args.days_old} days")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    else:
        print("❌ Cleanup cancelled")

def create_session(args):
    """Create a new session"""
    session_manager = QASessionManager()
    
    try:
        session_uuid = session_manager.create_session(
            test_name=args.test_name,
            user_id=args.user_id,
            tenant_id=args.tenant_id,
            project=args.project
        )
        
        print(f"✅ Created new session: {session_uuid}")
        print(f"📝 Test Name: {args.test_name}")
        
        if args.show_details:
            show_session(type('Args', (), {'session_uuid': session_uuid, 'verbose': False})())
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")

def export_session(args):
    """Export session data to JSON"""
    session_manager = QASessionManager()
    
    try:
        session = session_manager.get_session(args.session_uuid)
        
        # Convert to dict for JSON serialization
        session_data = session.model_dump()
        
        # Handle datetime serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        
        output_file = args.output or f"{args.session_uuid}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False, default=json_serializer)
        
        print(f"✅ Session exported to: {output_file}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")

def show_stats(args):
    """Show session statistics"""
    session_manager = QASessionManager()
    
    try:
        stats = session_manager.get_session_count()
        summaries = session_manager.list_all_sessions(limit=100)
        
        print("📊 QA Session Statistics")
        print("=" * 40)
        print(f"🔄 Active Sessions: {stats['active_sessions']}")
        print(f"💾 Memory Sessions: {stats['memory_sessions']}")
        print(f"📋 Total Sessions: {stats['total_sessions']}")
        
        if summaries:
            # Calculate success rate
            completed_sessions = [s for s in summaries if s.status == "completed"]
            if completed_sessions:
                avg_success_rate = sum(s.success_rate for s in completed_sessions) / len(completed_sessions)
                avg_duration = sum(s.duration_seconds for s in completed_sessions) / len(completed_sessions)
                
                print(f"📈 Average Success Rate: {avg_success_rate:.1f}%")
                print(f"⏱️ Average Duration: {avg_duration:.1f}s")
            
            # Status breakdown
            status_counts = {}
            for summary in summaries:
                status_counts[summary.status] = status_counts.get(summary.status, 0) + 1
            
            print("\n📊 Status Breakdown:")
            for status, count in status_counts.items():
                icon = "✅" if status == "completed" else "🔄" if status == "running" else "❌"
                print(f"  {icon} {status.title()}: {count}")
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="QA Session Manager CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List sessions command
    list_parser = subparsers.add_parser('list', help='List sessions')
    list_parser.add_argument('--active-only', action='store_true', help='Show only active sessions')
    list_parser.add_argument('--limit', type=int, default=20, help='Maximum number of sessions to show')
    
    # Show session command
    show_parser = subparsers.add_parser('show', help='Show session details')
    show_parser.add_argument('session_uuid', help='Session UUID to show')
    show_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    
    # Create session command
    create_parser = subparsers.add_parser('create', help='Create new session')
    create_parser.add_argument('--test-name', default='cli_created_test', help='Test name')
    create_parser.add_argument('--user-id', help='User ID')
    create_parser.add_argument('--tenant-id', help='Tenant ID')
    create_parser.add_argument('--project', help='Project name')
    create_parser.add_argument('--show-details', action='store_true', help='Show session details after creation')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old sessions')
    cleanup_parser.add_argument('--max-active', type=int, default=10, help='Maximum active sessions to keep')
    cleanup_parser.add_argument('--days-old', type=int, default=30, help='Remove sessions older than N days')
    cleanup_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export session to JSON')
    export_parser.add_argument('session_uuid', help='Session UUID to export')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show session statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    commands = {
        'list': list_sessions,
        'show': show_session,
        'create': create_session,
        'cleanup': cleanup_sessions,
        'export': export_session,
        'stats': show_stats
    }
    
    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\n⚠️ Operation interrupted")
    except Exception as e:
        print(f"❌ Command failed: {e}")

if __name__ == "__main__":
    main()