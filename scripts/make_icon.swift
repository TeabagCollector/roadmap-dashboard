import AppKit
import CoreText

// Original vector artwork. System typography is outlined; no font file is redistributed.
func color(_ hex:UInt32,_ alpha:CGFloat=1)->NSColor {
    NSColor(calibratedRed:CGFloat((hex>>16)&255)/255,green:CGFloat((hex>>8)&255)/255,blue:CGFloat(hex&255)/255,alpha:alpha)
}
let font=CTFontCreateWithName("AmericanTypewriter" as CFString,660,nil)
var character:UniChar=68,glyph:CGGlyph=0
CTFontGetGlyphsForCharacters(font,&character,&glyph,1)
let original=CTFontCreatePathForGlyph(font,glyph,nil)!
let bounds=original.boundingBoxOfPath
var offset=CGAffineTransform(translationX:492-bounds.midX,y:538-bounds.midY)
let letter=original.copy(using:&offset)!

func render(_ size:Int)->Data {
    let rep=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:size,pixelsHigh:size,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
    let ctx=NSGraphicsContext(bitmapImageRep:rep)!
    NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=ctx
    let c=ctx.cgContext;c.scaleBy(x:CGFloat(size)/1024,y:CGFloat(size)/1024)
    c.setAllowsAntialiasing(true);c.setShouldAntialias(true)
    let tile=NSBezierPath(roundedRect:NSRect(x:82,y:82,width:860,height:860),xRadius:190,yRadius:190)
    NSGraphicsContext.saveGraphicsState()
    let shadow=NSShadow();shadow.shadowColor=color(0x544B3A,0.22);shadow.shadowBlurRadius=24;shadow.shadowOffset=NSSize(width:0,height:-13);shadow.set()
    color(0xF4EEDF).setFill();tile.fill();NSGraphicsContext.restoreGraphicsState()
    NSGradient(starting:color(0xEDE5D5),ending:color(0xFCF8ED))!.draw(in:tile,angle:90)
    color(0xFFFFFF,0.68).setStroke();tile.lineWidth=2;tile.stroke()
    c.addPath(letter);c.setFillColor(color(0x34443C).cgColor);c.fillPath()
    let badge=NSBezierPath(ovalIn:NSRect(x:630,y:174,width:224,height:224))
    NSGraphicsContext.saveGraphicsState()
    let badgeShadow=NSShadow();badgeShadow.shadowColor=color(0x34443C,0.16);badgeShadow.shadowBlurRadius=16;badgeShadow.shadowOffset=NSSize(width:0,height:-6);badgeShadow.set();color(0x799B83).setFill();badge.fill();NSGraphicsContext.restoreGraphicsState()
    let check=NSBezierPath();check.move(to:NSPoint(x:689,y:286));check.line(to:NSPoint(x:726,y:248));check.line(to:NSPoint(x:793,y:324));check.lineWidth=18;check.lineCapStyle = .round;check.lineJoinStyle = .round;color(0xFBF8EF).setStroke();check.stroke()
    NSGraphicsContext.restoreGraphicsState()
    let png=rep.representation(using:.png,properties:[:])!
    // AppKit adds ancillary text to generated PNGs. Keep only artwork data.
    var clean=Data(png.prefix(8)),position=8
    while position+12<=png.count {
        let count=png[position..<position+4].reduce(0) { ($0<<8)|Int($1) }
        let end=position+12+count
        precondition(end<=png.count)
        let kind=String(data:png[position+4..<position+8],encoding:.ascii) ?? ""
        if !["tEXt","zTXt","iTXt","eXIf"].contains(kind) { clean.append(png[position..<end]) }
        position=end
    }
    return clean
}
func svgPath(_ path:CGPath)->String {
    var parts:[String]=[]
    func p(_ point:CGPoint)->String { String(format:"%.3f %.3f",Double(point.x),Double(point.y)) }
    path.applyWithBlock { e in
        switch e.pointee.type {
        case .moveToPoint:parts.append("M"+p(e.pointee.points[0]))
        case .addLineToPoint:parts.append("L"+p(e.pointee.points[0]))
        case .addQuadCurveToPoint:parts.append("Q"+p(e.pointee.points[0])+" "+p(e.pointee.points[1]))
        case .addCurveToPoint:parts.append("C"+p(e.pointee.points[0])+" "+p(e.pointee.points[1])+" "+p(e.pointee.points[2]))
        case .closeSubpath:parts.append("Z")
        @unknown default:break
        }
    }
    return parts.joined(separator:" ")
}
let output=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
try render(1024).write(to:output.appendingPathComponent("icon.png"))
try render(256).write(to:output.appendingPathComponent("icon-preview.png"))
let svg="""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" role="img" aria-label="Dashboard for Codex">
<defs><linearGradient id="paper" x2="0" y2="1"><stop stop-color="#fcf8ed"/><stop offset="1" stop-color="#ede5d5"/></linearGradient><filter id="shadow" x="-25%" y="-25%" width="150%" height="150%"><feDropShadow dy="13" stdDeviation="12" flood-color="#544b3a" flood-opacity=".22"/></filter></defs>
<rect x="82" y="82" width="860" height="860" rx="190" fill="url(#paper)" stroke="#fff" stroke-opacity=".68" stroke-width="2" filter="url(#shadow)"/>
<g transform="translate(0 1024) scale(1 -1)"><path d="\(svgPath(letter))" fill="#34443c"/><circle cx="742" cy="286" r="112" fill="#799b83"/><path d="M689 286 L726 248 L793 324" fill="none" stroke="#fbf8ef" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/></g></svg>
"""
try Data(svg.utf8).write(to:output.appendingPathComponent("icon.svg"))
let iconset=output.appendingPathComponent("AppIcon.iconset",isDirectory:true)
try FileManager.default.createDirectory(at:iconset,withIntermediateDirectories:true)
for pointSize in [16,32,128,256,512] {
    for scale in [1,2] {
        let filename="icon_\(pointSize)x\(pointSize)"+(scale==2 ? "@2x" : "")+".png"
        try render(pointSize*scale).write(to:iconset.appendingPathComponent(filename))
    }
}
let tool=Process();tool.executableURL=URL(fileURLWithPath:"/usr/bin/iconutil");tool.arguments=["-c","icns",iconset.path,"-o",output.appendingPathComponent("AppIcon.icns").path];try tool.run();tool.waitUntilExit();guard tool.terminationStatus==0 else { fatalError("iconutil failed") }
try FileManager.default.removeItem(at:iconset)
print("Generated original Dashboard icon in \(output.lastPathComponent)")
