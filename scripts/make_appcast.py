#!/usr/bin/env python3
"""Sign a release archive using Sparkle's Keychain tool and emit an update feed."""
import argparse,plistlib,subprocess,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
from urllib.parse import urlsplit
NS='http://www.andymatuschak.org/xml-namespaces/sparkle'
ET.register_namespace('sparkle',NS)
def make(archive,url,output,sparkle,account):
    address=urlsplit(url)
    if address.scheme!='https' or not address.hostname or address.username or address.password:raise ValueError('A public HTTPS download URL is required')
    with zipfile.ZipFile(archive) as z:
        paths=[n for n in z.namelist() if n.endswith('.app/Contents/Info.plist') and not n.startswith('__MACOSX/') and n.count('.app/')==1]
        if len(paths)!=1:raise ValueError('Expected one application bundle')
        info=plistlib.loads(z.read(paths[0]))
    tool=sparkle/'bin/sign_update'
    signature=subprocess.check_output([str(tool),'--account',account,'-p',str(archive)],text=True).strip()
    subprocess.run([str(tool),'--account',account,'--verify',str(archive),signature],check=True,capture_output=True)
    root=ET.Element('rss',{'version':'2.0'});channel=ET.SubElement(root,'channel');ET.SubElement(channel,'title').text='Dashboard for Codex updates'
    item=ET.SubElement(channel,'item');ET.SubElement(item,'title').text='Dashboard for Codex '+info['CFBundleShortVersionString']
    for name,value in [('version',info['CFBundleVersion']),('shortVersionString',info['CFBundleShortVersionString']),('minimumSystemVersion',info.get('LSMinimumSystemVersion','15.0')),('hardwareRequirements','arm64')]:ET.SubElement(item,'{'+NS+'}'+name).text=value
    ET.SubElement(item,'link').text='https://github.com/TeabagCollector/roadmap-dashboard/releases'
    ET.SubElement(item,'description').text='Update Dashboard for Codex. Local roadmaps and preferences are retained. / 更新 Dashboard，保留本机清单与偏好。'
    ET.SubElement(item,'enclosure',{'url':url,'{'+NS+'}edSignature':signature,'length':str(archive.stat().st_size),'type':'application/octet-stream'})
    output.parent.mkdir(parents=True,exist_ok=True);ET.indent(root);ET.ElementTree(root).write(output,encoding='utf-8',xml_declaration=True)
    return {'version':info['CFBundleShortVersionString'],'build':info['CFBundleVersion'],'output':str(output)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--download-url',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--sparkle-directory',type=Path,required=True);p.add_argument('--key-account',default='io.github.teabagcollector.dashboard-for-codex.updates');a=p.parse_args();print(make(a.archive,a.download_url,a.output,a.sparkle_directory,a.key_account))
