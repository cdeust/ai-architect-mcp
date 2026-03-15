'use strict';

const fs = require('node:fs');
const readline = require('node:readline');
const { EventSourcePort } = require('../ports/event-source-port');

const DEFAULT_PLAYBACK_SPEED = 1.0;

/**
 * JSONL file-based EventSourcePort implementation.
 *
 * Reads a brain-trace.jsonl file line by line and replays
 * PipelineEvents to the subscriber callback. Supports variable
 * playback speed based on event timestamps.
 */
class JsonlEventSource extends EventSourcePort {
  /**
   * @param {{ filePath: string }} options
   */
  constructor({ filePath }) {
    super();
    if (!filePath) {
      throw new Error('JsonlEventSource requires a non-empty filePath');
    }
    this._filePath = filePath;
    this._stream = null;
    this._rl = null;
    this._closed = false;
    this._playbackSpeed = DEFAULT_PLAYBACK_SPEED;
  }

  /**
   * Set the playback speed multiplier.
   *
   * @param {number} multiplier — 0 = instant, 1.0 = real-time, 2.0 = 2x speed
   */
  setPlaybackSpeed(multiplier) {
    if (typeof multiplier !== 'number' || multiplier < 0) {
      throw new Error('Playback speed must be a non-negative number');
    }
    this._playbackSpeed = multiplier;
  }

  /**
   * Subscribe to pipeline events replayed from the JSONL file.
   *
   * Reads the file line by line, parses each as JSON, and calls
   * the callback. Delay between events is derived from timestamps
   * when playback speed > 0.
   *
   * @param {function(import('../ports/event-source-port').PipelineEvent): void} callback
   */
  subscribe(callback) {
    if (typeof callback !== 'function') {
      throw new Error('subscribe() requires a function callback');
    }
    this._closed = false;
    this._replayFile(callback);
  }

  /**
   * Read and replay the JSONL file with timestamp-based delays.
   * @param {function(Object): void} callback
   * @private
   */
  async _replayFile(callback) {
    this._stream = fs.createReadStream(this._filePath, { encoding: 'utf8' });
    this._rl = readline.createInterface({ input: this._stream });

    let previousTimestamp = null;

    for await (const line of this._rl) {
      if (this._closed) break;

      const event = this._parseLine(line);
      if (!event) continue;

      await this._applyDelay(event, previousTimestamp);
      previousTimestamp = event.timestamp || null;
      callback(event);
    }
  }

  /**
   * Parse a single JSONL line into an event object.
   * @param {string} line
   * @returns {Object|null}
   * @private
   */
  _parseLine(line) {
    const trimmed = line.trim();
    if (!trimmed) return null;

    try {
      return JSON.parse(trimmed);
    } catch {
      return null;
    }
  }

  /**
   * Wait based on the time gap between consecutive events.
   * @param {Object} event
   * @param {string|null} previousTimestamp
   * @returns {Promise<void>}
   * @private
   */
  async _applyDelay(event, previousTimestamp) {
    if (this._playbackSpeed === 0) return;
    if (!previousTimestamp || !event.timestamp) return;

    const prev = new Date(previousTimestamp).getTime();
    const curr = new Date(event.timestamp).getTime();
    const gap = curr - prev;

    if (gap <= 0 || Number.isNaN(gap)) return;

    const delay = Math.round(gap / this._playbackSpeed);
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  /**
   * Close the file stream and stop replaying.
   * @returns {Promise<void>}
   */
  async close() {
    this._closed = true;
    if (this._rl) {
      this._rl.close();
      this._rl = null;
    }
    if (this._stream) {
      this._stream.destroy();
      this._stream = null;
    }
  }
}

module.exports = { JsonlEventSource };
