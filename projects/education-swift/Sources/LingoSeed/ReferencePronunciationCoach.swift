import SwiftUI

/// The archived original SVG supplies the exact spotlight path. Bubble bounds
/// are reconstructed from its captured pixels; CSS bounds/onset remain unverified.
struct ReferencePronunciationCoach:View {
    let dismiss:()->Void
    let navigate:()->Void
    var body:some View {
        GeometryReader {g in
            ZStack(alignment:.topLeading) {
                CoachMask().fill(.black.opacity(0.4),style:FillStyle(eoFill:true)).allowsHitTesting(false)
                CoachMouseSurface(dismiss:dismiss,navigate:navigate)
                ZStack {
                    RoundedRectangle(cornerRadius:15).fill(.white)
                    Text("在这里学习英语字母！").font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.ink)
                        .accessibilityIdentifier("pronunciation-coach-title")
                }.frame(width:275.59375,height:67).offset(x:134,y:144.5)
                Path {p in p.move(to:CGPoint(x:134,y:169));p.addLine(to:CGPoint(x:126,y:177));p.addLine(to:CGPoint(x:134,y:185));p.closeSubpath()}.fill(.white)
            }.frame(width:g.size.width,height:g.size.height,alignment:.topLeading)
        }
    }
}
private struct CoachMask:Shape {
    func path(in rect:CGRect)->Path {
        var p=Path(rect)
        p.addRoundedRect(in:CGRect(x:15.80078125,y:152,width:110,height:52),cornerSize:CGSize(width:26,height:26))
        return p
    }
}

private struct CoachMouseSurface:NSViewRepresentable {
    let dismiss:()->Void
    let navigate:()->Void
    final class Surface:NSView {
        var dismiss:(()->Void)?
        var navigate:(()->Void)?
        override var isFlipped:Bool {true}
        override func acceptsFirstMouse(for event:NSEvent?)->Bool {true}
        override func mouseDown(with event:NSEvent) {
            let p=convert(event.locationInWindow,from:nil)
            let hole=NSBezierPath(roundedRect:NSRect(x:15.80078125,y:152,width:110,height:52),xRadius:26,yRadius:26)
            if hole.contains(p) {navigate?()} else {dismiss?()}
        }
        override func accessibilityPerformPress()->Bool {dismiss?();return true}
    }
    func makeNSView(context:Context)->Surface {
        let view=Surface();view.setAccessibilityElement(true);view.setAccessibilityRole(.button)
        view.setAccessibilityIdentifier("pronunciation-coach-dismiss");view.setAccessibilityEnabled(true);return view
    }
    func updateNSView(_ view:Surface,context:Context) {view.dismiss=dismiss;view.navigate=navigate}
}
