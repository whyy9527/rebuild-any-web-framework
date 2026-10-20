import SwiftUI

struct ReferenceShop: View {
    let gems: Int
    let create: () -> Void
    var body: some View {
        ZStack(alignment:.topLeading) {
            VStack(alignment:.leading,spacing:0) {
                Text("红心").font(ReferenceStyle.font(24,bold:true)).frame(height:28).offset(y:-3)
                Rectangle().fill(ReferenceStyle.border).frame(height:2).padding(.top,0)
                HStack(alignment:.top,spacing:10) {
                    ReferenceStyle.image("en-shop-heart").resizable().scaledToFit().frame(width:100,height:100)
                    VStack(alignment:.leading,spacing:16) { Text("补心").font(ReferenceStyle.font(19,bold:true));Text("用宝石重新获取满心，就能继续学习！犯错也不用担心咯！").font(ReferenceStyle.font(17)).lineSpacing(8).frame(width:255,alignment:.leading) }.padding(.top,11.5)
                    Spacer(minLength:0)
                }.padding(.top,66)
                Text("道具").font(ReferenceStyle.font(24,bold:true)).frame(height:28).padding(.top,59.5)
                Rectangle().fill(ReferenceStyle.border).frame(height:2).padding(.top,22)
                HStack(alignment:.top,spacing:10) {
                    ReferenceStyle.image("en-shop-freeze").resizable().scaledToFit().frame(width:100,height:100)
                    VStack(alignment:.leading,spacing:16) { HStack { Text("连胜激冻").font(ReferenceStyle.font(19,bold:true));Text("已装备 2/2").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(ReferenceStyle.green).padding(.horizontal,8).padding(.vertical,4).background(Color(red:229/255,green:255/255,blue:204/255),in:Capsule()) };Text("即使一整天不练习，你的连胜天数也能保持不变。").font(ReferenceStyle.font(17)).lineSpacing(8).frame(width:187,alignment:.leading) }.padding(.top,11.5)
                    Spacer(minLength:0)
                }.padding(.top,16)
            }
            status("已满").offset(x:330,y:75)
            status("已装备").offset(x:330,y:303.5)
            LinearGradient(stops:[.init(color:.white,location:0),.init(color:.white.opacity(0.8),location:0.5),.init(color:.white.opacity(0.3),location:1)],startPoint:.top,endPoint:.bottom).frame(width:480,height:417)
            Text("你赚取了 \(gems) 颗宝石！ 创建个人档案，在小店中就能使用邻角啦！").font(ReferenceStyle.font(28,bold:true)).multilineTextAlignment(.center).frame(width:366,height:105).offset(x:57.015625,y:33.5)
            Button(action:create) { Text("创建档案").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(.white).frame(width:266,height:46).background { RoundedRectangle(cornerRadius:16).fill(ReferenceStyle.green).shadow(color:Color(red:70/255,green:163/255,blue:2/255),radius:0,y:4) } }.buttonStyle(.plain).frame(width:266,height:50).offset(x:107,y:180).accessibilityIdentifier("shop-create-profile")
        }.frame(width:480,height:417).foregroundStyle(ReferenceStyle.ink)
    }
    private func status(_ text:String)->some View { Text(text).font(ReferenceStyle.font(15,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).frame(width:150,height:46).background(.white,in:RoundedRectangle(cornerRadius:16)).overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)) }
}
