#!/usr/bin/env python3
"""
Quick start script to enable debugging system in OmicsOracle.

This script:
1. Registers debug routes in main.py
2. Adds basic tracing to workflow routes
3. Tests the debug dashboard

Usage:
    python enable_debugging.py
"""

import sys
from pathlib import Path


def check_files_exist():
    """Check if tracing files were created."""
    files_needed = [
        "omics_oracle_v2/tracing/__init__.py",
        "omics_oracle_v2/api/routes/debug.py"
    ]
    
    missing = []
    for file in files_needed:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print("❌ Missing required files:")
        for file in missing:
            print(f"   - {file}")
        return False
    
    print("✅ All tracing files exist")
    return True


def show_integration_steps():
    """Show steps to integrate the debugging system."""
    print("\n" + "=" * 70)
    print("🔍 DEBUGGING SYSTEM INTEGRATION GUIDE")
    print("=" * 70)
    
    print("\n📋 Step 1: Register Debug Routes")
    print("-" * 70)
    print("File: omics_oracle_v2/api/main.py")
    print("\nAdd this import:")
    print("    from omics_oracle_v2.api.routes.debug import router as debug_router")
    print("\nAdd this route registration:")
    print("    app.include_router(debug_router, tags=['Debug'])")
    
    print("\n📋 Step 2: Add Tracing to Workflow Routes")
    print("-" * 70)
    print("File: omics_oracle_v2/api/routes/workflows_dev.py")
    print("\nAdd these imports:")
    print("    from omics_oracle_v2.tracing import RequestTracer, TraceContext")
    print("\nIn execute_workflow function, add:")
    print("""
    # Start trace
    trace_id = RequestTracer.start_trace(
        query=request.query,
        workflow_type=request.workflow_type,
        user_id="dev_user"
    )
    
    try:
        with TraceContext(trace_id, "API", "execute_workflow"):
            result = orchestrator.execute(orchestrator_input)
        
        # Complete trace
        output = result.output
        RequestTracer.complete_trace(
            trace_id,
            success=result.success,
            datasets_found=output.total_datasets_found,
            datasets_analyzed=output.total_datasets_analyzed,
            report_generated=bool(output.final_report)
        )
        
        # Add trace_id to response
        response["trace_id"] = trace_id
        
    except Exception as e:
        RequestTracer.complete_trace(trace_id, success=False, error_message=str(e))
        raise
    """)
    
    print("\n📋 Step 3: Add Tracing to Orchestrator")
    print("-" * 70)
    print("File: omics_oracle_v2/agents/orchestrator.py")
    print("\nAdd to execute method:")
    print("""
    from omics_oracle_v2.tracing import TraceContext
    
    def execute(self, input_data, trace_id=None):
        with TraceContext(trace_id, "Orchestrator", "execute_workflow"):
            # existing code
            pass
    """)
    
    print("\n📋 Step 4: Add Tracing to Each Agent")
    print("-" * 70)
    print("Files: omics_oracle_v2/agents/query_agent.py, search_agent.py, etc.")
    print("\nAdd to execute method:")
    print("""
    def execute(self, input_data, trace_id=None):
        with TraceContext(trace_id, self.__class__.__name__, "execute"):
            # existing code
            pass
    """)
    
    print("\n📋 Step 5: Restart Server")
    print("-" * 70)
    print("    ./start_dev_server.sh")
    
    print("\n📋 Step 6: Access Debug Dashboard")
    print("-" * 70)
    print("    http://localhost:8000/debug/dashboard")
    
    print("\n" + "=" * 70)
    print("📚 Full documentation: DEBUGGING_SYSTEM_GUIDE.md")
    print("=" * 70)
    print()


def show_quick_test():
    """Show how to quickly test the system."""
    print("\n🧪 QUICK TEST")
    print("=" * 70)
    print("\n1. After integration, run a workflow:")
    print("   python test_dev_mode.py")
    print("\n2. Check the debug dashboard:")
    print("   http://localhost:8000/debug/dashboard")
    print("\n3. You should see:")
    print("   - Trace with complete timeline")
    print("   - All events logged")
    print("   - Performance metrics")
    print("   - Success/failure status")
    print()


def show_api_examples():
    """Show example API calls."""
    print("\n🔧 API EXAMPLES")
    print("=" * 70)
    print("\n# List recent traces")
    print("curl http://localhost:8000/debug/traces?limit=10")
    print("\n# Get specific trace")
    print("curl http://localhost:8000/debug/traces/{trace_id}")
    print("\n# Get timeline view")
    print("curl http://localhost:8000/debug/traces/{trace_id}/timeline")
    print("\n# Export as JSON")
    print("curl http://localhost:8000/debug/traces/{trace_id}/export > trace.json")
    print("\n# Clear old traces")
    print("curl -X POST http://localhost:8000/debug/traces/clear?max_age_hours=24")
    print()


def main():
    """Main entry point."""
    print("\n🚀 OmicsOracle Debugging System Enabler")
    print("=" * 70)
    
    # Check files
    if not check_files_exist():
        print("\n❌ Please ensure all tracing files are created first")
        sys.exit(1)
    
    # Show integration steps
    show_integration_steps()
    
    # Show test instructions
    show_quick_test()
    
    # Show API examples
    show_api_examples()
    
    print("\n✅ Ready to integrate! Follow the steps above.")
    print("\n💡 Tip: Integration takes ~15 minutes and provides complete visibility")
    print("   into your entire workflow execution pipeline.\n")


if __name__ == "__main__":
    main()
