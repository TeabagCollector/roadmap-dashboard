import AppKit
import Carbon
@preconcurrency import WebKit

final class FloatingPanel: NSPanel {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }
}
final class DragStrip: NSView {
    private var grabOffset:NSPoint?
    var onGrab:(()->Void)?
    override func acceptsFirstMouse(for event:NSEvent?)->Bool { true }
    override func resetCursorRects() { addCursorRect(bounds,cursor:.openHand) }
    override func mouseDown(with event: NSEvent) {
        guard let window=window else { return }
        let point=window.convertPoint(toScreen:event.locationInWindow)
        grabOffset=NSPoint(x:point.x-window.frame.minX,y:point.y-window.frame.minY)
        onGrab?()
    }
    override func mouseDragged(with event:NSEvent) {
        guard let window=window,let offset=grabOffset else { return }
        let point=window.convertPoint(toScreen:event.locationInWindow)
        window.setFrameOrigin(NSPoint(x:point.x-offset.x,y:point.y-offset.y))
    }
    override func mouseUp(with event:NSEvent) { grabOffset=nil }
}
final class MonitorDelegate: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, NSWindowDelegate {
    var panel: FloatingPanel!
    var web: WKWebView!
    var statusItem: NSStatusItem!
    var timer: Timer?
    var watcher: Process?
    var snapshotHash: Data?
    var root: URL!
    var dataRoot: URL!
    var baseRoot:URL!
    var connection:[String:Any]=[:]
    var setupBusy=false
    var onboardingQA=CommandLine.arguments.contains("--onboarding-smoke")
    var python = "python3"
    var liveMode = CommandLine.arguments.contains("--live")
    var language = "zh"
    func argument(_ key:String)->String? {
        let args=CommandLine.arguments
        guard let i=args.firstIndex(of:key),i+1<args.count else { return nil }
        return args[i+1]
    }
    var ready = false
    var qa = CommandLine.arguments.contains("--smoke") || CommandLine.arguments.contains("--roadmap-smoke") || CommandLine.arguments.contains("--roadmap-restore")
    var restore = CommandLine.arguments.contains("--restore-smoke")
    var captureOnly = CommandLine.arguments.contains("--capture")
    var requestBusy = false
    var hotKey: EventHotKeyRef?
    var hotKeyHandler: EventHandlerRef?
    var hotKeyPressed = false
    let hotKeyID = EventHotKeyID(signature:0x44415348,id:1) // DASH
    var hotKeyQA = CommandLine.arguments.contains("--hotkey-smoke")

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        guard let resources=Bundle.main.resourceURL else { NSApp.terminate(nil);return }
        root=resources.appendingPathComponent("runtime",isDirectory:true)
        language=argument("--language") ?? (Locale.preferredLanguages.first?.hasPrefix("zh") == true ? "zh" : "en")
        let support=FileManager.default.urls(for:.applicationSupportDirectory,in:.userDomainMask).first!
        baseRoot=URL(fileURLWithPath:argument("--base") ?? argument("--data") ?? support.appendingPathComponent("RoadmapDashboardPreview").path,isDirectory:true)
        if let data=try? Data(contentsOf:baseRoot.appendingPathComponent("connection.json")),let value=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] { connection=value }
        if !qa && !restore && !captureOnly && !CommandLine.arguments.contains("--demo") { liveMode=liveMode || connection["enabled"] as? Bool == true }
        if let data=try? Data(contentsOf:baseRoot.appendingPathComponent("installation.json")),let value=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any],let installed=value["python"] as? String,FileManager.default.isExecutableFile(atPath:installed) { python=installed }
        let bundledPython=resources.appendingPathComponent("python/bin/python3")
        if FileManager.default.isExecutableFile(atPath:bundledPython.path) { python=bundledPython.path }
        if let location=argument("--data") { dataRoot=URL(fileURLWithPath:location,isDirectory:true) }
        else { dataRoot=baseRoot.appendingPathComponent(liveMode ? "live" : "demo",isDirectory:true) }
        try? FileManager.default.createDirectory(at:dataRoot,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
        if !liveMode { prepareDemo() }
        if liveMode && !qa && !restore && !captureOnly && !hotKeyQA { startWatcher() }
        panel = FloatingPanel(contentRect:NSRect(x:0,y:0,width:400,height:660),styleMask:[.titled,.closable,.resizable,.fullSizeContentView],backing:.buffered,defer:false)
        panel.title = "Dashboard"
        panel.titleVisibility = .hidden
        panel.titlebarAppearsTransparent = true
        panel.isReleasedWhenClosed = false
        panel.hidesOnDeactivate = false
        panel.level = .normal
        panel.collectionBehavior = [.canJoinAllSpaces,.fullScreenAuxiliary]
        panel.minSize = NSSize(width:320,height:460)
        panel.maxSize = NSSize(width:680,height:1100)
        panel.delegate = self
        for t in [NSWindow.ButtonType.closeButton,.miniaturizeButton,.zoomButton] { panel.standardWindowButton(t)?.isHidden = true }
        if let screen = NSScreen.main { panel.setFrameOrigin(NSPoint(x:screen.visibleFrame.maxX-422,y:screen.visibleFrame.maxY-700)) }
        if !qa && !restore && !captureOnly && !hotKeyQA { panel.setFrameAutosaveName("RoadmapDashboardPreviewV1") }
        if CommandLine.arguments.contains("--quick-start-smoke") || CommandLine.arguments.contains("--first-launch-smoke") || CommandLine.arguments.contains("--roadmap-smoke") || CommandLine.arguments.contains("--roadmap-restore"),let widthText=argument("--qa-width"),let width=Double(widthText),width>=320,width<=680 { panel.setContentSize(NSSize(width:width,height:660)) }
        let controller = WKUserContentController()
        controller.add(self,name:"monitor")
        let configWeb = WKWebViewConfiguration()
        configWeb.userContentController = controller
        configWeb.websiteDataStore = .nonPersistent()
        let container=NSView(frame:panel.contentView!.bounds)
        web = WKWebView(frame:container.bounds,configuration:configWeb)
        web.autoresizingMask = [.width,.height]
        web.navigationDelegate = self
        web.setValue(false,forKey:"drawsBackground")
        panel.contentView = container
        container.addSubview(web)
        // Anchor to the actual top: WKWebView's coordinate orientation must not
        // place the drag strip at the bottom. Leave the header buttons exposed.
        let drag = DragStrip(frame:.zero)
        drag.identifier=NSUserInterfaceItemIdentifier("dashboard-title-drag")
        drag.translatesAutoresizingMaskIntoConstraints=false
        drag.onGrab={ [weak self] in self?.writeReport(["received":true],"title-drag-grab.json") }
        container.addSubview(drag,positioned:.above,relativeTo:web)
        let topDrag=DragStrip(frame:.zero)
        topDrag.identifier=NSUserInterfaceItemIdentifier("dashboard-top-drag")
        topDrag.translatesAutoresizingMaskIntoConstraints=false
        topDrag.onGrab=drag.onGrab
        container.addSubview(topDrag,positioned:.above,relativeTo:drag)
        NSLayoutConstraint.activate([
            drag.topAnchor.constraint(equalTo:container.topAnchor),
            drag.leadingAnchor.constraint(equalTo:container.leadingAnchor),
            drag.trailingAnchor.constraint(equalTo:container.trailingAnchor,constant:-180),
            drag.heightAnchor.constraint(equalToConstant:74),
            topDrag.topAnchor.constraint(equalTo:container.topAnchor),
            topDrag.leadingAnchor.constraint(equalTo:container.leadingAnchor),
            topDrag.trailingAnchor.constraint(equalTo:container.trailingAnchor),
            topDrag.heightAnchor.constraint(equalToConstant:20)
        ])
        let index = Bundle.main.resourceURL!.appendingPathComponent("ui/index.html")
        web.loadFileURL(index,allowingReadAccessTo:Bundle.main.resourceURL!)
        statusItem = NSStatusBar.system.statusItem(withLength:NSStatusItem.squareLength)
        statusItem.button?.image = NSImage(systemSymbolName:"rectangle.stack",accessibilityDescription:"Dashboard")
        let menu = NSMenu()
        menu.addItem(withTitle:language == "en" ? "Show / Hide Dashboard" : "显示 / 隐藏 Dashboard",action:#selector(togglePanel),keyEquivalent:"")
        menu.addItem(withTitle:language == "en" ? "Quit Dashboard" : "退出 Dashboard",action:#selector(quit),keyEquivalent:"q")
        menu.items.forEach { $0.target = self }
        statusItem.menu = menu
        if liveMode && connection["globalShortcut"] as? Bool == true && (hotKeyQA || (!qa && !restore && !captureOnly)) { registerHotKey() }
        if !qa && !restore && !captureOnly && !hotKeyQA { panel.orderFrontRegardless() }
        if hotKeyQA {
            panel.setFrameOrigin(NSPoint(x:-10000,y:-10000))
            DispatchQueue.main.asyncAfter(deadline:.now()+0.3) { self.runHotKeyQA() }
        }
        timer = Timer.scheduledTimer(withTimeInterval:1,repeats:true) { [weak self] _ in self?.loadSnapshot() }
        if qa || restore || captureOnly {
            DispatchQueue.main.asyncAfter(deadline:.now()+30) {
                self.writeReport(["passed":false,"error":"Native verification timed out"],"dashboard-timeout.json")
                NSApp.terminate(nil)
            }
        }
    }
    static func shouldHide(visible:Bool,active:Bool,key:Bool)->Bool { visible && active && key }
    @objc func togglePanel() {
        if Self.shouldHide(visible:panel.isVisible,active:NSApp.isActive,key:panel.isKeyWindow) { panel.orderOut(nil) }
        else { NSApp.activate(ignoringOtherApps:true);panel.makeKeyAndOrderFront(nil) }
    }
    func updateMenuLanguage() {
        guard let menu=statusItem?.menu,menu.items.count>=2 else { return }
        menu.items[0].title=language == "en" ? "Show / Hide Dashboard" : "显示 / 隐藏 Dashboard"
        menu.items[1].title=language == "en" ? "Quit Dashboard" : "退出 Dashboard"
    }
    @objc func quit() { NSApp.terminate(nil) }
    func applicationShouldHandleReopen(_ sender:NSApplication,hasVisibleWindows flag:Bool)->Bool { panel.orderFrontRegardless();return false }
    func windowShouldClose(_ sender:NSWindow)->Bool { panel.orderOut(nil);return false }
    func windowDidMove(_ notification:Notification) {
        guard root != nil,panel != nil,!qa,!restore,!captureOnly,!hotKeyQA else { return }
        writeReport(["frame":NSStringFromRect(panel.frame),"event":"windowDidMove"],"window-position.json")
    }
    func applicationWillTerminate(_ notification:Notification) {
        timer?.invalidate()
        if let key=hotKey { UnregisterEventHotKey(key) }
        if let handler=hotKeyHandler { RemoveEventHandler(handler) }
        if watcher?.isRunning == true { watcher?.terminate() }
    }
    func registerHotKey() {
        var specs=[EventTypeSpec(eventClass:OSType(kEventClassKeyboard),eventKind:UInt32(kEventHotKeyPressed)),EventTypeSpec(eventClass:OSType(kEventClassKeyboard),eventKind:UInt32(kEventHotKeyReleased))]
        let callback:EventHandlerUPP = { _,event,data in
            guard let event=event,let data=data else { return OSStatus(eventNotHandledErr) }
            let owner=Unmanaged<MonitorDelegate>.fromOpaque(data).takeUnretainedValue()
            var id=EventHotKeyID()
            let result=GetEventParameter(event,EventParamName(kEventParamDirectObject),EventParamType(typeEventHotKeyID),nil,MemoryLayout<EventHotKeyID>.size,nil,&id)
            guard result == noErr,id.signature == owner.hotKeyID.signature,id.id == owner.hotKeyID.id else { return OSStatus(eventNotHandledErr) }
            if GetEventKind(event) == UInt32(kEventHotKeyReleased) { owner.hotKeyPressed=false }
            else if !owner.hotKeyPressed { owner.hotKeyPressed=true;owner.togglePanel() }
            return noErr
        }
        let installed=InstallEventHandler(GetApplicationEventTarget(),callback,2,&specs,Unmanaged.passUnretained(self).toOpaque(),&hotKeyHandler)
        let status=installed == noErr ? RegisterEventHotKey(UInt32(kVK_ANSI_D),UInt32(cmdKey),hotKeyID,GetApplicationEventTarget(),0,&hotKey) : installed
        writeReport(["registered":status == noErr,"status":status,"shortcut":"Command+D","requiresAccessibility":false],hotKeyQA ? "hotkey-qa-registration.json" : "hotkey-registration.json")
        if status != noErr {
            if let handler=hotKeyHandler { RemoveEventHandler(handler);hotKeyHandler=nil }
            statusItem.button?.toolTip="Dashboard · ⌘D 注册失败，使用菜单显示/隐藏"
            let note=NSMenuItem(title:"⌘D 不可用，请使用上方菜单（\(status)）",action:nil,keyEquivalent:"")
            statusItem.menu?.insertItem(note,at:1)
        } else { statusItem.button?.toolTip="Dashboard · ⌘D 显示 / 隐藏" }
    }
    func runHotKeyQA() {
        let previousApp=NSWorkspace.shared.frontmostApplication
        func dispatch(_ kind:UInt32,_ id:EventHotKeyID)->OSStatus {
            var event:EventRef?
            let created=CreateEvent(nil,OSType(kEventClassKeyboard),kind,GetCurrentEventTime(),EventAttributes(0),&event)
            guard created == noErr,let event=event else { return created }
            defer { ReleaseEvent(event) }
            var value=id
            let parameter=SetEventParameter(event,EventParamName(kEventParamDirectObject),EventParamType(typeEventHotKeyID),MemoryLayout<EventHotKeyID>.size,&value)
            return parameter == noErr ? SendEventToEventTarget(event,GetApplicationEventTarget()) : parameter
        }
        panel.orderOut(nil)
        let first=dispatch(UInt32(kEventHotKeyPressed),hotKeyID)
        DispatchQueue.main.asyncAfter(deadline:.now()+0.3) {
            let shown=self.panel.isVisible
            _=dispatch(UInt32(kEventHotKeyPressed),self.hotKeyID)
            let repeatIgnored=self.panel.isVisible
            _=dispatch(UInt32(kEventHotKeyReleased),self.hotKeyID)
            let second=dispatch(UInt32(kEventHotKeyPressed),self.hotKeyID)
            let hidden = !self.panel.isVisible
            _=dispatch(UInt32(kEventHotKeyReleased),self.hotKeyID)
            // A second normal-level window covers the panel; Cmd+D must raise it.
            let cover=NSWindow(contentRect:NSRect(x:-10000,y:-10000,width:200,height:150),styleMask:[.titled],backing:.buffered,defer:false)
            cover.isReleasedWhenClosed=false
            self.panel.orderFrontRegardless();cover.makeKeyAndOrderFront(nil)
            _=dispatch(UInt32(kEventHotKeyPressed),self.hotKeyID)
            let broughtForward=self.panel.isVisible && self.panel.isKeyWindow
            _=dispatch(UInt32(kEventHotKeyReleased),self.hotKeyID)
            let wrong=dispatch(UInt32(kEventHotKeyPressed),EventHotKeyID(signature:0x54455354,id:99))
            self.writeReport(["registered":self.hotKey != nil,"firstDispatch":first,"secondDispatch":second,"shown":shown,"hidden":hidden,"repeatIgnored":repeatIgnored,"coveredPanelBroughtForward":broughtForward,"normalLevel":self.panel.level == .normal,"unrelatedEventIgnored":wrong == OSStatus(eventNotHandledErr),"hardwareKeyPressTested":false,"sentInputToOtherApplications":false],"hotkey-native-qa.json")
            cover.orderOut(nil)
            previousApp?.activate(options:[])
            NSApp.terminate(nil)
        }
    }
    func backend(_ command:String)->Process {
        let p=Process()
        p.executableURL=URL(fileURLWithPath:"/usr/bin/env")
        p.arguments=[python,root.appendingPathComponent("sync/dashboard.py").path,command,"--data",dataRoot.path]
        if liveMode {
            if let home=connection["codexHome"] as? String { p.arguments! += ["--codex-home",home] }
            if let ledger=connection["ledgerDirectory"] as? String { p.arguments! += ["--ledger-data",ledger] }
        }
        var env=ProcessInfo.processInfo.environment;env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONNOUSERSITE"]="1";env.removeValue(forKey:"PYTHONHOME");env.removeValue(forKey:"PYTHONPATH");p.environment=env
        p.currentDirectoryURL=root
        p.standardError=FileHandle.nullDevice
        return p
    }
    func startWatcher() {
        let p=backend("watch")
        p.standardOutput=FileHandle.nullDevice
        do { try p.run();watcher=p }
        catch { NSLog("Dashboard: local event reader could not start") }
    }
    func call(_ name:String,_ object:Any) {
        guard JSONSerialization.isValidJSONObject(object),let d=try? JSONSerialization.data(withJSONObject:object),let s=String(data:d,encoding:.utf8) else { return }
        web.evaluateJavaScript("window.\(name)(\(s));",completionHandler:nil)
    }
    func loadSnapshot() {
        guard ready else { return }
        do {
            let d:Data
            if !liveMode {
                var object=(try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("samples/demo.json")))) as! [String:Any]
                object["capturedAt"]=ISO8601DateFormatter().string(from:Date())
                object["threads"]=(object["threads"] as! [[String:Any]]).map { thread in var value=thread;value["completedAt"]=Date().timeIntervalSince1970-(thread["ageSeconds"] as? Double ?? 0);return value }
                if let ledgerData=try? Data(contentsOf:dataRoot.appendingPathComponent("ledger.json")) { object["ledger"]=try JSONSerialization.jsonObject(with:ledgerData) }
                d=try JSONSerialization.data(withJSONObject:object)
            } else { d=try Data(contentsOf:dataRoot.appendingPathComponent("feed.json")) }
            if d==snapshotHash { return }
            let object=try JSONSerialization.jsonObject(with:d)
            call("centralLoadSnapshot",object);snapshotHash=d
        } catch { web.evaluateJavaScript("window.centralError('暂未读到同步记录，保留上一份清单');",completionHandler:nil) }
    }
    func ledgerRequest(_ value:[String:Any]) {
        guard !requestBusy,let d=try? JSONSerialization.data(withJSONObject:value),d.count<1000000 else { return }
        requestBusy=true
        let p=backend("request"),input=Pipe(),output=Pipe()
        p.standardInput=input;p.standardOutput=output
        do { try p.run();input.fileHandleForWriting.write(d);try? input.fileHandleForWriting.close() }
        catch { requestBusy=false;call("centralLedgerResult",["ok":false,"error":"未能启动本机清单服务"]);return }
        DispatchQueue.global(qos:.userInitiated).async {
            let resultData=output.fileHandleForReading.readDataToEndOfFile()
            p.waitUntilExit()
            let result=(try? JSONSerialization.jsonObject(with:resultData)) as? [String:Any] ?? ["ok":false,"error":"本机清单未能保存，旧记录仍保留"]
            DispatchQueue.main.async {
                self.requestBusy=false
                self.call("centralLedgerResult",result)
            }
        }
    }
    func userContentController(_ controller:WKUserContentController,didReceive message:WKScriptMessage) {
        guard message.frameInfo.isMainFrame,message.frameInfo.request.url?.isFileURL == true,let body=message.body as? [String:Any],let action=body["action"] as? String else { return }
        switch action {
        case "ready":
            panel.contentView?.layoutSubtreeIfNeeded()
            if let content=panel.contentView {
                let hit=content.hitTest(NSPoint(x:100,y:content.bounds.height-40))
                writeReport(["windowFrame":NSStringFromRect(panel.frame),"contentBounds":NSStringFromRect(content.bounds),"titleHitIsNativeDrag":hit is DragStrip],"drag-layout.json")
            }
            let preferencesURL=dataRoot.appendingPathComponent("panel-preferences.json")
            var preferences=(try? Data(contentsOf:preferencesURL)).flatMap { try? JSONSerialization.jsonObject(with:$0) } as? [String:Any] ?? [:]
            if let explicit=argument("--language") { preferences["language"]=explicit }
            else if preferences["language"] == nil { preferences["language"]=language }
            language=preferences["language"] as? String == "en" ? "en" : "zh"
            updateMenuLanguage()
            call("centralLoadPreferences",preferences)
            ready=true;loadSnapshot()
            if !liveMode && !qa && !restore && !captureOnly && !hotKeyQA && !onboardingQA && connection.isEmpty { web.evaluateJavaScript("window.centralOpenSetup()",completionHandler:nil) }
            writeReport(["level":panel.level.rawValue,"normalWindow":panel.level == .normal,"commandD":"bring-front-if-covered;hide-if-already-active"],"window-mode.json")
            if CommandLine.arguments.contains("--quick-start-smoke") {
                DispatchQueue.main.asyncAfter(deadline:.now()+1) { self.runQuickStartQA() }
            }
            else if CommandLine.arguments.contains("--first-launch-smoke") {
                DispatchQueue.main.asyncAfter(deadline:.now()+1) {
                    self.web.evaluateJavaScript("({setupVisible:!document.getElementById('connection-panel').hidden,language:document.documentElement.lang,demo:document.getElementById('sync-time').textContent.includes('sample'),tasks:document.querySelectorAll('.task').length,startAvailable:!!document.querySelector('#start-tracking'),setupText:document.querySelector('#connection-content').textContent,overflow:document.documentElement.scrollWidth>innerWidth})") { result,error in
                        self.writeReport(["ui":result ?? NSNull(),"error":error?.localizedDescription ?? NSNull(),"bundledPython":self.python.hasPrefix(Bundle.main.resourceURL!.path)],"first-launch.json")
                        NSApp.terminate(nil)
                    }
                }
            }
            else if onboardingQA { DispatchQueue.main.asyncAfter(deadline:.now()+0.5) { self.runOnboardingQA() } }
            else if CommandLine.arguments.contains("--roadmap-smoke") || CommandLine.arguments.contains("--roadmap-restore") { DispatchQueue.main.asyncAfter(deadline:.now()+0.5) { self.runRoadmapQA() } }
            else if qa { DispatchQueue.main.asyncAfter(deadline:.now()+0.5) { self.runSmoke() } }
            else if restore { DispatchQueue.main.asyncAfter(deadline:.now()+0.5) { self.runRestore() } }
            else if captureOnly { DispatchQueue.main.asyncAfter(deadline:.now()+2) { self.capture(self.language == "en" ? "preview-en.png" : "preview-zh.png") { NSApp.terminate(nil) } } }
        case "connection":
            if let request=body["request"] as? [String:Any] { connectionRequest(request) }
        case "ledger":
            if let r=body["request"] as? [String:Any],let op=r["op"] as? String,["follow","check"].contains(op) { ledgerRequest(r) }
        case "preferences":
            guard let value=body["value"] as? [String:Any],let theme=value["theme"] as? String,["system","light","dark","warm","sage"].contains(theme),
                  let height=value["conversationHeight"] as? Double,height>=100,height<=1000,
                  let order=value["conversationOrder"] as? [String],order.count<=200,order.allSatisfy({ UUID(uuidString:$0) != nil }),
                  let completions=value["completionVersions"] as? [String:String],completions.count<=200,completions.allSatisfy({ UUID(uuidString:$0.key) != nil && $0.value.count<=100 }) else { return }
            language=value["language"] as? String == "en" ? "en" : "zh"
            updateMenuLanguage()
            let taskOrder=(value["taskOrder"] as? [String] ?? []).filter { !$0.isEmpty && $0.count<=160 }.prefix(500)
            let taskOpen=(value["expandedTasks"] as? [String:Bool] ?? [:]).filter { !$0.key.isEmpty && $0.key.count<=160 }
            let stepLimit=value["stepLimit"] as? Int ?? 5
            let clean:[String:Any]=["taskOrder":Array(taskOrder),"expandedTasks":taskOpen.count<=500 ? taskOpen : [:],"compactOverview":value["compactOverview"] as? Bool ?? false,"hideCompletedSteps":value["hideCompletedSteps"] as? Bool ?? true,"stepLimit":[0,3,5,8].contains(stepLimit) ? stepLimit : 5,"version":1,"theme":theme,"conversationHeight":height,"hideCompleted":value["hideCompleted"] as? Bool ?? false,"language":value["language"] as? String == "en" ? "en" : "zh","conversationOrder":order,"completionVersions":completions]
            do {
                let data=try JSONSerialization.data(withJSONObject:clean)
                let url=dataRoot.appendingPathComponent("panel-preferences.json")
                try data.write(to:url,options:.atomic)
                try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:url.path)
            } catch { web.evaluateJavaScript("window.centralError('外观设置未能保存，任务记录不受影响');",completionHandler:nil) }
        case "hide": panel.orderOut(nil)
        case "open":
            if !liveMode { call("centralError",language == "en" ? "Sample chats stay inside this preview." : "演示对话仅在此预览展示。");return }
            guard let id=body["id"] as? String,UUID(uuidString:id) != nil,let kind=body["kind"] as? String else { return }
            let prefix=kind=="codex" ? "codex://threads/" : kind=="chatgpt" ? "https://chatgpt.com/c/" : ""
            if !prefix.isEmpty,let url=URL(string:prefix+id) { NSWorkspace.shared.open(url) }
        default: break
        }
    }
    func webView(_ webView:WKWebView,decidePolicyFor navigationAction:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void) { decisionHandler(navigationAction.request.url?.isFileURL == true ? .allow : .cancel) }
    func applyConnection() {
        let old=connection
        connection=(try? Data(contentsOf:baseRoot.appendingPathComponent("connection.json"))).flatMap { try? JSONSerialization.jsonObject(with:$0) } as? [String:Any] ?? [:]
        let enabled=connection["enabled"] as? Bool == true
        if enabled == liveMode && NSDictionary(dictionary:old).isEqual(to:connection) { return }
        if watcher?.isRunning == true { watcher?.terminate() }
        watcher=nil;liveMode=enabled
        dataRoot=baseRoot.appendingPathComponent(enabled ? "live" : "demo",isDirectory:true)
        try? FileManager.default.createDirectory(at:dataRoot,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
        snapshotHash=nil
        if enabled { startWatcher() } else { prepareDemo() }
        loadSnapshot()
    }
    func connectionRequest(_ source:[String:Any]) {
        guard !setupBusy,let op=source["op"] as? String,["status","connect","start-tracking","disconnect","choose-home","choose-ledger","link-ledger","own-ledger","install-tracking","unread-begin","unread-finish"].contains(op) else { return }
        var request=source
        if op == "choose-home" || op == "choose-ledger" {
            let chooser=NSOpenPanel();chooser.canChooseDirectories=op == "choose-home";chooser.canChooseFiles=op == "choose-ledger";chooser.allowsMultipleSelection=false
            chooser.message=language == "en" ? (op == "choose-home" ? "Choose the ChatGPT Desktop local-work data folder" : "Choose an existing ledger.json to share") : (op == "choose-home" ? "选择 ChatGPT Desktop 本地工作记录文件夹" : "选择要共同维护的 ledger.json")
            guard chooser.runModal() == .OK,let selected=chooser.url else { call("centralConnectionResult",["ok":false,"error":"cancelled"]);return }
            request=op == "choose-home" ? ["op":"connect","codexHome":selected.path] : ["op":"link-ledger","path":selected.path]
        }
        guard let inputData=try? JSONSerialization.data(withJSONObject:request) else { return }
        setupBusy=true
        let process=Process(),input=Pipe(),output=Pipe()
        process.executableURL=URL(fileURLWithPath:"/usr/bin/env")
        process.arguments=[python,root.appendingPathComponent("sync/setup.py").path,"--base",baseRoot.path]
        var env=ProcessInfo.processInfo.environment;env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONNOUSERSITE"]="1";env.removeValue(forKey:"PYTHONHOME");env.removeValue(forKey:"PYTHONPATH");process.environment=env
        process.standardInput=input;process.standardOutput=output;process.standardError=FileHandle.nullDevice
        do { try process.run();input.fileHandleForWriting.write(inputData);try? input.fileHandleForWriting.close() }
        catch { setupBusy=false;call("centralConnectionResult",["ok":false,"error":"python-unavailable"]);return }
        DispatchQueue.global(qos:.userInitiated).async {
            let data=output.fileHandleForReading.readDataToEndOfFile();process.waitUntilExit()
            let result=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] ?? ["ok":false,"error":"setup-failed"]
            DispatchQueue.main.async {
                self.setupBusy=false
                if result["ok"] as? Bool == true && !self.qa && !self.restore && !self.captureOnly { self.applyConnection() }
                self.call("centralConnectionResult",result)
            }
        }
    }
    func prepareDemo() {
        guard let data=try? Data(contentsOf:root.appendingPathComponent("samples/demo.json")),let object=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any],let value=object["ledger"],let ledger=try? JSONSerialization.data(withJSONObject:value) else { return }
        let target=dataRoot.appendingPathComponent("ledger.json")
        if !FileManager.default.fileExists(atPath:target.path) {
            try? ledger.write(to:target,options:.atomic)
            try? FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:target.path)
        }
    }
    var reportRoot:URL {
        let path=dataRoot.appendingPathComponent("reports",isDirectory:true)
        try? FileManager.default.createDirectory(at:path,withIntermediateDirectories:true)
        return path
    }
    func writeReport(_ value:Any,_ name:String) {
        if let data=try? JSONSerialization.data(withJSONObject:value,options:[.prettyPrinted,.sortedKeys]) { try? data.write(to:reportRoot.appendingPathComponent(name),options:.atomic) }
    }
    func capture(_ name:String,completion:@escaping()->Void) {
        web.takeSnapshot(with:nil) { image,error in
            if let image=image,let tiff=image.tiffRepresentation,let bitmap=NSBitmapImageRep(data:tiff),let png=bitmap.representation(using:.png,properties:[:]) { try? png.write(to:self.reportRoot.appendingPathComponent(name),options:.atomic) }
            completion()
        }
    }
    func runRoadmapQA() {
        timer?.invalidate()
        let restore=CommandLine.arguments.contains("--roadmap-restore")
        let script="""
        (()=>{const check=(v,m)=>{if(!v)throw Error(m)};
        const f=structuredClone(DASHBOARD_DEMO);f.capturedAt=new Date().toISOString();f.ledger.revision=100;
        f.ledger.tasks=[{id:'long',title:'Sixteen-step task',project:'Example',defaultExpanded:true,steps:Array.from({length:16},(_,i)=>({id:'s'+i,text:'Step '+i,done:i<4,reported:i===4?'in_progress':'pending'}))},{id:'second',title:'Second task',project:'Example',steps:[{id:'one',text:'One',done:false}]},{id:'third',title:'Third task',project:'Example',steps:[{id:'one',text:'One',done:false}]}];
        window.centralLoadSnapshot(f);
        const long=()=>document.querySelector('[data-id=long]');
        if(\(restore ? "true":"false")){
          check(document.querySelector('.task').dataset.id==='second','order restored');
          check(document.querySelectorAll('.task.compact').length===3,'compact restored');check(!long().querySelector('.roadmap').hidden,'expanded task restored');
          document.querySelector('#list-options').click();check(document.querySelector('#step-limit').value==='3','limit restored');document.querySelector('#list-options').click();
          return {restored:true,order:true,compact:true,limit:true};
        }
        window.centralLoadPreferences({language:'en',theme:'warm',conversationHeight:200,hideCompleted:false,taskOrder:[],compactOverview:false,hideCompletedSteps:true,stepLimit:5,expandedTasks:{}});
        check(long().querySelectorAll('.step').length===5,'initial cap');check(!long().querySelector('.step.done'),'completed hidden');
        long().querySelector('.more-steps').click();check(long().querySelectorAll('.step').length===12,'show remaining');long().querySelector('.more-steps').click();
        long().querySelector('.step-visibility').click();check(long().querySelector('.step.done'),'completed can be shown');long().querySelector('.step-visibility').click();
        document.querySelector('#list-options').click();const choices=document.querySelectorAll('.display-choice input');choices[0].click();check(long().querySelector('.roadmap').hidden,'overview collapsed');document.querySelector('#task-sort').click();check(document.querySelector('#task-sort').getAttribute('aria-pressed')==='true','sort entry visible');
        document.querySelector('[data-id=second] .move-task').click();check(document.querySelector('.task').dataset.id==='second','manual move');
        const dt=new DataTransfer();document.querySelector('[data-id=third] .drag-handle').dispatchEvent(new DragEvent('dragstart',{bubbles:true,dataTransfer:dt}));const drop=document.querySelector('[data-id=second]');drop.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt,clientY:drop.getBoundingClientRect().top+1}));check(document.querySelector('.task').dataset.id==='third','drag order');document.querySelector('[data-id=third] .drag-handle').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true}));check(document.querySelector('.task').dataset.id==='second','keyboard order');
        const select=document.querySelector('#step-limit');select.value='3';select.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('#list-options').click();
        long().querySelector('.task-toggle').click();check(long().querySelectorAll('.step').length===3,'new cap');
        const before=f.ledger.tasks.map(t=>t.steps.map(s=>s.done));f.ledger.revision++;window.centralLoadSnapshot(f);check(document.querySelector('.task').dataset.id==='second','refresh preserves order');check(JSON.stringify(before)===JSON.stringify(f.ledger.tasks.map(t=>t.steps.map(s=>s.done))),'record unchanged');
        document.querySelector('#language').click();document.querySelector('#list-options').click();check(document.querySelector('#list-display-panel').textContent.includes('紧凑概览'),'Chinese view settings');document.querySelector('#list-options').click();
        return {cap:true,showAll:true,hideCompleted:true,overview:true,manualMove:true,dragEvents:true,keyboardMove:true,stableRefresh:true,recordUnchanged:true,bilingual:true,overflow:document.documentElement.scrollWidth>innerWidth};})();
        """
        web.evaluateJavaScript(script) { value,error in
            self.writeReport(["checks":value ?? NSNull(),"error":error?.localizedDescription ?? NSNull(),"detail":(error as NSError?)?.userInfo["WKJavaScriptExceptionMessage"] ?? NSNull()],restore ? "roadmap-restore.json":"roadmap-controls.json")
            self.capture("roadmap-controls.png") { NSApp.terminate(nil) }
        }
    }
    func runQuickStartQA() {
        web.evaluateJavaScript("""
        (()=>{const b=document.querySelector('#start-tracking');if(!b||b.disabled)throw Error('Start tracking action missing');
        const choice=document.querySelector('.tracking-choice input');if(!choice?.checked)throw Error('Roadmap choice missing');
        document.querySelector('#language').click();if(!b)throw Error('language');document.querySelector('#language').click();
        document.querySelector('#start-tracking').click();return {action:true,explicitRoadmapChoice:true};})();
        """) { value,error in
            if let error=error { self.writeReport(["error":error.localizedDescription],"quick-start.json");NSApp.terminate(nil);return }
            DispatchQueue.main.asyncAfter(deadline:.now()+3) {
                self.web.evaluateJavaScript("""
                (()=>{const c=document.querySelector('#connection-content').textContent;
                if(!c.includes('Local conversations connected'))throw Error('Not connected');
                if(!c.includes('Roadmap skill installed'))throw Error('Skill not installed');
                if(document.querySelector('#tasks').textContent.includes('keyboard & search'))throw Error('Sample tasks leaked');
                const live=document.querySelector('#sync-time').textContent;if(live.includes('sample'))throw Error('Demo feed remains');
                document.querySelector('#language').click();if(!document.querySelector('#connection-content').textContent.includes('真实对话已接入'))throw Error('Chinese status');
                if(!document.querySelector('#connection-panel').hidden)throw Error('Setup did not dismiss after success');return {width:innerWidth,setupDismissed:true,oneClickConnected:true,skillInstalled:true,noDemoTasks:true,liveFeed:true,bilingual:true,overflow:document.documentElement.scrollWidth>innerWidth};})();
                """) { result,error in
                    self.writeReport(["ui":result ?? NSNull(),"error":error?.localizedDescription ?? NSNull()],"quick-start.json")
                    self.capture("quick-start.png") { NSApp.terminate(nil) }
                }
            }
        }
    }
    func runOnboardingQA() {
        guard let home=argument("--source-fixture"),let shared=argument("--shared-fixture") else { NSApp.terminate(nil);return }
        connectionRequest(["op":"connect","codexHome":home])
        DispatchQueue.main.asyncAfter(deadline:.now()+1.5) {
            self.connectionRequest(["op":"link-ledger","path":shared])
            DispatchQueue.main.asyncAfter(deadline:.now()+3) {
                self.web.evaluateJavaScript("window.centralOpenSetup();") { _,_ in
                    DispatchQueue.main.asyncAfter(deadline:.now()+0.5) {
                        let script="""
                        (()=>{const check=(v,m)=>{if(!v)throw Error(m)};
                        check(document.querySelector('#connection-content').textContent.includes('Local conversations connected'),'setup connected');
                        check(document.querySelector('#tasks').textContent.includes('Shared fixture roadmap'),'shared roadmap rendered');
                        check(!document.querySelector('#tasks').textContent.includes('keyboard & search'),'demo leaked into live');
                        document.querySelector('#language').click();check(document.querySelector('#connection-content').textContent.includes('真实对话已接入'),'Chinese setup');
                        document.querySelector('#language').click();document.querySelector('.setup-close').click();
                        return {connected:true,sharedRoadmap:true,noDemoLeak:true,bilingualSetup:true};})();
                        """
                        self.web.evaluateJavaScript(script) { value,error in
                            let detail:Any=(error as NSError?)?.userInfo["WKJavaScriptExceptionMessage"] ?? NSNull()
                            let result:[String:Any]=["checks":value ?? NSNull(),"error":error?.localizedDescription ?? NSNull(),"detail":detail]
                            self.writeReport(result,"onboarding-checks.json")
                            NSApp.terminate(nil)
                        }
                    }
                }
            }
        }
    }
    func runSmoke() {
        let script="""
        (()=>{
          const check=(v,m)=>{if(!v)throw Error(m)};
          check(document.documentElement.lang==='en','initial English');
          check(document.querySelector('.list-heading h2').textContent==='My roadmap','English heading');
          check(document.querySelector('.conversation-title').textContent==='Notes app · keyboard navigation','English demo content');
          check(document.querySelector('#sync-time').textContent.includes('sample'),'demo disclosure');
          check(document.querySelector('#running').children.length===3,'three visible chats');
          check(!document.querySelector('#history-unread').open,'history folded');
          document.querySelector('#language').click();
          check(document.documentElement.lang==='zh-CN','Chinese preserved');
          check(document.querySelector('.list-heading h2').textContent==='我的清单','Chinese heading');
          check(document.querySelector('.conversation-title').textContent==='笔记应用 · 键盘导航','Chinese demo');
          document.querySelector('#language').click();
          check(document.querySelector('.list-heading h2').textContent==='My roadmap','switch back');
          document.querySelector('#theme').click();document.querySelector('[data-theme=warm]').click();
          check(document.documentElement.dataset.theme==='warm','theme');
          document.querySelector('#theme').click();document.querySelector('[data-theme=system]').click();
          const height=document.querySelector('#conversations').getBoundingClientRect().height;
          document.querySelector('#splitter').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true}));
          check(document.querySelector('#conversations').getBoundingClientRect().height>height,'splitter');
          document.querySelector('#splitter').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowUp',bubbles:true}));
          const toggle=document.querySelectorAll('.task-toggle')[1];toggle.click();check(document.querySelectorAll('.task-toggle')[1].getAttribute('aria-expanded')==='true','expand roadmap');
          check([...document.querySelectorAll('.badge')].some(x=>x.textContent==='Reported · awaiting review'),'review boundary');toggle.click();
          document.querySelectorAll('.step input')[1].click();
          return {english:true,chinese:true,demo:true,roadmap:true,reviewBoundary:true,splitter:true,theme:true,historyFolded:true};
        })();
        """
        web.evaluateJavaScript(script) { value,error in
            let detail:Any=(error as NSError?)?.userInfo["WKJavaScriptExceptionMessage"] ?? NSNull()
            let checkValue:Any=value ?? NSNull()
            let errorValue:Any=error?.localizedDescription ?? NSNull()
            self.writeReport(["checks":checkValue,"error":errorValue,"detail":detail],"preview-checks.json")
            DispatchQueue.main.asyncAfter(deadline:.now()+0.7) {
                self.web.evaluateJavaScript("document.querySelectorAll('.step input')[1].checked") { saved,_ in
                    self.writeReport(["checked":saved ?? false],"preview-checkbox.json")
                    self.capture("preview-en.png") {
                        self.web.evaluateJavaScript("document.querySelector('#language').click()") { _,_ in
                            self.capture("preview-zh.png") {
                                self.web.evaluateJavaScript("document.querySelector('#language').click()") { _,_ in
                                    self.panel.setContentSize(NSSize(width:320,height:660))
                                    DispatchQueue.main.asyncAfter(deadline:.now()+0.3) {
                                        self.web.evaluateJavaScript("({overflow:document.documentElement.scrollWidth>innerWidth,width:innerWidth,language:document.documentElement.lang})") { narrow,_ in
                                            self.writeReport(narrow ?? [:],"preview-narrow.json")
                                            self.capture("preview-narrow.png") { NSApp.terminate(nil) }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    func runRestore() {
        web.evaluateJavaScript("({language:document.documentElement.lang,checked:document.querySelectorAll('.step input')[1].checked})") { value,error in
            self.writeReport(["restored":value ?? NSNull(),"error":error?.localizedDescription ?? NSNull()],"preview-restore.json")
            NSApp.terminate(nil)
        }
    }
}
let application=NSApplication.shared
let delegate=MonitorDelegate()
application.delegate=delegate
application.run()
