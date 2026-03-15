'use strict';

const http = require('node:http');
const https = require('node:https');
const { EventSourcePort } = require('../ports/event-source-port');

const MAX_RETRIES = 5;
const RETRY_DELAY_MS = 1000;

/**
 * SSE-based EventSourcePort implementation.
 *
 * Connects to the Python MCP server's SSE endpoint and
 * forwards parsed PipelineEvents to the subscriber callback.
 */
class SseEventSource extends EventSourcePort {
  /**
   * @param {{ url: string }} options
   */
  constructor({ url }) {
    super();
    if (!url) {
      throw new Error('SseEventSource requires a non-empty url');
    }
    this._url = url;
    this._request = null;
    this._closed = false;
    this._retryCount = 0;
    this._callback = null;
  }

  /**
   * Subscribe to incoming pipeline events via SSE.
   *
   * Opens a persistent HTTP GET connection and parses the SSE
   * text/event-stream format. Each 'data:' line is JSON-parsed
   * and forwarded to the callback.
   *
   * @param {function(import('../ports/event-source-port').PipelineEvent): void} callback
   */
  subscribe(callback) {
    if (typeof callback !== 'function') {
      throw new Error('subscribe() requires a function callback');
    }
    this._callback = callback;
    this._closed = false;
    this._retryCount = 0;
    this._connect();
  }

  /**
   * Open the SSE connection and wire up response parsing.
   * @private
   */
  _connect() {
    if (this._closed) return;

    const client = this._url.startsWith('https') ? https : http;

    this._request = client.get(this._url, (res) => {
      this._retryCount = 0;
      this._handleResponse(res);
    });

    this._request.on('error', (err) => {
      this._handleConnectionError(err);
    });
  }

  /**
   * Parse SSE text/event-stream lines from the response.
   * @param {import('http').IncomingMessage} res
   * @private
   */
  _handleResponse(res) {
    if (res.statusCode !== 200) {
      res.destroy();
      this._handleConnectionError(
        new Error(`SSE endpoint returned status ${res.statusCode}`)
      );
      return;
    }

    let buffer = '';

    res.setEncoding('utf8');
    res.on('data', (chunk) => {
      buffer += chunk;
      buffer = this._processBuffer(buffer);
    });

    res.on('end', () => {
      this._handleConnectionError(new Error('SSE stream ended'));
    });

    res.on('error', (err) => {
      this._handleConnectionError(err);
    });
  }

  /**
   * Extract complete SSE data lines from the buffer and dispatch.
   * @param {string} buffer
   * @returns {string} remaining buffer content
   * @private
   */
  _processBuffer(buffer) {
    const lines = buffer.split('\n');
    const remaining = lines.pop();

    for (const line of lines) {
      this._parseLine(line);
    }

    return remaining || '';
  }

  /**
   * Parse a single SSE line. Only 'data:' lines are processed.
   * @param {string} line
   * @private
   */
  _parseLine(line) {
    const trimmed = line.trim();
    if (!trimmed.startsWith('data:')) return;

    const jsonStr = trimmed.slice(5).trim();
    if (!jsonStr) return;

    try {
      const event = JSON.parse(jsonStr);
      this._callback(event);
    } catch {
      // Malformed JSON line — skip silently
    }
  }

  /**
   * Handle connection errors with retry logic.
   * @param {Error} _err
   * @private
   */
  _handleConnectionError(_err) {
    if (this._closed) return;

    this._retryCount += 1;
    if (this._retryCount > MAX_RETRIES) {
      this._closed = true;
      return;
    }

    setTimeout(() => this._connect(), RETRY_DELAY_MS);
  }

  /**
   * Close the SSE connection and stop retrying.
   * @returns {Promise<void>}
   */
  async close() {
    this._closed = true;
    if (this._request) {
      this._request.destroy();
      this._request = null;
    }
  }
}

module.exports = { SseEventSource };
