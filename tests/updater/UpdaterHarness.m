#import <Cocoa/Cocoa.h>
#import <Sparkle/Sparkle.h>
static NSString *reportPath;
static void record(NSString *name,id value) {
    NSMutableDictionary *d=[[NSDictionary dictionaryWithContentsOfFile:reportPath] mutableCopy] ?: [NSMutableDictionary dictionary];
    d[name]=value;[d writeToFile:reportPath atomically:YES];
}
@interface TestDriver:SPUStandardUserDriver @end
@implementation TestDriver
- (void)showUpdateFoundWithAppcastItem:(SUAppcastItem *)item state:(SPUUserUpdateState *)state reply:(void (^)(SPUUserUpdateChoice))reply {
    record(@"found",item.versionString);reply(SPUUserUpdateChoiceInstall);
}
- (void)showReadyToInstallAndRelaunch:(void (^)(SPUUserUpdateChoice))reply { record(@"ready",@YES);dispatch_after(dispatch_time(DISPATCH_TIME_NOW,200*NSEC_PER_MSEC),dispatch_get_main_queue(),^{ reply(SPUUserUpdateChoiceInstall); }); }
- (void)showUpdaterError:(NSError *)error acknowledgement:(void (^)(void))ack {
    record(@"error",@{@"code":@(error.code),@"description":error.localizedDescription});ack();[NSApp terminate:nil];
}
- (void)showUpdateNotFoundWithError:(NSError *)error acknowledgement:(void (^)(void))ack { record(@"notFound",@(error.code));ack();[NSApp terminate:nil]; }
- (void)showUpdateInstalledAndRelaunched:(BOOL)relaunched acknowledgement:(void (^)(void))ack { record(@"installed",@YES);ack();[NSApp terminate:nil]; }
@end
@interface Harness:NSObject<NSApplicationDelegate,SPUUpdaterDelegate>
@property SPUUpdater *updater;
@property TestDriver *driver;
@end
@implementation Harness
- (void)applicationDidFinishLaunching:(NSNotification *)note {
    NSArray *args=NSProcessInfo.processInfo.arguments;reportPath=args[2];
    NSBundle *host=[NSBundle bundleWithPath:args[1]];
    self.driver=[[TestDriver alloc] initWithHostBundle:host delegate:nil];
    self.updater=[[SPUUpdater alloc] initWithHostBundle:host applicationBundle:NSBundle.mainBundle userDriver:self.driver delegate:self];
    NSError *error=nil;
    if (![self.updater startUpdater:&error]) {record(@"startError",error.localizedDescription);[NSApp terminate:nil];return;}
    if ([args containsObject:@"--automatic"]) {
        self.updater.automaticallyChecksForUpdates=YES;
        self.updater.automaticallyDownloadsUpdates=YES;
        [self.updater checkForUpdatesInBackground];
    } else { [self.updater checkForUpdates]; }
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,60*NSEC_PER_SEC),dispatch_get_main_queue(),^{ record(@"timeout",@YES);[NSApp terminate:nil]; });
}
- (BOOL)updater:(SPUUpdater *)updater willInstallUpdateOnQuit:(SUAppcastItem *)item immediateInstallationBlock:(void (^)(void))handler {
    record(@"automaticallyDownloaded",@YES);
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,300*NSEC_PER_MSEC),dispatch_get_main_queue(),^{handler();});return YES;
}
- (BOOL)updaterShouldRelaunchApplication:(SPUUpdater *)updater {return YES;}
- (void)updater:(SPUUpdater *)updater didAbortWithError:(NSError *)error {record(@"abort",@{@"code":@(error.code),@"description":error.localizedDescription});}
@end
int main(int argc,const char **argv) {
    @autoreleasepool { NSApplication *app=NSApplication.sharedApplication;[app setActivationPolicy:NSApplicationActivationPolicyAccessory];Harness *h=[Harness new];app.delegate=h;[app run]; }
    return 0;
}
