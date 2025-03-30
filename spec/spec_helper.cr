# spec/spec_helper.cr
require "spec"

# Adjust path based on where you run 'crystal spec' from
# Assuming you run it from the project root where 'src/' and 'spec/' reside.
require "../src/errors"
require "../src/transport"
require "../src/mcp_client"
# Feature modules are included by mcp_client.cr, no need to require them individually here

# Add a special macro to help with test expectations
macro expect_not_raises(&block)
  {% if block.body.is_a?(Expressions) %}
    {{block.body}}
  {% else %}
    {{block}}
  {% end %}
end

# Optional: Set a default log level for tests (e.g., suppress info messages)
# MCPClient.log_level = Logger::WARN