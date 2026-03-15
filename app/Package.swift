// swift-tools-version: 6.2
import PackageDescription

let packagesPath = "../../../ai-architect-prd-builder/packages"

let package = Package(
    name: "AIArchitectApp",
    platforms: [.macOS(.v26)],
    products: [
        .library(
            name: "AIArchitectApp",
            targets: ["AIArchitectApp"]
        ),
        .executable(
            name: "ai-architect-cli",
            targets: ["CLI"]
        )
    ],
    dependencies: [
        .package(path: "\(packagesPath)/AIPRDAppleIntelligenceEngine"),
        .package(path: "\(packagesPath)/AIPRDVisionEngine"),
        .package(path: "\(packagesPath)/AIPRDVisionEngineApple"),
        .package(path: "\(packagesPath)/AIPRDSharedUtilities")
    ],
    targets: [
        .target(
            name: "AIArchitectApp",
            dependencies: [
                .product(name: "AIPRDAppleIntelligenceEngine", package: "AIPRDAppleIntelligenceEngine"),
                .product(name: "AIPRDVisionEngine", package: "AIPRDVisionEngine"),
                .product(name: "AIPRDVisionEngineApple", package: "AIPRDVisionEngineApple"),
                .product(name: "AIPRDSharedUtilities", package: "AIPRDSharedUtilities")
            ],
            path: "Sources/AIArchitectApp"
        ),
        .executableTarget(
            name: "CLI",
            dependencies: ["AIArchitectApp"],
            path: "Sources/CLI"
        ),
        .testTarget(
            name: "AIArchitectAppTests",
            dependencies: ["AIArchitectApp"],
            path: "Tests"
        )
    ]
)
