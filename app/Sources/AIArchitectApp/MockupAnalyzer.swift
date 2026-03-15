import Foundation
import AIPRDVisionEngine
import AIPRDVisionEngineApple
import AIPRDSharedUtilities

/// Wraps VisionAnalyzerFactory to provide mockup image analysis via Apple Foundation Models.
@available(macOS 26.0, *)
public struct MockupAnalyzer: Sendable {

    private let analyzer: VisionAnalysisPort

    /// Creates a MockupAnalyzer using the Apple Foundation Models provider.
    /// Registers Foundation Models support and creates the analyzer asynchronously.
    public static func create(
        confidenceThreshold: Float = 0.85
    ) async throws -> MockupAnalyzer {
        VisionAnalyzerFactory.registerFoundationModelsSupport()
        let factory = VisionAnalyzerFactory()
        let config = VisionProviderConfiguration(
            confidenceThreshold: confidenceThreshold,
            useGuidedGeneration: true,
            preferFoundationModels: true
        )
        let port = try await factory.createFoundationModelsAnalyzer(
            configuration: config
        )
        return MockupAnalyzer(analyzer: port)
    }

    init(analyzer: VisionAnalysisPort) {
        self.analyzer = analyzer
    }

    /// Analyzes a mockup image, extracting UI components, interactions, and data requirements.
    public func analyzeMockup(imageData: Data) async throws -> MockupAnalysisResult {
        try await analyzer.analyzeMockup(imageData: imageData, prompt: nil)
    }

    /// The name of the underlying vision provider.
    public var providerName: String {
        analyzer.providerName
    }
}
