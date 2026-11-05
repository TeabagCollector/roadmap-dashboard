import AppKit
import Sparkle
@main struct SettingsTest {
    static func main() {
        let app=NSApplication.shared;app.setActivationPolicy(.accessory)
        let delegate=SettingsDelegate();app.delegate=delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}
final class SettingsDelegate:NSObject,NSApplicationDelegate {
    var panel:NSWindow!,feature:DashboardUpdater!
    var result:[String:Any]=[:]
    func buttons(_ view:NSView)->[NSButton] { (view as? NSButton).map { [$0] } ?? view.subviews.flatMap { buttons($0) } }
    func choices()->[NSButton] { panel.attachedSheet?.contentView.map { buttons($0) } ?? [] }
    func press(_ title:String) { guard let b=choices().first(where:{$0.title==title}) else { fail("Missing button: "+title);return };b.performClick(nil) }
    func fail(_ message:String) { result["error"]=message;finish() }
    func finish() { try? JSONSerialization.data(withJSONObject:result,options:.prettyPrinted).write(to:URL(fileURLWithPath:CommandLine.arguments[1]));NSApp.terminate(nil) }
    func applicationDidFinishLaunching(_ n:Notification) {
        panel=NSWindow(contentRect:NSRect(x:100,y:100,width:400,height:660),styleMask:[.titled],backing:.buffered,defer:false);panel.title="Isolated update settings QA";panel.makeKeyAndOrderFront(nil)
        feature=DashboardUpdater();feature.start(panel:panel,language:CommandLine.arguments.contains("--zh") ? "zh" : "en")
        DispatchQueue.main.asyncAfter(deadline:.now()+0.5) {
            if CommandLine.arguments.contains("--restore") {
                self.result["noRepeatedConsent"]=self.panel.attachedSheet == nil
                self.result["offAfterRestart"] = !self.feature.automaticallyChecks && !self.feature.automaticallyDownloads
                self.finish();return
            }
            let zh=CommandLine.arguments.contains("--zh")
            let checks=zh ? "自动检查更新" : "Check for updates automatically"
            let downloads=zh ? "自动下载，并在退出时安装" : "Download and install on quit"
            self.result["firstPrompt"]=self.panel.attachedSheet != nil
            self.result["downloadsDefaultOff"]=self.choices().first(where:{$0.title==downloads})?.state == .off
            self.press(zh ? "暂不开启" : "Not Now")
            DispatchQueue.main.asyncAfter(deadline:.now()+0.4) {
                self.result["declineDisables"]=(!self.feature.automaticallyChecks && !self.feature.automaticallyDownloads)
                self.feature.settings()
                DispatchQueue.main.asyncAfter(deadline:.now()+0.3) {
                    self.choices().first(where:{$0.title==checks})?.state = .on
                    self.choices().first(where:{$0.title==downloads})?.state = .on
                    self.press(zh ? "保存" : "Save")
                    DispatchQueue.main.asyncAfter(deadline:.now()+0.4) {
                        self.result["optInEnabled"]=self.feature.automaticallyChecks && self.feature.automaticallyDownloads
                        self.feature.settings()
                        DispatchQueue.main.asyncAfter(deadline:.now()+0.3) {
                            self.choices().first(where:{$0.title==checks})?.state = .off
                            // Keeping downloads checked must not leave downloads enabled after checks are disabled.
                            self.press(zh ? "保存" : "Save")
                            DispatchQueue.main.asyncAfter(deadline:.now()+0.3) {
                                self.result["disableStopsBoth"] = !self.feature.automaticallyChecks && !self.feature.automaticallyDownloads
                                self.result["consentRemembered"]=UserDefaults.standard.bool(forKey:"DashboardUpdateConsentRecorded")
                                self.result["profilingOff"] = !UserDefaults.standard.bool(forKey:"SUEnableSystemProfiling")
                                self.finish()
                            }
                        }
                    }
                }
            }
        }
    }
}
