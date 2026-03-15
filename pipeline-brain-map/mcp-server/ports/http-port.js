/**
 * Port interface for HTTP server operations.
 *
 * Implementations serve API endpoints and proxy SSE streams.
 * The composition root injects the handler that dispatches to tools.
 *
 * @interface HttpPort
 */

class HttpPort {
  /**
   * Start the HTTP server and serve the given handler.
   *
   * @param {function(Object, Object): void} handler — (req, res) callback
   * @returns {Promise<number>} assigned port number
   */
  async serve(handler) {
    throw new Error('HttpPort.serve() must be implemented');
  }

  /**
   * Get the port the server is listening on.
   * @returns {number}
   */
  getPort() {
    throw new Error('HttpPort.getPort() must be implemented');
  }

  /**
   * Close the server and release resources.
   * @returns {Promise<void>}
   */
  async close() {
    throw new Error('HttpPort.close() must be implemented');
  }
}

module.exports = { HttpPort };
