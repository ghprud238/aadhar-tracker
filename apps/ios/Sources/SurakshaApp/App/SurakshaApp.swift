import SwiftUI

public struct SurakshaAppView: View {
    public init() {}

    public var body: some View {
        MainTabView()
    }
}

#if os(iOS) && !SWIFT_PACKAGE
@main
public struct SurakshaApp: App {
    public init() {}

    public var body: some Scene {
        WindowGroup {
            SurakshaAppView()
        }
    }
}
#endif
