import AppKit
#if canImport(Sparkle)
import Sparkle

/// Sparkle owns downloads, signature verification and replacement. No custom installer.
final class DashboardUpdater:NSObject, SPUUpdaterDelegate {
    private var controller:SPUStandardUpdaterController!
    private weak var panel:NSWindow?
    private var language="en"
    private var consentPending=false
    var changed:(()->Void)?
    var canCheck:Bool { controller?.updater.canCheckForUpdates ?? false }
    var automaticallyChecks:Bool { controller?.updater.automaticallyChecksForUpdates ?? false }
    var automaticallyDownloads:Bool { controller?.updater.automaticallyDownloadsUpdates ?? false }
    func start(panel:NSWindow,language:String) {
        self.panel=panel;self.language=language
        controller=SPUStandardUpdaterController(startingUpdater:false,updaterDelegate:self,userDriverDelegate:nil)
        controller.startUpdater()
        if !UserDefaults.standard.bool(forKey:"DashboardUpdateConsentRecorded") {
            consentPending=true
            presentSettings(first:true)
        }
    }
    func setLanguage(_ value:String) { language=value }
    func check() { guard canCheck else { return };controller.checkForUpdates(nil) }
    func settings() { presentSettings(first:false) }
    private func presentSettings(first:Bool) {
        guard let panel=panel else { return }
        if panel.attachedSheet != nil {
            DispatchQueue.main.asyncAfter(deadline:.now()+0.5) { [weak self] in
                guard let self=self else { return }
                if !first || self.consentPending { self.presentSettings(first:first) }
            };return
        }
        let en=language == "en",alert=NSAlert()
        alert.messageText=en ? (first ? "Keep Dashboard up to date?" : "Update settings") : (first ? "让 Dashboard 保持更新？" : "更新设置")
        alert.informativeText=en ? "Checks use this project's public GitHub feed, at most daily by default. Optional automatic downloads install when Dashboard quits; they never force a restart. No account, model calls or system profiling. You can change this choice in the menu bar." : "允许后默认每天检查本项目的 GitHub 更新清单。可选的自动下载会在退出 Dashboard 时安装，不会强制重启。无需账号，不调用模型、不发送系统概况；可随时从菜单栏修改。"
        let view=NSView(frame:NSRect(x:0,y:0,width:330,height:64))
        let checks=NSButton(checkboxWithTitle:en ? "Check for updates automatically" : "自动检查更新",target:nil,action:nil)
        checks.frame=NSRect(x:0,y:34,width:330,height:24);checks.state=first ? .on : (automaticallyChecks ? .on : .off)
        let downloads=NSButton(checkboxWithTitle:en ? "Download and install on quit" : "自动下载，并在退出时安装",target:nil,action:nil)
        downloads.frame=NSRect(x:0,y:4,width:330,height:24);downloads.state=automaticallyDownloads ? .on : .off
        view.addSubview(checks);view.addSubview(downloads);alert.accessoryView=view
        alert.addButton(withTitle:en ? "Save" : "保存")
        alert.addButton(withTitle:en ? (first ? "Not Now" : "Cancel") : (first ? "暂不开启" : "取消"))
        alert.beginSheetModal(for:panel) { [weak self] response in
            guard let self=self else { return }
            if response == .alertFirstButtonReturn {
                self.controller.updater.automaticallyChecksForUpdates=checks.state == .on
                self.controller.updater.automaticallyDownloadsUpdates=checks.state == .on && downloads.state == .on
                UserDefaults.standard.set(true,forKey:"DashboardUpdateConsentRecorded")
            } else if first {
                self.controller.updater.automaticallyChecksForUpdates=false
                self.controller.updater.automaticallyDownloadsUpdates=false
                UserDefaults.standard.set(true,forKey:"DashboardUpdateConsentRecorded")
            }
            self.consentPending=false;self.changed?()
        }
    }
    func updater(_ updater:SPUUpdater,willInstallUpdateOnQuit item:SUAppcastItem,immediateInstallationBlock installHandler:@escaping ()->Void)->Bool {
        // The user explicitly opted into install-on-quit. Offer an earlier restart,
        // while retaining Sparkle's documented install-on-quit behavior.
        let alert=NSAlert(),en=language == "en"
        alert.messageText=en ? "Dashboard update is ready" : "Dashboard 新版已准备好"
        alert.informativeText=en ? "Install and reopen now, or keep working and install when you next quit Dashboard." : "现在安装并重新打开，或继续工作，等下次退出 Dashboard 时安装。"
        alert.addButton(withTitle:en ? "Install and Reopen" : "安装并重新打开")
        alert.addButton(withTitle:en ? "On Next Quit" : "下次退出时安装")
        func present() {
            guard let panel=self.panel else { return }
            if panel.attachedSheet != nil { DispatchQueue.main.asyncAfter(deadline:.now()+0.5) { present() };return }
            alert.beginSheetModal(for:panel) { response in if response == .alertFirstButtonReturn { installHandler() } }
        }
        present();return true
    }
}
#else
/// Source builds without Sparkle retain a manual release-page fallback.
final class DashboardUpdater {
    var changed:(()->Void)?
    var canCheck:Bool { true }
    var automaticallyChecks:Bool { false }
    var automaticallyDownloads:Bool { false }
    func start(panel:NSWindow,language:String) {}
    func setLanguage(_ value:String) {}
    func check() { NSWorkspace.shared.open(URL(string:"https://github.com/TeabagCollector/roadmap-dashboard/releases")!) }
    func settings() { check() }
}
#endif
