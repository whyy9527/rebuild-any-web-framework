import AppKit
import SwiftUI

struct ReferenceRegistration: View {
    let close: () -> Void
    var showLogin: (() -> Void)? = nil
    @State private var step = 0
    @State private var age = ""
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    @State private var emailError = false
    @State private var passwordError = false
    @State private var passwordVisible = false
    @State private var ageReset = 0
    private var invalid: Bool { emailError || passwordError }
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .topLeading) {
                Color.white
                Button { if step == 0 { close() } else { step -= 1; emailError = false; passwordError = false } } label: {
                    ReferenceStyle.image(step == 0 ? "en-path-profile-close" : "en-registration-back").resizable().frame(width: step == 0 ? 16 : 17, height: step == 0 ? 16 : 17)
                }.buttonStyle(.plain).frame(width: 20, height: 21.5).offset(x: 28, y: 30).accessibilityLabel(step == 0 ? "关闭" : "返回").accessibilityIdentifier("registration-back")
                if step != 1 {
                    Button(action: { showLogin?() }) { Text("登录").font(ReferenceStyle.font(15, bold: true)).foregroundStyle(ReferenceStyle.blue)
                        .frame(width: 67.6015625, height: 46).overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                        .offset(x: geometry.size.width - 97.6015625, y: 30) }.buttonStyle(.plain).accessibilityIdentifier("registration-switch-login")
                }
                Group {
                    if step == 0 { agePage }
                    else if step == 1 { methodsPage }
                    else { emailPage }
                }.frame(width: 375).offset(x: (geometry.size.width - 375) / 2)
            }
        }.background(.white)
    }
    private var agePage: some View {
        ZStack(alignment: .topLeading) {
            title("你的年龄是……").offset(y: 189.5)
            field("年龄", id: "path-age-input", text: $age, reservedTrailing: !age.isEmpty).id(ageReset).offset(y: 252.5)
            if !age.isEmpty { iconControl("en-registration-clear", label: "清除年龄", id: "registration-age-clear") { age = ""; ageReset += 1 }.offset(x: 343, y: 264.5) }
            (Text("告诉我们你的真实年龄，让我们为你打造一个更合适的多邻国学习体验。更多详情，请访问") + Text("隐私政策").font(ReferenceStyle.font(16, bold: true)).foregroundColor(ReferenceStyle.blue) + Text("。"))
                .font(ReferenceStyle.font(16, weight: 500)).foregroundStyle(ReferenceStyle.secondaryInk)
                .frame(width: 375, height: 48, alignment: .topLeading).offset(y: 304.5)
            control("下一步", id: "path-age-next", enabled: !age.isEmpty, color: age.isEmpty ? ReferenceStyle.border : ReferenceStyle.blue) { step = 1 }
                .offset(y: age.isEmpty ? 376.5 : 372.5)
            legal.offset(y: 461.5)
        }
    }
    private var methodsPage: some View {
        ZStack(alignment: .topLeading) {
            title("选个注册方式才能继续哦！").offset(y: 70)
            ReferenceStyle.image("en-registration-duo").resizable().frame(width: 280, height: 260).offset(x: 47.5, y: 184.5)
            method("使用 GOOGLE 继续", icon: "google", id: "registration-google", enabled: false) {}.offset(y: 504)
            method("使用 Facebook 继续", icon: "facebook", id: "registration-facebook", enabled: false) {}.offset(y: 564)
            method("使用电子邮件继续", icon: "email", id: "registration-email", enabled: true) { step = 2 }.offset(y: 624)
        }
    }
    private var emailPage: some View {
        let shift: CGFloat = invalid ? 24 : 0
        return ZStack(alignment: .topLeading) {
            title("创建档案").offset(y: 153.5 - shift)
            field("姓名（选填）", id: "registration-name", text: $name).offset(y: 216.5 - shift)
            field("邮箱", id: "registration-address", text: $email).offset(y: 276.5 - shift)
            field("密码", id: "registration-password", text: $password, secure: !passwordVisible, reservedTrailing: true).offset(y: 336.5)
            iconControl(passwordVisible ? "en-registration-hide-password" : "en-registration-show-password", label: passwordVisible ? "隐藏密码" : "显示密码", id: "registration-password-reveal") { passwordVisible.toggle() }.offset(x: 343, y: 348.5)
            if emailError { Text("邮箱地址无效").font(ReferenceStyle.font(16, weight: 400)).foregroundStyle(.red).offset(x: 28, y: 304.5) }
            if passwordError { Text("密码太短了").font(ReferenceStyle.font(16, weight: 400)).foregroundStyle(.red).offset(x: 28, y: 388.5) }
            control("创建帐户", id: "registration-submit", enabled: true, color: ReferenceStyle.blue) {
                emailError = email.isEmpty; passwordError = password.isEmpty
            }.offset(y: 408.5 + shift)
            legal.offset(y: 497.5 + shift)
        }
    }
    private func iconControl(_ name: String, label: String, id: String, action: @escaping () -> Void) -> some View {
        ReferencePracticeControl(label: label, identifier: id, enabled: true, action: action,
            face: AnyView(ReferenceStyle.image(name).resizable().frame(width: 24, height: 24))).frame(width: 24, height: 24)
    }
    private func title(_ value: String) -> some View {
        Text(value).font(ReferenceStyle.font(26, bold: true)).foregroundStyle(Color(white: 60/255)).frame(width: 375, height: 40)
    }
    private func field(_ placeholder: String, id: String, text: Binding<String>, secure: Bool = false, reservedTrailing: Bool = false) -> some View {
        ZStack(alignment: .topLeading) {
            RoundedRectangle(cornerRadius: 12).fill(Color(white: 247/255)).overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(ReferenceStyle.border, lineWidth: 2))
            RegistrationTextField(text: text, placeholder: placeholder, identifier: id, secure: secure)
                .id(secure).frame(width: secure || reservedTrailing ? 347 : 371, height: 44).offset(x: 2, y: 2)
        }.frame(width: 375, height: 48)
    }
    private func control(_ label: String, id: String, enabled: Bool, color: Color, action: @escaping () -> Void) -> some View {
        ReferencePracticeControl(label: label, identifier: id, enabled: enabled, action: action, face: AnyView(
            Text(label).font(ReferenceStyle.font(15, bold: true)).tracking(0.8).foregroundStyle(enabled ? .white : Color(white: 175/255))
                .frame(width: 375, height: 46).background {
                    RoundedRectangle(cornerRadius: 16).fill(color)
                        .shadow(color: enabled ? Color(red: 24/255, green: 153/255, blue: 214/255) : .clear, radius: 0, y: 4)
                }.frame(height: 50, alignment: .top)))
            .frame(width: 375, height: 50)
    }
    private func method(_ label: String, icon: String, id: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        ReferencePracticeControl(label: label, identifier: id, enabled: enabled, action: action, face: AnyView(
            HStack(spacing: 8) { ReferenceStyle.image("en-registration-" + icon).resizable().frame(width: 20, height: 20); Text(label.uppercased()).font(ReferenceStyle.font(17, bold: true)) }
                .foregroundStyle(ReferenceStyle.blue).frame(width: 375, height: 44)
                .background {
                    RoundedRectangle(cornerRadius: 16).fill(.white)
                        .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                        .shadow(color: ReferenceStyle.border, radius: 0, y: 4)
                }.frame(height: 48, alignment: .top)))
            .frame(width: 375, height: 48)
    }
    private var legal: some View {
        VStack(spacing: 20) {
            Text("登录即视为你已接受我们的服务条款与隐私政策。")
            Text("该网站受 reCAPTCHA Enterprise 保护。Google 隐私政策及服务条款也同时适用。")
        }.font(ReferenceStyle.font(14, weight: 400)).foregroundStyle(Color(white: 175/255)).multilineTextAlignment(.center).frame(width: 375)
    }
}

struct RegistrationTextField: NSViewRepresentable {
    @Binding var text: String
    let placeholder: String
    let identifier: String
    let secure: Bool
    final class Coordinator: NSObject, NSTextFieldDelegate {
        var parent: RegistrationTextField
        init(_ parent: RegistrationTextField) { self.parent = parent }
        func controlTextDidChange(_ notification: Notification) {
            guard let field = notification.object as? NSTextField else { return }
            parent.text = field.stringValue
        }
    }
    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeNSView(context: Context) -> NSTextField {
        let field: NSTextField = secure ? NSSecureTextField() : NSTextField()
        field.isBordered = false; field.drawsBackground = false; field.focusRingType = .none
        field.setContentHuggingPriority(.defaultLow, for: .vertical)
        field.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        field.cell = secure ? RegistrationSecureCell(textCell: "") : RegistrationCell(textCell: "")
        field.isEditable = true; field.isSelectable = true
        field.isBordered = false; field.drawsBackground = false
        field.font = ReferenceStyle.nativeFont(20, weight: 500)
        field.textColor = NSColor(srgbRed: 75/255, green: 75/255, blue: 75/255, alpha: 1)
        field.placeholderString = placeholder; field.stringValue = text; field.delegate = context.coordinator
        field.setAccessibilityLabel(placeholder); field.setAccessibilityIdentifier(identifier)
        return field
    }
    func updateNSView(_ field: NSTextField, context: Context) {
        context.coordinator.parent = self
        // This view owns live edits. Initialize on mount; explicit clear/reveal actions
        // remount with their identity. Replaying a delayed model value here can
        // truncate a multi-character key event during the age-width transition.
    }
}

// Source inputs have 14-point horizontal and 8-point vertical CSS padding.
private final class RegistrationCell: NSTextFieldCell {
    override func drawingRect(forBounds rect: NSRect) -> NSRect { rect.insetBy(dx: 14, dy: 8) }
    override func edit(withFrame rect: NSRect, in view: NSView, editor: NSText, delegate: Any?, event: NSEvent?) {
        super.edit(withFrame: drawingRect(forBounds: rect), in: view, editor: editor, delegate: delegate, event: event)
    }
    override func select(withFrame rect: NSRect, in view: NSView, editor: NSText, delegate: Any?, start: Int, length: Int) {
        super.select(withFrame: drawingRect(forBounds: rect), in: view, editor: editor, delegate: delegate, start: start, length: length)
    }
}
private final class RegistrationSecureCell: NSSecureTextFieldCell {
    override func drawingRect(forBounds rect: NSRect) -> NSRect { rect.insetBy(dx: 14, dy: 8) }
    override func edit(withFrame rect: NSRect, in view: NSView, editor: NSText, delegate: Any?, event: NSEvent?) {
        super.edit(withFrame: drawingRect(forBounds: rect), in: view, editor: editor, delegate: delegate, event: event)
    }
    override func select(withFrame rect: NSRect, in view: NSView, editor: NSText, delegate: Any?, start: Int, length: Int) {
        super.select(withFrame: drawingRect(forBounds: rect), in: view, editor: editor, delegate: delegate, start: start, length: length)
    }
}
