import Testing
import Foundation
@testable import AIArchitectApp

@Suite("AnalysisService Tests")
struct AnalysisServiceTests {

    @Test("Detects English language")
    func detectEnglish() throws {
        let service = try AnalysisService(inMemory: true)
        let result = service.analyzeText(
            "The quick brown fox jumps over the lazy dog near the river."
        )
        #expect(result.language == "en")
        #expect(result.confidence > 0.5)
    }

    @Test("Extracts named entities")
    func extractEntities() throws {
        let service = try AnalysisService(inMemory: true)
        let result = service.analyzeText(
            "Tim Cook announced new products at Apple Park in Cupertino."
        )
        #expect(result.entities.contains(where: { $0.contains("Tim Cook") || $0.contains("Cook") }))
    }

    @Test("Chunks long text into sentences")
    func chunkSentences() throws {
        let service = try AnalysisService(inMemory: true)
        let sentences = (0..<20).map { i in
            "Sentence number \(i) discusses the importance of natural language processing in modern software engineering and how it transforms the way we build intelligent applications."
        }
        let longText = sentences.joined(separator: " ")
        let result = service.analyzeText(longText)
        #expect(result.chunks.count >= 2)
    }

    @Test("SwiftData round-trip: save and load document")
    @MainActor
    func swiftDataRoundTrip() throws {
        let service = try AnalysisService(inMemory: true)
        try service.saveDocument(
            title: "Test PRD",
            content: "A product requirements document for testing persistence."
        )
        let docs = try service.listDocuments()
        #expect(docs.contains(where: { $0.title == "Test PRD" }))
    }
}
