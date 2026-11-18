// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "SurakshaApp",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(
            name: "SurakshaApp",
            targets: ["SurakshaApp"]
        ),
        .executable(
            name: "SurakshaAppTests",
            targets: ["SurakshaAppTests"]
        )
    ],
    dependencies: [],
    targets: [
        .target(
            name: "SurakshaApp",
            dependencies: [],
            path: "Sources/SurakshaApp"
        ),
        .executableTarget(
            name: "SurakshaAppTests",
            dependencies: ["SurakshaApp"],
            path: "Tests/SurakshaAppTests"
        ),
    ]
)
