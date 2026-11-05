#!/usr/bin/env python3
"""Fetch a pinned official Sparkle build for release packaging."""
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path
VERSION='2.10.1'
URL='https://github.com/sparkle-project/Sparkle/releases/download/2.10.1/Sparkle-2.10.1.tar.xz'
SHA256='1a856d2a9edb8e628de88121d7be04cf0e2167f8641650b78fca00b14244cf27'
def fetch(output):
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    archive=output/('Sparkle-'+VERSION+'.tar.xz')
    if not archive.exists():subprocess.run(['curl','--fail','--location',URL,'--output',str(archive)],check=True)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA256:raise ValueError('Official Sparkle archive checksum mismatch')
    destination=output/VERSION
    if not destination.exists():
        destination.mkdir()
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                target=(destination/member.name).resolve()
                if destination not in target.parents:raise ValueError('Unsafe archive path')
                if member.isdev() or member.isfifo():raise ValueError('Unexpected archive member')
                if member.issym() or member.islnk():
                    link=(target.parent/member.linkname).resolve() if member.issym() else (destination/member.linkname).resolve()
                    if destination not in link.parents:raise ValueError('Unsafe archive link')
            tar.extractall(destination)
    return {'version':VERSION,'directory':str(destination),'sha256':SHA256}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'artifacts/sparkle');a=p.parse_args();print(json.dumps(fetch(a.output)))
