> pytest -v
/usr/lib/python3.13/site-packages/pytest_asyncio/plugin.py:207: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
=============================================================================================== test session starts ================================================================================================
platform linux -- Python 3.13.2, pytest-8.3.5, pluggy-1.5.0 -- /usr/bin/python
cachedir: .pytest_cache
rootdir: /home/cam/repos/cyberon
configfile: pytest.ini
testpaths: app/tests
plugins: asyncio-0.25.1, anyio-4.8.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None
collected 182 items                                                                                                                                                                                                

app/tests/mcp/test_integration.py::test_server_initialization PASSED                                                                                                                                         [  0%]
app/tests/mcp/test_integration.py::test_query_integration PASSED                                                                                                                                             [  1%]
app/tests/mcp/test_integration.py::test_resources_integration PASSED                                                                                                                                         [  1%]
app/tests/mcp/test_integration.py::test_tools_integration PASSED                                                                                                                                             [  2%]
app/tests/mcp/test_integration.py::test_prompts_integration PASSED                                                                                                                                           [  2%]
app/tests/mcp/test_integration.py::test_error_handling PASSED                                                                                                                                                [  3%]
app/tests/mcp/test_mcp_server.py::TestMCPServer::test_server_initialization PASSED                                                                                                                           [  3%]
app/tests/mcp/test_mcp_server.py::TestMCPServer::test_register_handler PASSED                                                                                                                                [  4%]
app/tests/mcp/test_mcp_server.py::TestMCPServer::test_register_transport PASSED                                                                                                                              [  4%]
app/tests/mcp/test_mcp_server.py::TestMCPServer::test_handle_valid_request PASSED                                                                                                                            [  5%]
app/tests/mcp/test_mcp_server.py::TestMCPServer::test_handle_invalid_request PASSED                                                                                                                          [  6%]
app/tests/mcp/test_mcp_server.py::TestMCPServer::test_handler_exception PASSED                                                                                                                               [  6%]
app/tests/mcp/test_mcp_server.py::TestMCPServer::test_invalid_json PASSED                                                                                                                                    [  7%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_list_prompts_handler PASSED                                                                                                               [  7%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_get_prompt_handler_entity_analysis PASSED                                                                                                 [  8%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_get_prompt_handler_concept_comparison PASSED                                                                                              [  8%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_get_prompt_handler_ontology_exploration PASSED                                                                                            [  9%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_get_prompt_handler_hierarchy_analysis PASSED                                                                                              [  9%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_get_prompt_handler_central_concepts PASSED                                                                                                [ 10%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_get_prompt_handler_not_found PASSED                                                                                                       [ 10%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_process_prompt_template PASSED                                                                                                            [ 11%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_entity_analysis_prompt_handler PASSED                                                                                                     [ 12%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_concept_comparison_prompt_handler PASSED                                                                                                  [ 12%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_ontology_exploration_prompt_handler PASSED                                                                                                [ 13%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_hierarchy_analysis_prompt_handler PASSED                                                                                                  [ 13%]
app/tests/mcp/test_prompt_integration.py::TestPromptHandlers::test_central_concepts_prompt_handler PASSED                                                                                                    [ 14%]
app/tests/mcp/test_query_integration.py::test_entity_search_handler PASSED                                                                                                                                   [ 14%]
app/tests/mcp/test_query_integration.py::test_entity_info_handler PASSED                                                                                                                                     [ 15%]
app/tests/mcp/test_query_integration.py::test_find_paths_handler PASSED                                                                                                                                      [ 15%]
app/tests/mcp/test_query_integration.py::test_find_connections_handler PASSED                                                                                                                                [ 16%]
app/tests/mcp/test_query_integration.py::test_mcp_server_json_rpc_format PASSED                                                                                                                              [ 17%]
app/tests/mcp/test_query_integration.py::test_session_management PASSED                                                                                                                                      [ 17%]
app/tests/mcp/test_query_integration.py::test_error_handling PASSED                                                                                                                                          [ 18%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_list_resource_templates PASSED                                                                                                        [ 18%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_list_resources PASSED                                                                                                                 [ 19%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_read_entity_resource PASSED                                                                                                           [ 19%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_read_entity_search_resource PASSED                                                                                                    [ 20%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_read_graph_summary_resource PASSED                                                                                                    [ 20%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_read_section_resource PASSED                                                                                                          [ 21%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_read_subsection_resource PASSED                                                                                                       [ 21%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_resource_subscription PASSED                                                                                                          [ 22%]
app/tests/mcp/test_resource_integration.py::TestResourceHandlers::test_resource_unsubscription PASSED                                                                                                        [ 23%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_init PASSED                                                                                                                                  [ 23%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_init_and_aenter_default_io_streams[asyncio] PASSED                                                                                           [ 24%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_aenter_returns_self[asyncio] PASSED                                                                                                          [ 24%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_aexit_closes_transport[asyncio] PASSED                                                                                                       [ 25%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_close_idempotent[asyncio] PASSED                                                                                                             [ 25%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_send_message_framing[asyncio] PASSED                                                                                                         [ 26%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_send_already_has_newline[asyncio] PASSED                                                                                                     [ 26%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_send_after_close[asyncio] PASSED                                                                                                             [ 27%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_send_broken_pipe[asyncio] PASSED                                                                                                             [ 28%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_reader_loop_internal_logic_with_handler_response[asyncio] PASSED                                                                             [ 28%]
app/tests/mcp/test_stdio_transport.py::TestStdioTransport::test_reader_loop_handles_eof[asyncio] ^C

================================================================================================= warnings summary =================================================================================================
app/tests/mcp/test_integration.py:24
  /home/cam/repos/cyberon/app/tests/mcp/test_integration.py:24: PytestCollectionWarning: cannot collect test class 'TestTransport' because it has a __init__ constructor (from: app/tests/mcp/test_integration.py)
    class TestTransport:

app/tests/mcp/test_mcp_server.py:13
  /home/cam/repos/cyberon/app/tests/mcp/test_mcp_server.py:13: PytestCollectionWarning: cannot collect test class 'TestMCPServerClass' because it has a __init__ constructor (from: app/tests/mcp/test_mcp_server.py)
    class TestMCPServerClass(MCPServer):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
/usr/lib/python3.13/unittest/mock.py:359: KeyboardInterrupt
(to show a full traceback on KeyboardInterrupt use --full-trace)
========================================================================================== 52 passed, 2 warnings in 5.47s ==========================================================================================