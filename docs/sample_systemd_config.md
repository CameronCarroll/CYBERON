[Unit]
Description=CYBERON MCP Server Stdio
After=network.target

[Service]
Type=simple
User=cam
Group=cam

WorkingDirectory=/home/cam/repos/cyberon/

ExecStart=/bin/sh -c 'exec /usr/bin/python /home/cam/repos/cyberon/mcp_server.py --data-file=/home/cam/repos/cyberon/data_template.json < /run/cyberon/mcp_in.pipe > /run/cyberon/mcp_out.pipe'

Restart=on-failure
RestartSec=5

StandardError=journal

[Install]
WantedBy=multi-user.target