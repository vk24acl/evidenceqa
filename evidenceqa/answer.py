"""Evidence-first answers: quoted source sentences or optional bounded synthesis."""
from dataclasses import asdict
import re
from .retrieval import tokens


def ask(index,question,use_llm=False):
    if not isinstance(question,str) or not 3<=len(question.strip())<=2000:
        raise ValueError('Question must contain 3–2000 characters.')
    question=question.strip()
    retrieved=index.search(question,3)
    qualifying=[r for r in retrieved if r['coverage']>=.35]
    candidates=[];query=set(tokens(question))
    for row in qualifying:
        for sentence in re.split(r'(?<=[.!?])\s+|\n',row['chunk'].text):
            overlap=query & set(tokens(sentence))
            coverage=len(overlap)/len(query) if query else 0
            if coverage>=.35 and sentence.strip():
                candidates.append((sum(index.idf(t) for t in overlap),sentence.strip(),row))
    if not candidates:
        return {'answer':'I could not find enough evidence in these documents to answer that question.',
                'abstained':True,'mode':'extractive','citations':[],
                'retrieved':[{'document':r['chunk'].document,'id':r['chunk'].id,
                              'score':r['score'],'coverage':r['coverage']} for r in retrieved]}
    candidates.sort(key=lambda c:-c[0])
    selected=[];seen=set()
    for score,sentence,row in candidates:
        if sentence not in seen:
            selected.append((sentence,row));seen.add(sentence)
        if len(selected)==2:break
    citations=[]
    for sentence,row in selected:
        citation=asdict(row['chunk'])
        citation['quote']=sentence;citation['score']=row['score'];citation['coverage']=row['coverage']
        if citation['id'] not in {c['id'] for c in citations}:citations.append(citation)
    answer='\n'.join(f'{sentence} [{row["chunk"].id}]' for sentence,row in selected)
    result={'answer':answer,'abstained':False,'mode':'extractive','citations':citations,
            'retrieved':[{'document':r['chunk'].document,'id':r['chunk'].id,
                          'score':r['score'],'coverage':r['coverage']} for r in retrieved]}
    if use_llm:
        from .generation import synthesize
        try:
            generated=synthesize(question,citations)
            result.update(answer=generated['answer'],mode='llm',
                          citations=[c for c in citations if c['id'] in generated['citations']])
        except (ValueError,RuntimeError):
            result['fallback_reason']='Optional synthesis was unavailable or failed citation validation; showing source extracts.'
    return result
