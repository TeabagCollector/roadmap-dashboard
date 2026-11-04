#!/usr/bin/env python3
"""User-local installer with explicit destination, preflight and data-preserving removal."""
import argparse,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAME='Roadmap Dashboard Preview.app'

def install(apps,base,python=sys.executable,dry_run=False):
    if sys.version_info<(3,9):raise ValueError('Python 3.9 or later is required')
    runtime=subprocess.run([python,'-c','import sys; assert sys.version_info >= (3,9); print(sys.executable)'],capture_output=True,text=True,check=True).stdout.strip()
    source=ROOT/'build'/NAME
    if not source.exists():
        if not shutil.which('swiftc'):raise ValueError('Install Xcode command-line tools and Swift 6 first')
        if not dry_run:subprocess.run(['bash',str(ROOT/'build.sh')],check=True)
    destination=apps/NAME
    if dry_run:return {'dryRun':True,'destination':str(destination),'dataBase':str(base),'python':runtime,'buildNeeded':not source.exists()}
    apps.mkdir(parents=True,exist_ok=True);base.mkdir(parents=True,exist_ok=True);os.chmod(base,0o700)
    staging=Path(tempfile.mkdtemp(prefix='.roadmap-install-',dir=apps))
    try:
        shutil.copytree(source,staging/NAME)
        for cache in (staging/NAME).rglob('__pycache__'):shutil.rmtree(cache)
        backup=apps/(NAME+'.previous')
        if backup.exists():raise ValueError('Previous backup exists; inspect it before updating')
        if destination.exists():
            receipt=base/'installation.json'
            if not receipt.exists() or json.loads(receipt.read_text()).get('application')!=str(destination):raise ValueError('Unrecognized existing app; choose another destination')
            destination.rename(backup)
        try:(staging/NAME).rename(destination)
        except BaseException:
            if backup.exists() and not destination.exists():backup.rename(destination)
            raise
        config={'python':runtime,'application':str(destination),'base':str(base)}
        tmp=base/'installation.tmp';tmp.write_text(json.dumps(config));os.chmod(tmp,0o600);os.replace(tmp,base/'installation.json')
    finally:shutil.rmtree(staging)
    return {'installed':str(destination),'dataPreserved':True,'next':'Open the app and choose Connect local Codex in setup.'}

def uninstall(apps,base):
    manifest=base/'installation.json'
    if not manifest.exists():raise ValueError('No installation receipt; no files removed')
    value=json.loads(manifest.read_text());target=Path(value['application'])
    if target!=apps/NAME or target.name!=NAME:raise ValueError('Installation receipt mismatch')
    if target.exists():shutil.rmtree(target)
    manifest.unlink()
    return {'uninstalled':True,'dataPreservedAt':str(base),'trackingSkillPreserved':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--apps-dir',type=Path,default=Path.home()/'Applications');p.add_argument('--base',type=Path,default=Path.home()/'Library/Application Support/RoadmapDashboardPreview');p.add_argument('--python',default=sys.executable);p.add_argument('--dry-run',action='store_true');p.add_argument('--uninstall',action='store_true');args=p.parse_args()
    try:
        if args.uninstall and args.dry_run:result={'dryRun':True,'removeApplicationOnly':str(args.apps_dir/NAME),'preserveData':str(args.base)}
        elif args.uninstall:result=uninstall(args.apps_dir,args.base)
        else:result=install(args.apps_dir,args.base,args.python,args.dry_run)
        print(json.dumps(result))
    except (ValueError,OSError,subprocess.CalledProcessError) as e:print(json.dumps({'ok':False,'error':str(e)}));sys.exit(1)
if __name__=='__main__':main()
