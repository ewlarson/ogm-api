#!/usr/bin/env node
/**
 * MCP HTTP Bridge
 * Connects to an HTTP-based MCP server and provides stdio transport for Claude Desktop
 */

const https = require('https');
const http = require('http');

// Configuration
const MCP_SERVER_URL = 'https://ogm.geo4lib.app/api/v1/mcp';
const MCP_WEBSOCKET_URL = 'wss://ogm.geo4lib.app/api/v1/mcp/ws';

// MCP Protocol handling
class MCPBridge {
    constructor() {
        this.requestId = 0;
        this.pendingRequests = new Map();
    }

    // Send HTTP request to MCP server
    async sendRequest(method, params = {}) {
        const id = ++this.requestId;
        const request = {
            jsonrpc: '2.0',
            id: id,
            method: method,
            params: params
        };

        return new Promise((resolve, reject) => {
            const url = new URL(MCP_SERVER_URL);
            const options = {
                hostname: url.hostname,
                port: url.port || (url.protocol === 'https:' ? 443 : 80),
                path: url.pathname,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(JSON.stringify(request))
                }
            };

            const req = (url.protocol === 'https:' ? https : http).request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => {
                    data += chunk;
                });
                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        if (response.error) {
                            reject(new Error(response.error.message));
                        } else {
                            resolve(response.result);
                        }
                    } catch (error) {
                        reject(error);
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.write(JSON.stringify(request));
            req.end();
        });
    }

    // Handle stdio communication
    async handleStdio() {
        process.stdin.setEncoding('utf8');
        process.stdout.setEncoding('utf8');

        process.stdin.on('data', async (data) => {
            try {
                const lines = data.toString().trim().split('\n');
                for (const line of lines) {
                    if (line.trim()) {
                        const message = JSON.parse(line);
                        await this.handleMessage(message);
                    }
                }
            } catch (error) {
                console.error('Error handling message:', error);
                this.sendErrorResponse(null, -32700, 'Parse error');
            }
        });
    }

    async handleMessage(message) {
        const { method, params, id } = message;

        try {
            switch (method) {
                case 'initialize':
                    const initResult = await this.sendRequest('initialize', params);
                    this.sendResponse(id, initResult);
                    break;

                case 'tools/list':
                    const toolsResult = await this.sendRequest('tools/list', params);
                    this.sendResponse(id, toolsResult);
                    break;

                case 'tools/call':
                    const callResult = await this.sendRequest('tools/call', params);
                    this.sendResponse(id, callResult);
                    break;

                default:
                    this.sendErrorResponse(id, -32601, `Method not found: ${method}`);
            }
        } catch (error) {
            this.sendErrorResponse(id, -32603, `Internal error: ${error.message}`);
        }
    }

    sendResponse(id, result) {
        const response = {
            jsonrpc: '2.0',
            id: id,
            result: result
        };
        console.log(JSON.stringify(response));
    }

    sendErrorResponse(id, code, message) {
        const response = {
            jsonrpc: '2.0',
            id: id,
            error: {
                code: code,
                message: message
            }
        };
        console.log(JSON.stringify(response));
    }
}

// Main execution
async function main() {
    try {
        const bridge = new MCPBridge();
        await bridge.handleStdio();
    } catch (error) {
        console.error('Bridge error:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}
