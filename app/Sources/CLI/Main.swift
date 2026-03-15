import Foundation
import AIArchitectApp

@main
@available(macOS 26.0, *)
struct AIArchitectCLI {

    static func main() async throws {
        let arguments = CommandLine.arguments

        if arguments.contains("--list") {
            try await listDocuments()
        } else if let textIndex = arguments.firstIndex(of: "--text"),
                  textIndex + 1 < arguments.count {
            let text = arguments[textIndex + 1]
            try analyzeAndStore(text: text)
        } else {
            printUsage()
        }
    }

    private static func analyzeAndStore(text: String) throws {
        let service = try AnalysisService(inMemory: true)
        let result = service.analyzeText(text)

        print("Language: \(result.language) (confidence: \(result.confidence))")
        print("Multilingual: \(result.isMultilingual)")
        print("Entities: \(result.entities.joined(separator: ", "))")
        print("Chunks: \(result.chunks.count)")
        for (i, chunk) in result.chunks.enumerated() {
            print("  [\(i + 1)] \(chunk.prefix(80))")
        }
    }

    @MainActor
    private static func listDocuments() async throws {
        let service = try AnalysisService(inMemory: true)
        let docs = try service.listDocuments()

        if docs.isEmpty {
            print("No documents stored.")
        } else {
            for doc in docs {
                print("- \(doc.title) (v\(doc.version), \(doc.status.rawValue))")
            }
        }
    }

    private static func printUsage() {
        print("Usage:")
        print("  ai-architect-cli --text \"Your text to analyze\"")
        print("  ai-architect-cli --list")
    }
}
