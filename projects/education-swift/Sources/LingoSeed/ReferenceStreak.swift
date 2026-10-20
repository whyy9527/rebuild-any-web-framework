import SwiftUI

private let streakOrange = Color(red:1,green:150/255,blue:0)
private let streakClubCopy = "连胜达到 7 天，就能加入连胜精英俱⁠乐⁠部，赢取专⁠属⁠奖⁠励⁠。"

/// Source: english-streak-followup-v1. Multi-day history and animation timing
/// remain unknown; the current observed guest has one active day.
struct ReferenceStreakPopover: View {
    let streak: Int
    let today: Date
    let details: () -> Void
    private var weekday: Int {Calendar(identifier:.gregorian).component(.weekday,from:today)-1}
    var body: some View {
        ZStack(alignment:.topLeading) {
            RoundedRectangle(cornerRadius:15,style:.circular).fill(streakOrange)
            Rectangle().fill(.white).frame(width:384,height:246).offset(x:2,y:242)
            Text("\(streak) 天连胜").font(ReferenceStyle.font(25,bold:true)).foregroundStyle(.white).fixedSize().offset(x:22,y:28)
            Text("你创下了迄今最长的连胜纪录！").font(ReferenceStyle.font(17)).foregroundStyle(.white).fixedSize().offset(x:22,y:70)
            ReferenceStyle.image("en-streak-d1a7e56a31778321").resizable().frame(width:64,height:77).offset(x:292,y:38)
            ZStack(alignment:.topLeading) {
                RoundedRectangle(cornerRadius:12).fill(.white).frame(width:344,height:87)
                ForEach(0..<7,id:\.self) { day in
                    Text(["日","一","二","三","四","五","六"][day]).font(ReferenceStyle.font(17,bold:true)).foregroundStyle(day==weekday ? streakOrange : ReferenceStyle.disclosureInk).frame(width:34,height:20).offset(x:21.28125+CGFloat(day)*44.5703125,y:14.5)
                    Circle().fill(ReferenceStyle.border).frame(width:34,height:34).offset(x:21.28125+CGFloat(day)*44.5703125,y:41)
                }
                ReferenceStyle.image("en-streak-688fdeb22d27e719").resizable().frame(width:46.199951,height:115.5).offset(x:15.18945+CGFloat(weekday)*44.5703125,y:-40.75)
            }.frame(width:344,height:87).clipped().offset(x:22,y:135)
            RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2).frame(width:344,height:140).offset(x:22,y:262)
            ReferenceStyle.image("en-streak-c20e2fea2873a615").resizable().frame(width:60,height:60).offset(x:42,y:288)
            Text("连胜精英俱乐部").font(ReferenceStyle.font(17,bold:true)).fixedSize().offset(x:126,y:282)
            Text(streakClubCopy).font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk).lineSpacing(4).frame(width:218.828125,alignment:.leading).offset(x:126,y:314)
            ReferencePracticeControl(label:"查看更多",identifier:"streak-details",enabled:true,action:details,face:AnyView(
                Text("查看更多").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(.white).frame(width:344,height:46).background(streakOrange,in:RoundedRectangle(cornerRadius:16)).shadow(color:Color(red:205/255,green:121/255,blue:0),radius:0,y:4).frame(height:50,alignment:.top)
            ),fixedFaceSize:true).frame(width:344,height:50).offset(x:22,y:418)
        }.frame(width:388,height:490).clipShape(RoundedRectangle(cornerRadius:15,style:.circular))
            .overlay(RoundedRectangle(cornerRadius:15,style:.circular).strokeBorder(ReferenceStyle.border,lineWidth:2))
            .foregroundStyle(ReferenceStyle.ink)
    }
}

struct ReferenceStreakCalendar: View {
    let streak: Int
    let today: Date
    let close: () -> Void
    @State private var monthOffset = 0
    @State private var scroll: CGFloat = 0
    private let calendar = Calendar(identifier:.gregorian)
    private var month: Date {calendar.date(byAdding:.month,value:monthOffset,to:today)!}
    private var days: Int {calendar.range(of:.day,in:.month,for:month)!.count}
    private var rows: Int {
        let first=calendar.date(from:calendar.dateComponents([.year,.month],from:month))!
        return (calendar.component(.weekday,from:first)-1+days+6)/7
    }
    private var calendarHeight: CGFloat {107+CGFloat(rows)*44}
    private var contentHeight: CGFloat {725+calendarHeight}
    var body: some View {
        GeometryReader { proxy in
            ZStack {
                Color.black.opacity(0.4)
                ZStack(alignment:.topLeading) {
                    ScrollView(.vertical) {
                        content.background(ReferenceScrollOffset {scroll=max(0,$0)})
                    }.scrollIndicators(.hidden)
                    if scroll > 0 {
                        Rectangle().fill(streakOrange).frame(height:64)
                        Text("连胜").font(ReferenceStyle.font(17,bold:true)).foregroundStyle(.white).frame(width:480,height:20).offset(y:21)
                    }
                    ReferencePracticeControl(label:"",identifier:"streak-close",enabled:true,action:close,face:AnyView(
                        ReferenceStyle.image("en-streak-0418963dae849437").resizable().frame(width:16,height:16).frame(width:32,height:32).background(.white,in:Circle())
                    ),fixedFaceSize:true).frame(width:32,height:32).offset(x:20,y:16)
                }.frame(width:480,height:max(0,proxy.size.height-96)).background(.white).clipShape(RoundedRectangle(cornerRadius:16,style:.circular))
            }.frame(width:proxy.size.width,height:proxy.size.height)
        }.foregroundStyle(ReferenceStyle.ink)
    }
    private var content: some View {
        ZStack(alignment:.topLeading) {
            Rectangle().fill(streakOrange).frame(width:480,height:300)
            Text("\(streak) 天连胜").font(ReferenceStyle.font(32,bold:true)).foregroundStyle(.white).fixedSize().offset(x:24,y:101)
            ReferenceStyle.image("en-streak-d1a7e56a31778321").resizable().frame(width:80,height:98).offset(x:360,y:64)
            RoundedRectangle(cornerRadius:12).fill(.white).frame(width:432,height:80).offset(x:24,y:196)
            ReferenceStyle.image("en-streak-4c7c824860bcb2a2").resizable().frame(width:40,height:40).offset(x:44,y:216)
            Text("你创下了迄今最长的连胜纪录！").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk).fixedSize().offset(x:104,y:226)
            Text("连胜日历").font(ReferenceStyle.font(25,bold:true)).fixedSize().accessibilityIdentifier("streak-calendar-heading").offset(x:24,y:326)
            monthGrid.offset(x:24,y:366)
            Text("连胜目标").font(ReferenceStyle.font(25,bold:true)).fixedSize().offset(x:24,y:calendarHeight+392)
            goal.offset(x:24,y:calendarHeight+432)
            Text("连胜精英俱乐部").font(ReferenceStyle.font(25,bold:true)).fixedSize().offset(x:24,y:calendarHeight+537)
            club.offset(x:24,y:calendarHeight+581)
        }.frame(width:480,height:contentHeight,alignment:.topLeading)
    }
    private var monthGrid: some View {
        ZStack(alignment:.topLeading) {
            RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)
            // The source carousel renders neighbouring months too. Its outer
            // modal clips them; the small edge fragments are real paint.
            ForEach(-1...1,id:\.self) { delta in
                monthFace(offset:monthOffset+delta).offset(x:CGFloat(delta)*412)
            }
            monthArrow(previous:true).offset(x:10,y:22)
            monthArrow(previous:false).offset(x:408,y:22)
        }.frame(width:432,height:calendarHeight)
    }
    private func monthFace(offset:Int)->some View {
        let date=calendar.date(byAdding:.month,value:offset,to:today)!
        let beginning=calendar.date(from:calendar.dateComponents([.year,.month],from:date))!
        let count=calendar.range(of:.day,in:.month,for:date)!.count
        let blank=calendar.component(.weekday,from:beginning)-1
        return ZStack(alignment:.topLeading) {
            Text(String(calendar.component(.year,from:date))+"年"+String(calendar.component(.month,from:date))+"月").font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.secondaryInk).frame(width:432,height:20).offset(y:18.5)
            ForEach(0..<7,id:\.self) { col in
                Text(["日","一","二","三","四","五","六"][col]).font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).frame(width:36,height:20).offset(x:19+CGFloat(col)*59.6640625,y:56)
            }
            ForEach(1...count,id:\.self) { day in
                let slot=blank+day-1
                let active=offset==0 && day==calendar.component(.day,from:today)
                Text(String(day)).font(ReferenceStyle.font(17,bold:true)).foregroundStyle(active ? .white : ReferenceStyle.disclosureInk).frame(width:30,height:30)
                    .background(active ? streakOrange : .clear,in:Circle())
                    .offset(x:22+CGFloat(slot%7)*59.6640625,y:91+CGFloat(slot/7)*44)
            }
        }.frame(width:432,height:calendarHeight)
    }
    private func monthArrow(previous:Bool)->some View {
        ReferencePracticeControl(label:"",identifier:previous ? "streak-prev" : "streak-next",enabled:true,action:{monthOffset += previous ? -1 : 1},face:AnyView(ReferenceStyle.image(previous ? "en-streak-prev" : "en-streak-next").resizable().frame(width:14,height:14)),fixedFaceSize:true).frame(width:14,height:14)
    }
    private var goal: some View {
        ZStack(alignment:.topLeading) {
            RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)
            UnevenRoundedRectangle(topLeadingRadius:9,bottomLeadingRadius:9).fill(ReferenceStyle.border).frame(width:332,height:18).offset(x:46,y:30.5)
            ReferenceStyle.image("en-streak-196e4bf1a2288e97").resizable().frame(width:36,height:39).offset(x:18,y:18)
            Text(String(streak)).font(ReferenceStyle.font(14,bold:true)).foregroundStyle(Color(red:1,green:75/255,blue:75/255)).frame(width:36,height:16.5).offset(x:18,y:33.5)
            ReferenceStyle.image("en-streak-3f517c0a30c58188").resizable().frame(width:36,height:37).offset(x:378,y:20)
            Text("7").font(ReferenceStyle.font(14,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).frame(width:36,height:16.5).offset(x:378,y:33.5)
        }.frame(width:432,height:79)
    }
    private var club: some View {
        ZStack(alignment:.topLeading) {
            RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)
            ReferenceStyle.image("en-streak-c20e2fea2873a615").resizable().frame(width:72,height:72).offset(x:30,y:26)
            Text(streakClubCopy).font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk).lineSpacing(4).frame(width:252.828125,alignment:.leading).offset(x:126,y:38)
        }.frame(width:432,height:120)
    }
}
