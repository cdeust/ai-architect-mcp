/**
 * Port interface for pipeline event sources.
 *
 * Implementations subscribe to events from SSE streams (live)
 * or JSONL files (replay). The port abstracts the source so the
 * domain layer can process events without knowing their origin.
 *
 * @interface EventSourcePort
 */

/**
 * @typedef {Object} PipelineEvent
 * @property {string} event_id
 * @property {string} event_type
 * @property {number} stage_id
 * @property {string} session_id
 * @property {string} timestamp
 * @property {string} tool_name
 * @property {string} message
 * @property {number|null} duration_ms
 * @property {Object} metadata
 */

class EventSourcePort {
  /**
   * Subscribe to incoming pipeline events.
   *
   * @param {function(PipelineEvent): void} callback — called for each event
   * @returns {void}
   */
  subscribe(callback) {
    throw new Error('EventSourcePort.subscribe() must be implemented');
  }

  /**
   * Close the event source and release resources.
   *
   * @returns {Promise<void>}
   */
  async close() {
    throw new Error('EventSourcePort.close() must be implemented');
  }
}

module.exports = { EventSourcePort };
