// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "LoaderApp",
    platforms: [
        .iOS(.v15),
    ],
    targets: [
        .executableTarget(
            name: "LoaderApp",
            path: ".",
            exclude: ["Info.plist"]
        ),
    ]
)
