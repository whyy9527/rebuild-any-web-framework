import AppKit
import SwiftUI

/// Original guest login presentation. Remote authentication remains a separate unimplemented branch.
struct ReferenceLogin: View {
    let close: () -> Void
    let signup: () -> Void
    let forgot: () -> Void
    @State private var email = ""
    @State private var password = ""
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .topLeading) {
                Color.white
                Button(action: close) { ReferenceStyle.image("en-path-profile-close").resizable().frame(width:16,height:16) }
                    .buttonStyle(.plain).frame(width:16,height:20.5).offset(x:30,y:30).accessibilityLabel("关闭").accessibilityIdentifier("login-close")
                Button(action:signup) { Text("注册").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(ReferenceStyle.blue)
                    .frame(width:67.6015625,height:46).background { RoundedRectangle(cornerRadius:16).fill(.white).shadow(color:ReferenceStyle.border,radius:0,y:4) }
                    .overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)) }
                    .buttonStyle(.plain).frame(height:50).offset(x:geometry.size.width-97.6015625,y:30).accessibilityIdentifier("login-signup")
                ZStack(alignment:.topLeading) {
                    Text("登录").font(ReferenceStyle.font(26,bold:true)).frame(width:375,height:40).offset(y:57.5)
                    field("邮箱或用户名",id:"login-address",value:$email,width:371,height:44).offset(y:120.5)
                    ZStack(alignment:.topLeading) {
                        RoundedRectangle(cornerRadius:12).fill(Color(white:247/255)).overlay(RoundedRectangle(cornerRadius:12).strokeBorder(ReferenceStyle.border,lineWidth:2))
                        RegistrationTextField(text:$password,placeholder:"密码",identifier:"login-password",secure:true).frame(width:297.0390625,height:56).offset(x:2,y:2)
                        Link(destination:URL(string:"https://www.duolingo.com/forgot_password")!) { Text("忘记密码？").font(ReferenceStyle.font(15,weight:500)).foregroundStyle(ReferenceStyle.disclosureInk).multilineTextAlignment(.center).frame(width:61.9609375,height:56) }
                            .buttonStyle(.plain).environment(\.openURL,OpenURLAction { _ in forgot(); return .handled }).offset(x:297.0390625,y:2).accessibilityIdentifier("login-forgot")
                    }.frame(width:375,height:60).offset(y:180.5)
                    ReferencePracticeControl(label:"登录",identifier:"login-submit",enabled:true,action:{},face:AnyView(Text("登录").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(.white).frame(width:375,height:46).background(ReferenceStyle.blue,in:RoundedRectangle(cornerRadius:16)).shadow(color:Color(red:24/255,green:153/255,blue:214/255),radius:0,y:4).frame(height:50,alignment:.top)))
                        .frame(width:375,height:50).offset(y:264.5)
                    HStack(spacing:8) { Rectangle().fill(ReferenceStyle.border).frame(height:2);Text("或者").font(ReferenceStyle.font(16)).foregroundStyle(ReferenceStyle.disclosureInk);Rectangle().fill(ReferenceStyle.border).frame(height:2) }.frame(width:375,height:20).offset(y:334.5)
                    method("通过谷歌登录",resource:"en-registration-google",id:"login-google").offset(y:374.5)
                    method("通过 Facebook 登录",resource:"en-registration-facebook",id:"login-facebook").offset(y:439.5)
                    method("使用 Apple 登录",resource:"en-login-apple",id:"login-apple").offset(y:504.5)
                    VStack(spacing:20) { Text("登录即视为你已接受我们的服务条款与隐私政策。");Text("该网站受 reCAPTCHA Enterprise 保护。Google 隐私政策及服务条款也同时适用。") }
                        .font(ReferenceStyle.font(14,weight:400)).foregroundStyle(ReferenceStyle.disclosureInk).multilineTextAlignment(.center).frame(width:375).offset(y:595.5)
                }.frame(width:375).offset(x:(geometry.size.width-375)/2)
            }
        }.foregroundStyle(ReferenceStyle.ink)
    }
    private func field(_ placeholder:String,id:String,value:Binding<String>,width:CGFloat,height:CGFloat)->some View {
        ZStack(alignment:.topLeading) { RoundedRectangle(cornerRadius:12).fill(Color(white:247/255)).overlay(RoundedRectangle(cornerRadius:12).strokeBorder(ReferenceStyle.border,lineWidth:2));RegistrationTextField(text:value,placeholder:placeholder,identifier:id,secure:false).frame(width:width,height:height).offset(x:2,y:2) }.frame(width:375,height:48)
    }
    private func method(_ label:String,resource:String,id:String)->some View {
        Button {} label: { HStack(spacing:8) { ReferenceStyle.image(resource).resizable().scaledToFit().frame(width:20,height:20);Text(label).font(ReferenceStyle.font(15,bold:true)) }.foregroundStyle(id=="login-apple" ? ReferenceStyle.ink : ReferenceStyle.blue).frame(width:375,height:46).background { RoundedRectangle(cornerRadius:16).fill(.white).shadow(color:ReferenceStyle.border,radius:0,y:4) }.overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)) }.buttonStyle(.plain).frame(height:50).accessibilityIdentifier(id)
    }
}
