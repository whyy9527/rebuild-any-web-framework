import SwiftUI
import LearningCore

struct ReferenceQuests: View {
    let snapshot: HomeProgressSnapshot?
    private let orange = Color(red: 1, green: 150/255, blue: 0)
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 0) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("就是你了！").font(ReferenceStyle.font(25, bold: true)).frame(height: 34)
                    Text("完成特别任务，获取奖励！特别任务每天都会更新哦！")
                        .font(ReferenceStyle.font(17)).frame(height: 48)
                }.frame(maxWidth: .infinity, alignment: .leading)
                ReferenceStyle.image("quests-banner-duo").resizable().frame(width: 172, height: 184)
            }.padding(24).foregroundStyle(.white)
                .background(Color(red: 144/255, green: 105/255, blue: 205/255), in: RoundedRectangle(cornerRadius: 16, style: .circular))
                .accessibilityElement(children: .contain).accessibilityIdentifier("quests-banner")
            HStack {
                Text("每日特别任务").font(ReferenceStyle.font(25, bold: true))
                Spacer()
                if let countdown = snapshot?.questCountdown {
                    HStack(spacing: 5) {
                        ReferenceStyle.image("quests-clock").resizable().frame(width: 16, height: 16)
                        Text(countdown).font(ReferenceStyle.font(17, bold: true)).foregroundStyle(orange)
                    }
                }
            }.frame(height: 28).padding(.top, 30)
            HStack(spacing: 22) {
                ReferenceStyle.image("quest-xp").resizable().frame(width: 60, height: 60)
                VStack(alignment: .leading, spacing: 8) {
                    Text("获取 \(snapshot?.questTarget ?? 10) 经验").font(ReferenceStyle.font(19, bold: true)).frame(height: 26)
                    HStack(spacing: 0) {
                        ZStack {
                            GeometryReader { geometry in
                                Capsule().fill(ReferenceStyle.border)
                                Capsule().fill(Color(red: 1, green: 200/255, blue: 0))
                                    .frame(width: geometry.size.width * CGFloat(snapshot?.questProgress ?? 0) / CGFloat(snapshot?.questTarget ?? 10))
                                    .overlay(alignment: .top) { Capsule().fill(Color(red: 1, green: 211/255, blue: 51/255)).frame(height: 5).padding(.horizontal, 5).padding(.top, 3) }
                            }.frame(height: 20)
                            Text("\(snapshot?.questProgress ?? 0) / \(snapshot?.questTarget ?? 10)")
                                .font(ReferenceStyle.font(14, bold: true)).tracking(0.56)
                                .foregroundStyle(Color(red: 205/255, green: 121/255, blue: 0))
                        }.frame(maxWidth: .infinity).padding(.top, 4)
                        ReferenceStyle.image("quest-chest").resizable().frame(width: 35, height: 35)
                    }.padding(.trailing, 4).frame(height: 35)
                }.frame(maxWidth: .infinity, alignment: .leading)
            }.padding(.horizontal, 27).padding(.vertical, 22)
                .overlay(RoundedRectangle(cornerRadius: 16, style: .circular).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                .accessibilityElement(children: .contain).accessibilityIdentifier("quests-daily").padding(.top, 12)
            HStack(spacing: 22) {
                ReferenceStyle.image("quests-locked").resizable().frame(width: 60, height: 60)
                Text("更多特别任务即将解锁").font(ReferenceStyle.font(19, bold: true)).foregroundStyle(ReferenceStyle.disclosureInk)
                Spacer(minLength: 0)
            }.padding(20).frame(maxWidth: .infinity)
                .background(Color(white: 247/255), in: RoundedRectangle(cornerRadius: 16, style: .circular))
                .overlay(RoundedRectangle(cornerRadius: 16, style: .circular).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                .accessibilityElement(children: .contain).accessibilityIdentifier("quests-locked").padding(.top, 16)
        }
    }
}

struct ReferenceQuestMonthly: View {
    let practice: () -> Void
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 28) {
                HStack(spacing: 0) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("每月挑战稍后揭秘！").font(ReferenceStyle.font(17, bold: true)).frame(height: 28)
                        Text("快开始你的每月挑战，独家徽章尽入囊中！").font(ReferenceStyle.font(17))
                            .foregroundStyle(ReferenceStyle.secondaryInk).frame(height: 48)
                    }.padding(.top, 8).frame(width: geometry.size.width - 140, height: 138, alignment: .topLeading)
                    ReferenceStyle.image("quests-monthly-medal").resizable().frame(width: 116, height: 138)
                }.frame(width: geometry.size.width - 44, height: 138, alignment: .leading)
                Button(action: practice) {
                    Text("去学个单元").font(ReferenceStyle.font(15, bold: true)).tracking(0.8)
                        .foregroundStyle(ReferenceStyle.blue).frame(maxWidth: .infinity).frame(height: 50).contentShape(Rectangle())
                }.buttonStyle(QuestPracticeButtonStyle()).accessibilityIdentifier("quests-practice")
            }.padding(.horizontal, 22).padding(.top, 22).padding(.bottom, 10)
        }.frame(height: 248)
            .overlay(RoundedRectangle(cornerRadius: 16, style: .circular).strokeBorder(ReferenceStyle.border, lineWidth: 2))
            .accessibilityElement(children: .contain).accessibilityIdentifier("quests-monthly")
    }
}

private struct QuestPracticeButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.background(alignment: .top) {
            RoundedRectangle(cornerRadius: 16, style: .circular).fill(ReferenceStyle.background).frame(height: 48)
                .shadow(color: ReferenceStyle.border, radius: 0, y: configuration.isPressed ? 0 : 2)
        }.overlay(alignment: .top) {
            RoundedRectangle(cornerRadius: 16, style: .circular).strokeBorder(ReferenceStyle.border, lineWidth: 2).frame(height: 48)
        }.offset(y: configuration.isPressed ? 2 : 0)
    }
}
