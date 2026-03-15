import Testing
import Foundation
@testable import AIArchitectApp
import AIPRDVisionEngine
import AIPRDVisionEngineApple

@Suite("MockupAnalyzer Tests")
struct MockupAnalyzerTests {

    @Test("Factory registration succeeds")
    func factoryRegistration() {
        VisionAnalyzerFactory.registerFoundationModelsSupport()
        let factory = VisionAnalyzerFactory()
        let providers = factory.availableOnDeviceProviders()
        #expect(providers.count >= 1)
    }
}
