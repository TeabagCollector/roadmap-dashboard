#!/usr/bin/env python3
"""Export reviewed source paths only. Never crawl a personal workspace."""
import argparse, hashlib, json, os, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
 '.gitignore','LICENSE','README.md','README.zh-CN.md','build.sh',
 'Preview English.command','预览中文版.command','Install.command',
 'src/Monitor.swift','src/index.html','src/style.css','src/app.js',
 'src/conversation-model.js','src/connection.js','src/i18n.js','src/demo-data.js','src/preview.js',
 'sync/dashboard.py','sync/setup.py','sync/client.py','samples/demo.json',
 'tests/test_sync.py','tests/test_setup.py','tests/test_export.py','tests/conversations.test.cjs',
 'scripts/export_source.py','scripts/install.py','scripts/package_macos.py','docs/INSTALL-MACOS.md','docs/CONNECT.md','docs/PRIVACY.md','docs/LANDSCAPE.md',
 'docs/preview-en.png','docs/preview-zh.png','docs/demo-en.gif','docs/demo-zh.gif','docs/DEMO.md',
 'skills/roadmap-dashboard-sync/SKILL.md',
)

def scan_bytes(name, data):
    if name.endswith('.gif'):
        if not data.startswith((b'GIF87a',b'GIF89a')): raise ValueError('Not a GIF: '+name)
        # Only graphics/control blocks and the standard loop extension belong
        # in the rendered walkthrough; reject embedded text or custom metadata.
        offset=13
        if data[10]&128: offset+=3*(2**((data[10]&7)+1))
        def blocks(pos):
            while True:
                length=data[pos];pos+=1
                if not length:return pos
                pos+=length
                if pos>len(data):raise ValueError('Truncated GIF: '+name)
        while offset<len(data):
            marker=data[offset];offset+=1
            if marker==0x3b:return
            if marker==0x21:
                kind=data[offset];offset+=1
                if kind==0xff and data[offset+1:offset+12]!=b'NETSCAPE2.0':raise ValueError('GIF metadata: '+name)
                if kind not in (0xf9,0xff):raise ValueError('GIF text metadata: '+name)
                offset=blocks(offset)
            elif marker==0x2c:
                flags=data[offset+8];offset+=9
                if flags&128:offset+=3*(2**((flags&7)+1))
                offset=blocks(offset+1)
            else:raise ValueError('Invalid GIF block: '+name)
        raise ValueError('Missing GIF trailer: '+name)
    if name.endswith('.png'):
        # Only decoded native demo screenshots enter this allowlist. PNG text
        # metadata, if present, is rejected rather than treated as a photograph.
        if not data.startswith(b'\x89PNG\r\n\x1a\n'): raise ValueError('Not a PNG: '+name)
        offset=8
        while offset+12<=len(data):
            length=int.from_bytes(data[offset:offset+4],'big');kind=data[offset+4:offset+8]
            if kind in (b'tEXt',b'zTXt',b'iTXt',b'eXIf'): raise ValueError('Image metadata: '+name)
            offset+=12+length
        return
    text=data.decode('utf-8')
    private_path=r'/'+'Users/'+r'[^/\s\"\']+/'
    secret=r'\b(?:sk'+'-'+r'[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|cmh'+'-'+r'[A-Za-z0-9_-]{8,})'
    if re.search(private_path,text) or re.search(secret,text):
        raise ValueError('Private path or secret-like value: '+name)
    if Path.home().name in text and Path.home().name not in ('root','runner'):
        raise ValueError('Local user name: '+name)
    ids=re.findall(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',text,re.I)
    if any(not value.startswith('00000000-') for value in ids):
        raise ValueError('Non-demo thread identifier: '+name)

def collect(root=ROOT):
    values={}
    for name in FILES:
        path=root/name
        if path.is_symlink() or root.resolve() not in path.resolve().parents:
            raise ValueError('Symlink or outside-root file: '+name)
        data=path.read_bytes();scan_bytes(name,data);values[name]=data
    return values

def export(output, root=ROOT):
    values=collect(root)
    manifest={'format':1,'scope':'Reviewed source and fictional demo assets only; no runtime data',
      'files':[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in sorted(values.items())]}
    values['SOURCE-MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    output=Path(output)
    if output.resolve() in [(root/name).resolve() for name in FILES]: raise ValueError('Output would overwrite source')
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix('.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(values.items()):
            info=zipfile.ZipInfo('roadmap-dashboard/'+name,date_time=(2026,11,4,0,0,0))
            info.create_system=3
            info.external_attr=(0o100755 if name.endswith(('.sh','.command')) else 0o100644)<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    os.replace(temporary,output)
    return {'files':len(values),'archive':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/roadmap-dashboard-source-preview.zip')
    args=parser.parse_args();print(json.dumps(export(args.output)))
if __name__=='__main__':main()
