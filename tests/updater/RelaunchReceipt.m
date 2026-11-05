#import <Cocoa/Cocoa.h>
@interface Receipt:NSObject<NSApplicationDelegate> @end
@implementation Receipt
- (void)applicationDidFinishLaunching:(NSNotification *)note {
    NSURL *url=[[NSBundle.mainBundle.bundleURL URLByDeletingLastPathComponent] URLByAppendingPathComponent:@"relaunch-receipt.plist"];
    [@{@"relaunched":@YES,@"build":[NSBundle.mainBundle objectForInfoDictionaryKey:@"CFBundleVersion"]} writeToURL:url atomically:YES];
    [NSApp terminate:nil];
}
@end
int main(void) { @autoreleasepool {NSApplication *app=NSApplication.sharedApplication;[app setActivationPolicy:NSApplicationActivationPolicyAccessory];Receipt *delegate=[Receipt new];app.delegate=delegate;[app run];}return 0; }
