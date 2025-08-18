#!/usr/bin/env node
/**
 * MCP WebSocket Bridge
 * Connects to a WebSocket-based MCP server and provides stdio transport for Claude Desktop
 */

const WebSocket = require('ws');

// Configuration
const MCP_WEBSOCKET_URL = 'wss://ogm.geo4lib.app/api/v1/mcp/ws';

// MCP Protocol handling
class MCPWebSocketBridge {
    constructor() {
        this.requestId = 0;
        this.pendingRequests = new Map();
        this.ws = null;
        this.connected = false;
    }

    // Connect to WebSocket MCP server
    async connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(MCP_WEBSOCKET_URL);

            this.ws.on('open', () => {
                console.error('Connected to MCP WebSocket server');
                this.connected = true;
                resolve();
            });

            this.ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleIncomingMessage(message);
                } catch (error) {
                    console.error('Error parsing incoming message:', error);
                }
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            });

            this.ws.on('close', () => {
                console.error('WebSocket connection closed');
                this.connected = false;
                process.exit(0);
            });
        });
    }

    // Handle incoming messages from WebSocket
    handleIncomingMessage(message) {
        const { id, result, error } = message;
        
        if (this.pendingRequests.has(id)) {
            const { resolve, reject } = this.pendingRequests.get(id);
            this.pendingRequests.delete(id);
            
            if (error) {
                reject(new Error(error.message));
            } else {
                resolve(result);
            }
        }
    }

    // Send message to WebSocket server
    async sendMessage(method, params = {}) {
        if (!this.connected) {
            throw new Error('WebSocket not connected');
        }

        const id = ++this.requestId;
        const message = {
            jsonrpc: '2.0',
            id: id,
            method: method,
            params: params
        };

        return new Promise((resolve, reject) => {
            this.pendingRequests.set(id, { resolve, reject });
            this.ws.send(JSON.stringify(message));
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
                        await this.handleOutgoingMessage(message);
                    }
                }
            } catch (error) {
                console.error('Error handling message:', error);
                // Send a proper error response with ID 0
                this.sendErrorResponse(0, -32700, 'Parse error');
            }
        });
    }

    async handleOutgoingMessage(message) {
        // Validate required JSON-RPC fields
        if (!message || typeof message !== 'object') {
            this.sendErrorResponse(0, -32700, 'Invalid message format');
            return;
        }

        const { method, params, id } = message;

        // Validate required fields
        if (!method || typeof method !== 'string') {
            this.sendErrorResponse(id || 0, -32600, 'Invalid request: missing or invalid method');
            return;
        }

        try {
            switch (method) {
                case 'initialize':
                    const initResult = await this.sendMessage('initialize', params || {});
                    this.sendResponse(id, initResult);
                    break;

                case 'tools/list':
                    const toolsResult = await this.sendMessage('tools/list', params || {});
                    this.sendResponse(id, toolsResult);
                    break;

                case 'tools/call':
                    const callResult = await this.sendMessage('tools/call', params || {});
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
        // Ensure we have a valid ID - use 0 if id is null/undefined
        const responseId = id !== null && id !== undefined ? id : 0;
        
        const response = {
            jsonrpc: '2.0',
            id: responseId,
            error: {
                code: code,
                message: message
            }
        };
        console.log(JSON.stringify(response));
    }

    // Cleanup
    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Main execution
async function main() {
    const bridge = new MCPWebSocketBridge();
    
    try {
        // Connect to WebSocket server
        await bridge.connect();
        
        // Handle stdio
        await bridge.handleStdio();
        
        // Handle process termination
        process.on('SIGINT', () => {
            console.error('Received SIGINT, shutting down...');
            bridge.close();
            process.exit(0);
        });
        
        process.on('SIGTERM', () => {
            console.error('Received SIGTERM, shutting down...');
            bridge.close();
            process.exit(0);
        });
        
    } catch (error) {
        console.error('Bridge error:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}
