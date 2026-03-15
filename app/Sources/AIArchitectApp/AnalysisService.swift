import Foundation
import SwiftData
import AIPRDAppleIntelligenceEngine
import AIPRDSharedUtilities

/// Composes NLTextAnalyzer and SwiftDataStack to provide text analysis with persistence.
@available(macOS 26.0, *)
public final class AnalysisService: Sendable {

    private let stack: SwiftDataStack
    private let analyzer: NLTextAnalyzer

    /// Creates the service with a SwiftData stack and NL analyzer.
    /// - Parameters:
    ///   - cloudKit: Enable iCloud sync via CloudKit.
    ///   - inMemory: Use in-memory store (for tests).
    public init(cloudKit: Bool = false, inMemory: Bool = false) throws {
        self.stack = try SwiftDataStack(cloudKit: cloudKit, inMemory: inMemory)
        self.analyzer = NLTextAnalyzer()
    }

    // MARK: - Text Analysis

    /// Runs full NL analysis on the given text.
    public func analyzeText(_ text: String) -> AnalysisResult {
        let lang = analyzer.detectLanguage(in: text)
        let entities = analyzer.extractEntities(from: text)
        let chunks = analyzer.chunkBySentences(text)

        return AnalysisResult(
            language: lang.dominantLanguage ?? "und",
            confidence: lang.confidence,
            isMultilingual: lang.isMultilingual,
            entities: entities.map(\.text),
            chunks: chunks
        )
    }

    // MARK: - Persistence

    /// Saves a PRD document to SwiftData.
    @MainActor
    public func saveDocument(title: String, content: String) throws {
        let context = stack.container.mainContext
        let metadata = DocumentMetadata(
            author: "AI Architect",
            projectName: title,
            aiProvider: "on-device"
        )
        let document = PRDDocument(
            userId: UUID(),
            title: title,
            description: content,
            metadata: metadata
        )
        let model = try PRDDocumentModel.from(document)
        context.insert(model)
        try context.save()
    }

    /// Lists all stored PRD documents.
    @MainActor
    public func listDocuments() throws -> [PRDDocument] {
        let context = stack.container.mainContext
        let descriptor = FetchDescriptor<PRDDocumentModel>(
            sortBy: [SortDescriptor(\.updatedAt, order: .reverse)]
        )
        let models = try context.fetch(descriptor)
        return try models.map { model in
            let sectionModels = model.sections ?? []
            let sections = try sectionModels.map { try $0.toDomain() }
            return try model.toDomain(sections: sections, mockups: [])
        }
    }
}
