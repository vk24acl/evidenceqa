"""A transparent, small authored fixture; not an independent benchmark."""
from pathlib import Path
import json
from .answer import ask
from .retrieval import Index,read_chunks

ROOT=Path(__file__).resolve().parents[1]


def evaluate(directory=None):
    index=Index(read_chunks(directory or ROOT/'corpus'))
    cases=[json.loads(line) for line in (ROOT/'eval/questions.jsonl').read_text().splitlines() if line.strip()]
    results=[]
    for case in cases:
        answer=ask(index,case['question'])
        retrieved={r['chunk'].document for r in index.search(case['question'],3)}
        citation_ids={c.id for c in index.chunks}
        valid=all(c['id'] in citation_ids and c['quote'] in c['text'] for c in answer['citations'])
        results.append({'id':case['id'],'answerable':case['answerable'],
            'retrieval_hit':case.get('source') in retrieved if case['answerable'] else None,
            'correct_abstention':answer['abstained']==(not case['answerable']),
            'expected_phrase_found':case.get('phrase','').lower() in answer['answer'].lower() if case['answerable'] else None,
            'citation_ids_valid':valid,'answer':answer['answer']})
    positive=[r for r in results if r['answerable']];negative=[r for r in results if not r['answerable']]
    return {'fixture':'12 authored questions about fictional sample policies; not an independent benchmark',
            'mode':'offline extractive','cases':len(results),'answerable':len(positive),'unanswerable':len(negative),
            'retrieval_recall_at_3':sum(r['retrieval_hit'] for r in positive)/len(positive),
            'answerable_expected_phrase_rate':sum(r['expected_phrase_found'] for r in positive)/len(positive),
            'unanswerable_abstention_rate':sum(r['correct_abstention'] for r in negative)/len(negative),
            'citation_id_validity_rate':sum(r['citation_ids_valid'] for r in results)/len(results),
            'results':results,'llm_evaluated':False}
