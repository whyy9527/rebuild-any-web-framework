import SwiftUI
import Lottie

/// Original Lottie JSON loaded by the observed web homepage, rendered natively.
struct ReferenceHomeDuo: View {
    private static let animation: LottieAnimation? = {
        guard let url = Bundle.module.url(forResource: "en-home-duo-twirl", withExtension: "json", subdirectory: "Reference"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? LottieAnimation.from(data: data)
    }()
    var body: some View {
        if let animation = Self.animation {
            LottieView(animation: animation).resizable().looping()
        } else {
            Text("原版 Duo 动画未能载入。")
        }
    }
}
