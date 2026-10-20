import SwiftUI

struct ReferenceForgotPassword: View {
    @State private var email = ""
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment:.topLeading) {
                Text("密码忘了？").font(ReferenceStyle.font(25,bold:true)).frame(width:350,height:34).offset(y:174)
                Text("你将收到一封邮件，内含如何重置密码的说明").font(ReferenceStyle.font(17)).frame(width:350,height:20).offset(y:218.5)
                ZStack(alignment:.topLeading) { RoundedRectangle(cornerRadius:12).fill(Color(white:247/255)).overlay(RoundedRectangle(cornerRadius:12).strokeBorder(ReferenceStyle.border,lineWidth:2));RegistrationTextField(text:$email,placeholder:"邮箱",identifier:"forgot-email",secure:false).frame(width:346,height:44).offset(x:2,y:2) }.frame(width:350,height:48).offset(y:262.5)
                Button {} label: { Text("提交").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(.white).frame(width:350,height:46).background { RoundedRectangle(cornerRadius:16).fill(ReferenceStyle.blue).shadow(color:Color(red:24/255,green:153/255,blue:214/255),radius:0,y:4) } }.buttonStyle(.plain).frame(height:50).offset(y:320.5).accessibilityIdentifier("forgot-submit")
            }.frame(width:350).offset(x:(geometry.size.width-350)/2)
        }.foregroundStyle(ReferenceStyle.ink)
    }
}
