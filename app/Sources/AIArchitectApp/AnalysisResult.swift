import Foundation

/// Result of text analysis combining language detection, entity extraction, and chunking.
public struct AnalysisResult: Sendable, Codable {
    public let language: String
    public let confidence: Double
    public let isMultilingual: Bool
    public let entities: [String]
    public let chunks: [String]

    public init(
        language: String,
        confidence: Double,
        isMultilingual: Bool,
        entities: [String],
        chunks: [String]
    ) {
        self.language = language
        self.confidence = confidence
        self.isMultilingual = isMultilingual
        self.entities = entities
        self.chunks = chunks
    }
}
