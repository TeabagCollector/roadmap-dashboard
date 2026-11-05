#!/usr/bin/env python3
"""Build an Apple silicon preview with a pinned, relocatable Python runtime."""
import argparse,hashlib,json,os,plistlib,shutil,subprocess,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNTIME_SHA256='353d5f1b4fd2715e7053f12f068435d5bbad16b91e057006b5d01e0925709a7e'
RUNTIME_URL='https://github.com/astral-sh/python-build-standalone/releases/download/20261026/cpython-3.12.16%2B20261026-aarch64-apple-darwin-install_only_stripped.tar.gz'
VERSION='0.5.0-preview.6'
APP='Dashboard for Codex.app'

def package(archive,output,notices,sparkle):
    archive=archive.resolve();output=output.resolve()
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=RUNTIME_SHA256:raise ValueError('Runtime checksum mismatch')
    if output.exists():raise ValueError('Output already exists; choose a new candidate directory')
    subprocess.run(['bash',str(ROOT/'build.sh')],check=True)
    output.mkdir(parents=True)
    app=output/APP;shutil.copytree(ROOT/'build/Roadmap Dashboard Preview.app',app,symlinks=True)
    resources=app/'Contents/Resources'
    metadata=json.loads((notices/'PYTHON.json').read_text())
    if metadata['python_version']!='3.12.16':raise ValueError('License bundle version mismatch')
    shutil.copytree(notices/'licenses',resources/'third-party-licenses')
    with tempfile.TemporaryDirectory(prefix='dashboard-runtime-') as directory:
        directory=Path(directory).resolve()
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                dest=(directory/member.name).resolve()
                if directory not in dest.parents:raise ValueError('Unsafe archive member')
                if member.isdev() or member.isfifo():raise ValueError('Unexpected archive entry')
                if member.issym() or member.islnk():
                    target=(dest.parent/member.linkname).resolve() if member.issym() else (directory/member.linkname).resolve()
                    if directory not in target.parents:raise ValueError('Unsafe runtime link')
            tar.extractall(directory)
        shutil.copytree(directory/'python',resources/'python',symlinks=True)
    # No dependency installer is needed in the shipped application.
    site=resources/'python/lib/python3.12/site-packages'
    for item in site.glob('pip*'):
        if item.is_dir():shutil.rmtree(item)
    for item in (resources/'python/bin').glob('pip*'):item.unlink()
    for cache in app.rglob('__pycache__'):shutil.rmtree(cache)
    for lib in (resources/'python/lib').glob('*.a'):lib.unlink()
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    info.update(CFBundleName='Dashboard for Codex',CFBundleDisplayName='Dashboard for Codex',CFBundleIdentifier='io.github.teabagcollector.dashboard-for-codex.preview',CFBundleShortVersionString=VERSION,CFBundleVersion='10',LSMinimumSystemVersion='15.0',LSArchitecturePriority=['arm64'])
    sparkle=sparkle.resolve()
    framework=sparkle/'Sparkle.framework'
    if not framework.is_dir():raise ValueError('Official Sparkle.framework directory is required')
    if plistlib.loads((framework/'Resources/Info.plist').read_bytes())['CFBundleShortVersionString']!='2.10.1':raise ValueError('Sparkle 2.10.1 is required; use fetch_sparkle.py')
    frameworks=app/'Contents/Frameworks';frameworks.mkdir(exist_ok=True)
    shutil.copytree(framework,frameworks/'Sparkle.framework',symlinks=True)
    info.update(SUFeedURL='https://raw.githubusercontent.com/TeabagCollector/roadmap-dashboard/main/updates/appcast.xml',SUPublicEDKey=(ROOT/'updates/public-key.txt').read_text().strip(),SUEnableAutomaticChecks=False,SUAutomaticallyUpdate=False,SUAllowsAutomaticUpdates=True,SUEnableSystemProfiling=False,SUVerifyUpdateBeforeExtraction=True,SUScheduledCheckInterval=86400)
    (app/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    subprocess.run(['swiftc','-target','arm64-apple-macos15.0','-module-cache-path',str(ROOT/'build/module-cache'),'-framework','AppKit','-framework','WebKit','-framework','Carbon','-F',str(sparkle),'-framework','Sparkle','-Xlinker','-rpath','-Xlinker','@executable_path/../Frameworks',str(ROOT/'src/Monitor.swift'),str(ROOT/'src/Updater.swift'),'-o',str(app/'Contents/MacOS/roadmap-dashboard')],check=True)
    shutil.copyfile(ROOT/'LICENSE',resources/'LICENSE')
    shutil.copyfile(sparkle/'LICENSE',resources/'Sparkle-LICENSE.txt')
    (resources/'THIRD-PARTY-NOTICES.txt').write_text('Bundled CPython 3.12.16 from Astral python-build-standalone, release 20261026.\nSource: '+RUNTIME_URL+'\nArchive SHA256: '+RUNTIME_SHA256+'\nCPython and bundled third-party license notices are retained under python/lib/python3.12/LICENSE.txt and third-party-licenses/.\nNo end-user dependency download or Python installation is required.\n')
    with (resources/'THIRD-PARTY-NOTICES.txt').open('a') as notices_file:notices_file.write('\nSparkle 2.10.1 (MIT), https://github.com/sparkle-project/Sparkle/releases/tag/2.10.1. Archive SHA256: 1a856d2a9edb8e628de88121d7be04cf0e2167f8641650b78fca00b14244cf27. License retained in Sparkle-LICENSE.txt.\n')
    # Re-sign changed Mach-O files before sealing the outer bundle.
    subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True,capture_output=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
    return app

def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime-archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime-notices',type=Path,required=True);p.add_argument('--sparkle-directory',type=Path,required=True);a=p.parse_args();print(package(a.runtime_archive,a.output,a.runtime_notices,a.sparkle_directory))
if __name__=='__main__':main()
