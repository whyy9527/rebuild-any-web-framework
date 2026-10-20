import SwiftUI

struct ReferenceSettings: View {
    @Bindable var model: LearningModel
    var body: some View {
        HStack(alignment: .top, spacing: 0) {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    Text("Preferences").font(ReferenceStyle.font(32, bold: true))
                        .frame(height: 36).accessibilityIdentifier("preferences-title")
                    section("Lesson experience").padding(.top, 48)
                    VStack(spacing: 24) {
                        switchRow("Sound effects", id: "sound-effects", value: $model.preferences.soundEffects)
                        switchRow("Animations", id: "animations", value: $model.preferences.animations)
                        switchRow("Motivational messages", id: "motivational-messages", value: $model.preferences.motivationalMessages)
                        switchRow("Listening exercises", id: "listening-exercises", value: $model.preferences.listeningExercises)
                    }.padding(.top, 24)
                    section("Appearance").padding(.top, 48)
                    Text("Dark mode").font(ReferenceStyle.font(20, bold: true)).frame(height: 28).padding(.top, 24)
                    Menu {
                        ForEach(["System Default", "On", "Off"], id: \.self) { value in
                            Button(value) { model.preferences.darkMode = value; model.savePreferences() }
                                .accessibilityIdentifier("appearance-" + value.lowercased().replacingOccurrences(of: " ", with: "-"))
                        }
                    } label: {
                        HStack {
                            Text(model.preferences.darkMode.uppercased()).font(ReferenceStyle.font(15, bold: true)).tracking(0.5)
                            Spacer(); Image(systemName: "chevron.down").font(.system(size: 14, weight: .bold)).foregroundStyle(ReferenceStyle.disclosureInk)
                        }.padding(.horizontal, 14).frame(height: 48)
                            .foregroundStyle(ReferenceStyle.secondaryInk)
                            .background(ReferenceStyle.background, in: RoundedRectangle(cornerRadius: 12))
                            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                            .compositingGroup().shadow(color: ReferenceStyle.border, radius: 0, y: 2)
                    }.menuStyle(.button).buttonStyle(.plain).menuIndicator(.hidden)
                        .accessibilityLabel("Dark mode").accessibilityValue(model.preferences.darkMode).accessibilityIdentifier("dark-mode")
                }.frame(maxWidth: 528, alignment: .leading).padding(.horizontal, 24).padding(.top, 24)
            }.frame(maxWidth: .infinity)
            VStack(spacing: 16) {
                navigationCard("Account", items: ["Preferences", "Privacy settings"])
                navigationCard("Support", items: ["Help Center"])
                Spacer()
            }.frame(width: 368).padding(.horizontal, 24).padding(.top, 24)
        }.foregroundStyle(ReferenceStyle.ink)
    }
    private func section(_ title: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title).font(ReferenceStyle.font(24, bold: true)).foregroundStyle(ReferenceStyle.secondaryInk).frame(height: 32)
            Rectangle().fill(ReferenceStyle.border).frame(height: 2)
        }
    }
    private func switchRow(_ title: String, id: String, value: Binding<Bool>) -> some View {
        HStack {
            Text(title).font(ReferenceStyle.font(20, bold: true))
            Spacer()
            Button { value.wrappedValue.toggle(); model.savePreferences() } label: {
                ZStack(alignment: value.wrappedValue ? .trailing : .leading) {
                    Capsule().fill(value.wrappedValue ? ReferenceStyle.blue : ReferenceStyle.border).frame(height: 24)
                    RoundedRectangle(cornerRadius: 7).fill(ReferenceStyle.background).frame(width: 28, height: 32)
                        .overlay(RoundedRectangle(cornerRadius: 7).strokeBorder(value.wrappedValue ? ReferenceStyle.blue : ReferenceStyle.border, lineWidth: 2))
                }.frame(width: 56, height: 32)
            }.buttonStyle(.plain)
                .accessibilityLabel(title).accessibilityValue(value.wrappedValue ? "on" : "off").accessibilityIdentifier(id)
        }.frame(height: 32)
    }
    private func navigationCard(_ title: String, items: [String]) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(title).font(ReferenceStyle.font(24, bold: true)).foregroundStyle(ReferenceStyle.secondaryInk).frame(height: 32)
            VStack(alignment: .leading, spacing: 4) {
                ForEach(items, id: \.self) { item in
                    Button {
                        model.destination = item == "Preferences" ? "Settings" : item
                    } label: {
                        Text(item).font(ReferenceStyle.font(20, bold: true)).frame(maxWidth: .infinity, alignment: .leading).frame(height: 40)
                    }.buttonStyle(.plain).accessibilityIdentifier("settings-" + item.lowercased().replacingOccurrences(of: " ", with: "-"))
                }
            }
        }.padding(.horizontal, 48).padding(.vertical, 26).frame(maxWidth: .infinity, alignment: .leading)
            .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2))
    }
}
