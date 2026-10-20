import SwiftUI

/// The explicit observed guest snapshot; cumulative XP is not supplied by this presentation.
struct GuestProfileSnapshot: Decodable {
    struct Achievement: Decodable {
        let title: String
        let level: Int
        let current: Int
        let target: Int
        let description: String
        let resource: String?
    }
    let joined: String
    let streak: Int
    let experience: Int
    let achievements: [Achievement]
    static let observed: Self? = Bundle.module.url(forResource:"guest-profile-snapshot",withExtension:"json",subdirectory:"Reference")
        .flatMap { try? Data(contentsOf:$0) }.flatMap { try? JSONDecoder().decode(Self.self,from:$0) }
}

struct ReferenceGuestProfile: View {
    let avatar: () -> Void
    let achievements: () -> Void
    var avatarState: [String:Int]?
    var animations: Bool
    let languages: () -> Void
    var body: some View {
        if let snapshot = GuestProfileSnapshot.observed {
            VStack(alignment:.leading,spacing:0) {
                ZStack(alignment:.top) {
                    RoundedRectangle(cornerRadius:16).fill(avatarState.flatMap {SourceAvatarCatalog.source.avatarOnProfileDisplayOptions[String($0["BackgroundColor"] ?? 1)]}.map {SourceAvatarCatalog.color($0.backgroundColor)} ?? Color(red:221/255,green:244/255,blue:1))
                    if let state=avatarState {ReferenceAvatarRenderer(states:state,animations:animations,zoom:nil,identifier:"guest-profile-avatar-renderer").frame(width:480,height:224)}
                    else {ReferenceStyle.image("en-guest-avatar").resizable().frame(width:166.125,height:266).offset(y:39)}
                    HStack { Spacer();ReferencePracticeControl(label:"",identifier:"guest-profile-edit",enabled:true,action:avatar,face:AnyView(ReferenceStyle.image("en-guest-edit").resizable().frame(width:18,height:18).frame(width:46,height:46).background(RoundedRectangle(cornerRadius:16).stroke(Color.black.opacity(0.3),lineWidth:2))),fixedFaceSize:true).frame(width:48,height:48).padding(16) }
                }.frame(width:480,height:224).clipShape(RoundedRectangle(cornerRadius:15)).overlay { ReferencePracticeControl(label:"",identifier:"guest-profile-avatar",enabled:true,action:avatar,face:AnyView(Color.clear)).frame(width:220,height:224) }
                HStack {
                    Text(snapshot.joined).accessibilityIdentifier("guest-profile-joined").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk)
                    Spacer()
                    ReferencePracticeControl(label:"",identifier:"guest-profile-languages",enabled:true,action:languages,face:AnyView(ReferenceStyle.image("en-home-56c79be7b1d61ed14ae1").resizable().frame(width:31,height:23.9140625)),fixedFaceSize:true).frame(width:39,height:43.9140625)
                }.frame(height:43.9140625).padding(.top,28)
                Rectangle().fill(ReferenceStyle.border).frame(height:2).padding(.top,22)
                Text("数据统计").font(ReferenceStyle.font(24,bold:true)).foregroundStyle(Color(white:60/255)).frame(height:28).padding(.top,28)
                HStack(spacing:12) {
                    statistic("en-guest-streak",String(snapshot.streak),"连胜天数")
                    statistic("en-guest-xp",String(snapshot.experience),"总经验")
                }.padding(.top,16)
                HStack {
                    Text("成就").font(ReferenceStyle.font(24,bold:true)).foregroundStyle(Color(white:60/255))
                    Spacer()
                    ReferencePracticeControl(label:"显示全部",identifier:"guest-profile-achievements",enabled:true,action:achievements,face:AnyView(Text("显示全部").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(ReferenceStyle.blue)),role:.link).frame(width:63.203125,height:18)
                }.frame(height:28).padding(.top,28)
                VStack(spacing:0) {
                    ForEach(Array(snapshot.achievements.enumerated()),id:\.offset) { index,item in
                        if index>0 { Rectangle().fill(ReferenceStyle.border).frame(height:2) }
                        HStack(spacing:30) {
                            ZStack(alignment:.bottom) {
                                if let resource=item.resource { ReferenceStyle.image(resource).resizable().frame(width:77,height:95.859375) }
                                Text("第 \(item.level) 级").font(ReferenceStyle.font(11,bold:true)).foregroundStyle(.white).padding(.bottom,12)
                            }.frame(width:77,height:95.859375)
                            VStack(alignment:.leading,spacing:16) {
                                HStack {Text(item.title).font(ReferenceStyle.font(19,bold:true));Spacer();Text("\(item.current)/\(item.target)").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.disclosureInk)}
                                GeometryReader { g in
                                    Capsule().fill(ReferenceStyle.border)
                                    Capsule().fill(Color(red:1,green:204/255,blue:0)).frame(width:g.size.width*CGFloat(item.current)/CGFloat(item.target))
                                }.frame(height:14)
                                Text(item.description).font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk)
                            }
                        }.padding(20).frame(height:135.859375)
                    }
                }.overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)).padding(.top,16)
            }.frame(width:480,alignment:.topLeading)
        }
    }
    private func statistic(_ resource:String,_ value:String,_ label:String) -> some View {
        HStack(alignment:.top,spacing:15) {
            ReferenceStyle.image(resource).resizable().scaledToFit().frame(width:21,height:29)
            VStack(alignment:.leading,spacing:4) {
                Text(value).font(ReferenceStyle.font(20,bold:true)).foregroundStyle(Color(white:60/255))
                Text(label).font(ReferenceStyle.font(16)).foregroundStyle(ReferenceStyle.disclosureInk)
            }
            Spacer(minLength:0)
        }.padding(.horizontal,26).padding(.top,14).frame(width:234,height:78,alignment:.topLeading)
            .overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2))
    }
}

struct ReferenceGuestProfileIntroduction: View {
    let start: () -> Void
    let later: () -> Void
    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
            VStack(spacing:0) {
                ReferenceStyle.image("en-guest-intro").resizable().frame(width:336,height:160).padding(.top,40)
                Text("制作专属虚拟头像！").font(ReferenceStyle.font(24,bold:true)).padding(.top,18)
                ReferencePracticeControl(label:"开始",identifier:"guest-profile-start",enabled:true,action:start,face:AnyView(Text("开始").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(.white).frame(width:336,height:46).background(ReferenceStyle.blue,in:RoundedRectangle(cornerRadius:16)).compositingGroup().shadow(color:Color(red:24/255,green:153/255,blue:214/255),radius:0,y:4).frame(height:50,alignment:.top))).frame(width:336,height:50).padding(.top,32)
                ReferencePracticeControl(label:"下次再说",identifier:"guest-profile-later",enabled:true,action:later,face:AnyView(Text("下次再说").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(ReferenceStyle.blue))).frame(width:336,height:32).padding(.top,20)
                Spacer(minLength:0)
            }.frame(width:384,height:402.5).background(.white,in:RoundedRectangle(cornerRadius:16))
        }
    }
}

struct ReferenceGuestAchievementsError: View {
    let home: () -> Void
    var body: some View {
        GeometryReader { g in
            ZStack(alignment:.topLeading) {
                ReferenceStyle.image("en-error-sad").resizable().frame(width:200,height:202.6953125).offset(y:16)
                Text("Error 404").accessibilityIdentifier("guest-profile-error").font(ReferenceStyle.errorFont(32,bold:true)).foregroundStyle(Color(white:60/255)).frame(width:420,height:40,alignment:.leading).offset(x:248)
                Text("Sorry, the page you were looking for doesn’t exist. Try going to").font(ReferenceStyle.errorFont(18)).foregroundStyle(Color(white:175/255)).lineSpacing(7.8).frame(width:420,height:57.6,alignment:.topLeading).offset(x:248,y:92)
                errorLink("duolingo.com",id:"guest-error-home",width:106.890625,action:home).offset(x:314.3515625,y:124.953125)
                Text(", or follow us on").font(ReferenceStyle.errorFont(18)).foregroundStyle(Color(white:175/255)).frame(width:127.375,height:21,alignment:.leading).offset(x:421.2421875,y:124.953125)
                Link("Twitter",destination:URL(string:"https://twitter.com/duolingo")!).font(ReferenceStyle.errorFont(18,bold:true)).foregroundStyle(Color(white:175/255)).frame(width:57.265625,height:21).accessibilityIdentifier("guest-error-twitter").offset(x:548.6171875,y:124.953125)
                Text("or").font(ReferenceStyle.errorFont(18)).foregroundStyle(Color(white:175/255)).frame(width:20.9765625,height:21,alignment:.leading).offset(x:605.8828125,y:124.953125)
                Link("Facebook",destination:URL(string:"http://facebook.com/duolingo")!).font(ReferenceStyle.errorFont(18,bold:true)).foregroundStyle(Color(white:175/255)).frame(width:75.296875,height:21).accessibilityIdentifier("guest-error-facebook").offset(x:248,y:153.75)
                Text(".").font(ReferenceStyle.errorFont(18)).foregroundStyle(Color(white:175/255)).frame(width:4.25,height:21).offset(x:323.296875,y:153.75)
                ReferenceStyle.image("en-error-logo").resizable().frame(width:119.5,height:28).offset(x:248,y:204.046875)
                ReferencePracticeControl(label:"",identifier:"guest-error-logo",enabled:true,action:home,face:AnyView(Color.clear),role:.link,fixedFaceSize:true).frame(width:119.5,height:21).offset(x:248,y:215.546875)
            }.frame(width:668,height:243.5,alignment:.topLeading).offset(x:(g.size.width-668)/2,y:(g.size.height-243.5)/2)
        }.background(.white)
    }
    private func errorLink(_ label:String,id:String,width:CGFloat,action:@escaping ()->Void) -> some View {
        ReferencePracticeControl(label:label,identifier:id,enabled:true,action:action,face:AnyView(Text(label).font(ReferenceStyle.errorFont(18,bold:true)).foregroundStyle(Color(white:175/255)).fixedSize()),role:.link,fixedFaceSize:true).frame(width:width,height:21)
    }
}
