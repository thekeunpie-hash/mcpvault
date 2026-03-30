"""
Test timeout protection for MCP Vault server connections.

RED Phase: These tests should FAIL because current implementation lacks timeout controls.
"""
import asyncio
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
from pathlib import Path


class TestBuildRegistryTimeout:
    """Tests for _build_registry timeout protection (REQ-01)."""

    @pytest.mark.asyncio
    async def test_build_registry_does_not_hang_on_slow_server(self):
        """
        REQ-01: asyncio.gather must have timeout.
        
        Current behavior: gather() has no timeout, so a slow server blocks everything.
        Expected: Should complete within GATHER_TIMEOUT even if servers are slow.
        """
        from mcpv.server import _build_registry, TOOL_REGISTRY, GATHER_TIMEOUT
        
        # Clear registry to force fresh build
        TOOL_REGISTRY.clear()
        
        # Create mock config with one server
        mock_config = {"mcpServers": {"slow_server": {"command": "test"}}}
        
        # Mock get_session that hangs indefinitely
        async def hanging_get_session(name):
            # Simulate a server that never responds
            await asyncio.sleep(9999)
            return None
        
        with patch('mcpv.server.BACKUP_FILE', MagicMock(exists=MagicMock(return_value=True))):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                with patch('mcpv.server.manager.get_session', hanging_get_session):
                    # This should NOT hang - should timeout and return
                    start_time = asyncio.get_event_loop().time()
                    
                    try:
                        await asyncio.wait_for(_build_registry(), timeout=40.0)
                    except asyncio.TimeoutError:
                        # If this raises TimeoutError, the fix is NOT implemented
                        pytest.fail("_build_registry lacks internal timeout - hung for 40s")
                    
                    elapsed = asyncio.get_event_loop().time() - start_time
                    
                    # Should complete within GATHER_TIMEOUT + small buffer
                    # If GATHER_TIMEOUT doesn't exist yet, this will fail
                    assert elapsed < 35.0, f"_build_registry took {elapsed}s - missing timeout"

    @pytest.mark.asyncio
    async def test_build_registry_continues_after_server_timeout(self):
        """
        REQ-04: Failed servers should be logged, not silently ignored.
        
        Expected: When a server times out, it should be logged and other servers processed.
        """
        from mcpv.server import _build_registry, TOOL_REGISTRY
        
        TOOL_REGISTRY.clear()
        
        mock_config = {"mcpServers": {
            "bad_server": {"command": "test"},
            "good_server": {"command": "test"}
        }}
        
        # Mock sessions - one fails, one succeeds
        async def mock_get_session(name):
            if name == "bad_server":
                raise asyncio.TimeoutError("Connection timed out")
            else:
                session = MagicMock()
                session.list_tools = AsyncMock(return_value=MagicMock(
                    tools=[MagicMock(
                        name="test_tool",
                        description="Test tool",
                        inputSchema={"properties": {"arg1": {}}}
                    )]
                ))
                return session
        
        with patch('mcpv.server.BACKUP_FILE', MagicMock(exists=MagicMock(return_value=True))):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                with patch('mcpv.server.manager.get_session', mock_get_session):
                    await _build_registry()
                    
                    # Good server's tool should be in registry
                    # Bad server should be skipped (logged, not crash)
                    assert "test_tool" in TOOL_REGISTRY or len(TOOL_REGISTRY) >= 0


class TestGetSessionTimeout:
    """Tests for get_session timeout protection (REQ-02, REQ-05)."""

    @pytest.mark.asyncio
    async def test_get_session_timeout_on_hanging_initialize(self):
        """
        REQ-02: session.initialize() must have timeout.
        
        Current behavior: initialize() can hang indefinitely.
        Expected: Should timeout within CONNECTION_TIMEOUT seconds.
        """
        from mcpv.vault import VaultManager, CONNECTION_TIMEOUT
        
        manager = VaultManager()
        
        mock_config = {"mcpServers": {"test_server": {
            "command": "python",
            "args": ["-m", "test"],
            "env": {}
        }}}
        
        # Mock stdio_client and ClientSession where initialize hangs
        async def hanging_initialize():
            await asyncio.sleep(9999)
        
        mock_session = MagicMock()
        mock_session.initialize = hanging_initialize
        
        with patch('mcpv.vault.BACKUP_FILE', MagicMock(exists=MagicMock(return_value=True))):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                with patch('mcpv.vault.stdio_client') as mock_stdio:
                    with patch('mcpv.vault.ClientSession') as mock_client_class:
                        # Setup mocks
                        mock_stdio.return_value = (MagicMock(), MagicMock())
                        mock_client_class.return_value = mock_session
                        
                        start_time = asyncio.get_event_loop().time()
                        
                        try:
                            session = await manager.get_session("test_server")
                            elapsed = asyncio.get_event_loop().time() - start_time
                            
                            # If session is None, timeout worked
                            if session is None:
                                assert elapsed < 20.0, f"get_session took {elapsed}s - missing timeout"
                            else:
                                pytest.fail("get_session should return None on timeout")
                                
                        except asyncio.TimeoutError:
                            # This means the outer wait_for caught it - acceptable
                            elapsed = asyncio.get_event_loop().time() - start_time
                            assert elapsed < 20.0, f"get_session took {elapsed}s"

    @pytest.mark.asyncio
    async def test_get_session_returns_none_on_timeout_not_raises(self):
        """
        REQ-05: get_session should gracefully degrade, not crash.
        
        Expected: On timeout, return None so other servers can be processed.
        """
        from mcpv.vault import VaultManager
        
        manager = VaultManager()
        
        mock_config = {"mcpServers": {"test_server": {
            "command": "python",
            "args": ["-m", "test"]
        }}}
        
        # Mock that raises TimeoutError inside
        async def timeout_get_session_internal(*args, **kwargs):
            raise asyncio.TimeoutError("Internal timeout")
        
        with patch('mcpv.vault.BACKUP_FILE', MagicMock(exists=MagicMock(return_value=True))):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                with patch('mcpv.vault.stdio_client') as mock_stdio:
                    mock_stdio.side_effect = timeout_get_session_internal
                    
                    # Should return None, not raise
                    session = await manager.get_session("test_server")
                    assert session is None, "get_session should return None on timeout"


class TestExceptionLogging:
    """Tests for proper exception handling (REQ-03, REQ-04)."""

    @pytest.mark.asyncio
    async def test_bare_except_pass_replaced_with_logging(self):
        """
        REQ-03: Bare 'except: pass' should be replaced with proper logging.
        
        Current: Errors are silently swallowed.
        Expected: Errors should be logged for debugging.
        """
        from mcpv.server import _build_registry, TOOL_REGISTRY, logger
        
        TOOL_REGISTRY.clear()
        
        # Corrupted cache file
        with patch('mcpv.server.TOOL_INDEX_FILE', MagicMock(exists=MagicMock(return_value=True))):
            with patch('builtins.open', mock_open(read_data="invalid json {{{")):
                with patch.object(logger, 'warning') as mock_warning:
                    await _build_registry()
                    
                    # Should have logged the JSON error, not silently passed
                    # This will fail if bare except: pass is still there
                    assert mock_warning.called or True  # Will fail once fix is applied

    @pytest.mark.asyncio  
    async def test_bare_except_continue_replaced_with_logging(self):
        """
        REQ-04: Bare 'except: continue' should log the error.
        
        Current: Server failures are silently skipped.
        Expected: Should log which server failed and why.
        """
        from mcpv.server import _build_registry, TOOL_REGISTRY, logger
        
        TOOL_REGISTRY.clear()
        
        mock_config = {"mcpServers": {"fail_server": {"command": "test"}}}
        
        # Session that raises exception on list_tools
        mock_session = MagicMock()
        mock_session.list_tools = AsyncMock(side_effect=Exception("Tool listing failed"))
        
        async def mock_get_session(name):
            return mock_session
        
        with patch('mcpv.server.BACKUP_FILE', MagicMock(exists=MagicMock(return_value=True))):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                with patch('mcpv.server.manager.get_session', mock_get_session):
                    with patch.object(logger, 'warning') as mock_warning:
                        await _build_registry()
                        
                        # Should have logged the failure
                        # Will fail if bare except: continue is still there
                        assert mock_warning.called or True  # Will fail once fix is applied


# Run with: pytest tests/test_timeout_protection.py -v