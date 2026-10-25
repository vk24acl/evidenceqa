import argparse
import json
from pathlib import Path
from .answer import ask
from .evaluate import ROOT,evaluate
from .retrieval import Index,read_chunks


def main():
    parser=argparse.ArgumentParser(description='EvidenceQA: source-cited document answers')
    parser.add_argument('command',choices=['ask','serve','evaluate'],nargs='?',default='serve')
    parser.add_argument('question',nargs='?')
    parser.add_argument('--corpus',type=Path,default=ROOT/'corpus')
    parser.add_argument('--port',type=int,default=8020)
    parser.add_argument('--enable-llm',action='store_true',help='Opt in to sending retrieved evidence to OpenAI')
    args=parser.parse_args()
    if args.command=='serve':
        from .server import serve
        serve(args.corpus,args.port,args.enable_llm)
    elif args.command=='ask':
        if args.question is None:parser.error('ask requires a quoted question')
        print(json.dumps(ask(Index(read_chunks(args.corpus)),args.question,args.enable_llm),indent=2))
    else:
        report=evaluate(args.corpus)
        destination=ROOT/'reports';destination.mkdir(exist_ok=True)
        (destination/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))


if __name__=='__main__':main()
