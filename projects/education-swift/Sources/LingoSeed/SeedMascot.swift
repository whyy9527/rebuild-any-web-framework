import SwiftUI

/// Original sprout companion, drawn from shapes; no reference brand artwork.
struct SeedMascot: View {
    private let green = Color(red: 0.345, green: 0.8, blue: 0)
    var body: some View {
        ZStack {
            Ellipse().fill(Color.black.opacity(0.08)).frame(width: 94, height: 24).offset(y: 58)
            Capsule().fill(.orange).frame(width: 22, height: 12).rotationEffect(.degrees(-16)).offset(x: -24, y: 52)
            Capsule().fill(.orange).frame(width: 22, height: 12).rotationEffect(.degrees(16)).offset(x: 24, y: 52)
            Ellipse().fill(green).frame(width: 28, height: 58).rotationEffect(.degrees(30)).offset(x: -45, y: 12)
            Ellipse().fill(green).frame(width: 28, height: 58).rotationEffect(.degrees(-30)).offset(x: 45, y: 12)
            RoundedRectangle(cornerRadius: 38).fill(green).frame(width: 94, height: 105).offset(y: 4)
            Ellipse().fill(Color(red: 0.58, green: 0.9, blue: 0.12)).frame(width: 61, height: 44).offset(y: 29)
            Capsule().fill(green).frame(width: 9, height: 29).rotationEffect(.degrees(-10)).offset(y: -56)
            Ellipse().fill(Color(red: 0.22, green: 0.65, blue: 0)).frame(width: 17, height: 32).rotationEffect(.degrees(-55)).offset(x: -12, y: -65)
            Ellipse().fill(Color(red: 0.57, green: 0.88, blue: 0)).frame(width: 18, height: 34).rotationEffect(.degrees(50)).offset(x: 13, y: -69)
            HStack(spacing: 6) {
                eye(looking: 3)
                eye(looking: 1)
            }.offset(y: -5)
            Ellipse().fill(.yellow).frame(width: 20, height: 12).offset(y: 16)
            Capsule().fill(Color(red: 0.22, green: 0.55, blue: 0)).frame(width: 17, height: 4).rotationEffect(.degrees(-8)).offset(y: 37)
        }.frame(width: 125, height: 155).accessibilityLabel("Seed, your learning companion")
    }
    private func eye(looking: CGFloat) -> some View {
        ZStack {
            Ellipse().fill(.white).frame(width: 33, height: 41)
            Ellipse().fill(Color(white: 0.25)).frame(width: 14, height: 23).offset(x: looking, y: 2)
            Circle().fill(.white).frame(width: 6).offset(x: looking + 3, y: -4)
        }
    }
}
