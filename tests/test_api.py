import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from evidenceqa.evaluate import ROOT
from evidenceqa.retrieval import Index,read_chunks
from evidenceqa.server import make_handler


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(Index(read_chunks(ROOT/'corpus'))))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def post(self,data):
        request=urllib.request.Request(self.base+'/api/ask',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        return urllib.request.urlopen(request)

    def test_question_endpoint_returns_source_citation(self):
        with self.post({'question':'What is the refund window after purchase?'}) as response:
            result=json.load(response);self.assertFalse(result['abstained'])
            self.assertEqual(result['citations'][0]['document'],'refunds.md')

    def test_corpus_endpoint_and_interface(self):
        with urllib.request.urlopen(self.base+'/api/corpus') as response:
            result=json.load(response);self.assertEqual(len(result['documents']),4)
            self.assertFalse(result['llm_enabled'])
        with urllib.request.urlopen(self.base) as response:self.assertIn(b'inspectable evidence',response.read())

    def test_llm_cannot_be_enabled_by_remote_request(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.post({'question':'What is the refund window?','use_llm':True})
        self.assertEqual(error.exception.code,400)

    def test_invalid_question_returns_400(self):
        with self.assertRaises(urllib.error.HTTPError) as error:self.post({'question':{'bad':'shape'}})
        self.assertEqual(error.exception.code,400)
