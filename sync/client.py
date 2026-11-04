#!/usr/bin/env python3
"""Agent entry point follows the explicit connection, not a copied ledger."""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
import dashboard as d
import setup

def main(base=None):
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['status','request']);args=parser.parse_args()
    base=base or setup.default_base()
    try:
        connection=setup.status(base)
        if args.command=='status':result={'ok':True,'connection':connection}
        else:
            if not connection['connected']:raise ValueError('connect-first')
            request=json.load(sys.stdin)
            if request.get('op') not in ('get','plan','report','accept'):raise ValueError('agent-operation-not-allowed')
            result={'ok':True,'ledger':d.mutate(request,Path(connection['ledgerDirectory']))}
    except (ValueError,OSError,KeyError,StopIteration) as e:result={'ok':False,'error':str(e)}
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
