import SwiftUI

/// Actual guest Legendary entry. Start requests the observed profile interruption.
struct ReferenceLegendary: View {
    let hearts: Int
    let start: () -> Void
    let quit: () -> Void
    private let gold = Color(red:255/255,green:200/255,blue:0)
    private let goldInk = Color(red:174/255,green:104/255,blue:2/255)
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment:.topLeading) {
                Color(red:24/255,green:24/255,blue:24/255)
                HStack(spacing:8) { ReferenceStyle.image("en-legendary-heart").resizable().frame(width:32,height:32);Text(String(hearts)).font(ReferenceStyle.font(15,bold:true)).foregroundStyle(Color(red:255/255,green:75/255,blue:75/255)) }
                    .frame(width:64,height:32).offset(x:geometry.size.width-96,y:40)
                ZStack(alignment:.topLeading) {
                    ReferenceStyle.image("en-legendary-art").resizable().frame(width:442,height:442).offset(x:-11,y:16)
                    Text("来向我们展示你的传奇实力吧").font(ReferenceStyle.font(24,bold:true)).frame(width:420,height:26).offset(y:458)
                    Text("完成这个超硬核挑战，晋升到传奇等级！").font(ReferenceStyle.font(17)).frame(width:420,height:20).offset(y:508)
                    ReferencePracticeControl(label:"开始 +40 经验",identifier:"legendary-start",enabled:true,action:start,face:AnyView(
                        Text("开始 +40 经验").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(goldInk).frame(width:388,height:46)
                            .background { stripedGold.frame(width:388,height:46).clipShape(RoundedRectangle(cornerRadius:16)).shadow(color:Color(red:231/255,green:166/255,blue:1/255),radius:0,y:4) }.frame(height:50,alignment:.top)),role:.link)
                        .frame(width:388,height:50).offset(x:16,y:552)
                    ReferencePracticeControl(label:"下次再说",identifier:"legendary-quit",enabled:true,action:quit,face:AnyView(Text("下次再说").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(.white).frame(width:95.203125,height:48)))
                        .frame(width:95.203125,height:48).offset(x:162.3984375,y:610)
                }.frame(width:420,height:682,alignment:.topLeading).offset(x:(geometry.size.width-420)/2,y:(geometry.size.height-682)/2)
            }
        }.foregroundStyle(.white)
    }
    private var stripedGold: some View {
        Canvas { context,size in
            context.fill(Path(CGRect(origin:.zero,size:size)),with:.color(gold))
            // Original 136-degree 10/40/53/71-percent stripe stops, no replacement artwork.
            let span = size.width * 0.72 + size.height * 0.69
            for (a,b) in [(0.10,0.40),(0.53,0.71)] {
                var path=Path();path.move(to:CGPoint(x:span*a/0.72,y:0));path.addLine(to:CGPoint(x:span*b/0.72,y:0));path.addLine(to:CGPoint(x:(span*b-size.height*0.69)/0.72,y:size.height));path.addLine(to:CGPoint(x:(span*a-size.height*0.69)/0.72,y:size.height));path.closeSubpath()
                context.fill(path,with:.color(Color(red:1,green:231/255,blue:0).opacity(0.5)))
            }
        }
    }
}
