"""Loopback-only demo API. The corpus is configured by the local operator."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .answer import ask
from .evaluate import ROOT
from .retrieval import Index,read_chunks


def make_handler(index,enable_llm=False):
    class Handler(BaseHTTPRequestHandler):
        def respond(self,status,data,content_type='application/json; charset=utf-8'):
            body=data if isinstance(data,bytes) else json.dumps(data,allow_nan=False).encode()
            self.send_response(status);self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)

        def do_GET(self):
            if self.path=='/':self.respond(200,(ROOT/'web/index.html').read_bytes(),'text/html; charset=utf-8')
            elif self.path=='/health':self.respond(200,{'status':'ok'})
            elif self.path=='/api/corpus':
                self.respond(200,{'documents':sorted({c.document for c in index.chunks}),
                                  'chunks':len(index.chunks),'llm_enabled':enable_llm})
            else:self.respond(404,{'error':'Route not found.'})

        def do_POST(self):
            if self.path!='/api/ask':return self.respond(404,{'error':'Route not found.'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                return self.respond(415,{'error':'Use application/json.'})
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:
                return self.respond(403,{'error':'Cross-origin requests are disabled.'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 1<=size<=8192:raise ValueError('JSON body must be 1–8192 bytes.')
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict):raise ValueError('Expected a JSON object.')
                use_llm=data.get('use_llm',False)
                if not isinstance(use_llm,bool):raise ValueError('use_llm must be a boolean.')
                if use_llm and not enable_llm:raise ValueError('Optional model answers are disabled by the server.')
                self.respond(200,ask(index,data.get('question'),use_llm))
            except (ValueError,TypeError) as exc:self.respond(400,{'error':str(exc)})
    return Handler


def serve(directory,port=8020,enable_llm=False):
    index=Index(read_chunks(directory))
    server=ThreadingHTTPServer(('127.0.0.1',port),make_handler(index,enable_llm))
    print(f'EvidenceQA demo: http://127.0.0.1:{server.server_port} · {len(index.chunks)} chunks')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
