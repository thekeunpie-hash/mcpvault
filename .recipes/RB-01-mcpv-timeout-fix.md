# RB-01: MCP Vault Timeout Fix

## Problem Statement
`get_initial_context` hangs indefinitely when connecting to upstream MCP servers due to missing timeout controls on async operations.

## Traceability Matrix

| REQ-ID | Spec Quote | Planned Function | File | Priority |
|--------|------------|------------------|------|----------|
| REQ-01 | "asyncio.gather(*tasks)" must have timeout | `_build_registry()` | server.py:57 | P0 |
| REQ-02 | "session.initialize()" must have timeout | `get_session()` | vault.py:283 | P0 |
| REQ-03 | Replace bare "except: pass" with logging | `_build_registry()` | server.py:45,76 | P1 |
| REQ-04 | Replace bare "except: continue" with logging | `_build_registry()` | server.py:76 | P1 |
| REQ-05 | Add overall timeout to get_session | `get_session()` | vault.py:252-285 | P0 |

## Implementation Plan

### DATA Layer
- No SQL/database changes required
- Add `CONNECTION_TIMEOUT` constant (15s default)
- Add `GATHER_TIMEOUT` constant (30s default)

### LOGIC Layer (Python)

#### server.py Changes
1. Add timeout constants at module level
2. Wrap `asyncio.gather()` with `asyncio.wait_for(timeout=GATHER_TIMEOUT)`
3. Replace bare `except: pass` with proper exception logging
4. Replace bare `except: continue` with timeout-aware exception handling

#### vault.py Changes
1. Import `asyncio` module
2. Wrap `session.initialize()` with `asyncio.wait_for(timeout=CONNECTION_TIMEOUT)`
3. Add try/except around entire session establishment
4. Return None on timeout instead of raising (allows graceful degradation)

### UI Layer
- Not applicable (MCP server, no UI)

## Test Strategy

### RED Phase Test
```python
# test_timeout_protection.py
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

def test_build_registry_timeout_on_hanging_server():
    """Test that _build_registry doesn't hang when a server is slow."""
    from mcpv.server import _build_registry, TOOL_REGISTRY
    
    # Mock a server that hangs indefinitely
    async def hanging_get_session(name):
        await asyncio.sleep(999)  # Never completes
        return None
    
    with patch('mcpv.server.manager.get_session', hanging_get_session):
        # This should complete within 35 seconds, not hang forever
        result = asyncio.run(asyncio.wait_for(_build_registry(), timeout=35.0))
        
        # Should either return empty registry or cached data, NOT hang
        assert result is None or isinstance(TOOL_REGISTRY, dict)

def test_get_session_timeout_on_initialize():
    """Test that get_session doesn't hang on initialize()."""
    from mcpv.vault import VaultManager
    
    manager = VaultManager()
    
    # Mock session that hangs on initialize
    async def hanging_initialize():
        await asyncio.sleep(999)
    
    with patch('mcpv.vault.stdio_client') as mock_stdio:
        with patch('mcpv.vault.ClientSession') as mock_session:
            mock_session.return_value.initialize = hanging_initialize
            
            # Should timeout within 20 seconds
            with pytest.raises(asyncio.TimeoutError):
                asyncio.run(asyncio.wait_for(
                    manager.get_session("test_server"),
                    timeout=20.0
                ))
```

## Implementation Order
1. Add timeout constants
2. Fix `asyncio.gather()` timeout (REQ-01)
3. Fix `session.initialize()` timeout (REQ-02, REQ-05)
4. Replace bare except clauses (REQ-03, REQ-04)
5. Run tests

## Expected Outcome
- `get_initial_context` completes within 35 seconds maximum
- Failed servers are logged, not silently ignored
- Registry still loads from cache if available
- No indefinite hangs on any single server failure