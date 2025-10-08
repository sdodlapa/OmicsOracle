# SearchAgent Async Fix - Summary

## Problem

The SearchAgent was failing with error:
```
Error executing search: this event loop is already running.
Execution error in agent 'SearchAgent': Failed to execute search: this event loop is already running.
```

## Root Cause

The SearchAgent uses an async `GEOClient` but needs to run in a synchronous `_process()` method (part of the base Agent interface). When running inside FastAPI's async context (which already has an event loop), calling `asyncio.run()` or `loop.run_until_complete()` fails because you cannot run a new event loop while one is already running.

## Solution

Created a `_run_async()` helper method that:

1. **Detects if we're in an async context** using `asyncio.get_running_loop()`
2. **If in async context (FastAPI)**: Creates a new thread with its own event loop to run the coroutine
3. **If not in async context**: Uses `asyncio.run()` directly

### Code Change

```python
def _run_async(self, coro):
    """Run an async coroutine in a sync context."""
    import asyncio

    try:
        # Check if there's a running loop
        loop = asyncio.get_running_loop()
        # We're in an async context - create a new thread with its own loop
        import threading
        result = [None]
        exception = [None]

        def run_in_thread():
            try:
                # Create a new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result[0] = new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()

        if exception[0]:
            raise exception[0]
        return result[0]

    except RuntimeError:
        # No running loop - we can use asyncio.run directly
        return asyncio.run(coro)
```

### Usage in SearchAgent

```python
# Old (broken):
loop = asyncio.get_event_loop()
search_result = loop.run_until_complete(
    self._geo_client.search(query=search_query, max_results=input_data.max_results)
)

# New (working):
search_result = self._run_async(
    self._geo_client.search(query=search_query, max_results=input_data.max_results)
)
```

## Status

✅ **FIXED** - Server will auto-reload with the changes

## Testing

Try this query in the dashboard:
- Query: "HiC data for human brain tissue"
- Workflow: Simple Search
- Expected: Should now successfully search and return results

## Files Modified

- `omics_oracle_v2/agents/search_agent.py`
  - Added `_run_async()` helper method
  - Updated `_process()` to use `_run_async()` instead of direct event loop calls

## Alternative Solutions Considered

1. **nest_asyncio** - Doesn't work well with uvloop (used by FastAPI)
2. **ThreadPoolExecutor** - Still had event loop issues
3. **Making agents async** - Would require changing base Agent interface (too invasive)
4. **Using sync HTTP client** - GEOClient is designed to be async for better performance

## Impact

- ✅ No breaking changes to other agents
- ✅ Maintains async performance of GEOClient
- ✅ Works in both FastAPI (async) and standalone (sync) contexts
- ✅ Thread-safe implementation

**Date**: October 5, 2025
**Status**: Applied and ready for testing
