"""Inspectable BM25 retrieval with stable chunk IDs and exact line provenance."""
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib
import math
import re

STOP=set('a an and are as at be been by can could did do does for from had has have how i if in into is it its me my of on or our please should that the their there these they this to us was we were what when where which who why will with would you your tell many much'.split())


def tokens(text):
    return [word for word in re.findall(r'[a-z0-9]+',text.lower()) if word not in STOP]


@dataclass(frozen=True)
class Chunk:
    id: str
    document: str
    heading: str
    start_line: int
    end_line: int
    text: str


def read_chunks(directory, max_words=180):
    directory=Path(directory).resolve()
    result=[]
    for path in sorted(directory.rglob('*')):
        if path.suffix.lower() not in {'.md','.txt'} or not path.is_file():continue
        if path.is_symlink() or not path.resolve().is_relative_to(directory):continue
        if path.stat().st_size>2_000_000:raise ValueError('Document exceeds 2 MB: '+path.name)
        lines=path.read_text(encoding='utf-8').splitlines()
        heading=path.stem;buffer=[];start=1
        def flush(end):
            if not buffer:return
            content='\n'.join(buffer).strip()
            if not content:return
            relative=path.relative_to(directory).as_posix()
            digest=hashlib.sha256(f'{relative}:{start}:{content}'.encode()).hexdigest()[:12]
            result.append(Chunk(digest,relative,heading,start,end,content))
        for number,line in enumerate(lines,1):
            if line.startswith('#'):
                flush(number-1);buffer=[];heading=line.lstrip('#').strip();start=number+1
            elif sum(len(x.split()) for x in buffer)+len(line.split())>max_words and buffer:
                flush(number-1);buffer=[line];start=number
            else:
                if not buffer:start=number
                buffer.append(line)
        flush(len(lines))
    if not result:raise ValueError('No text chunks found. Add UTF-8 .md or .txt documents.')
    return result


class Index:
    def __init__(self,chunks):
        self.chunks=list(chunks)
        if not self.chunks:raise ValueError('Cannot index an empty corpus.')
        self.counts=[Counter(tokens(c.heading+' '+c.text)) for c in self.chunks]
        self.lengths=[sum(c.values()) for c in self.counts]
        self.average=sum(self.lengths)/len(self.lengths) or 1
        self.df=Counter(word for counter in self.counts for word in counter)

    def idf(self,word):
        return math.log(1+(len(self.chunks)-self.df[word]+.5)/(self.df[word]+.5))

    def search(self,question,k=3):
        query=set(tokens(question))
        if not query:return []
        ranked=[]
        for chunk,count,length in zip(self.chunks,self.counts,self.lengths):
            overlap=query & count.keys()
            score=sum(self.idf(t)*(count[t]*2.5)/(count[t]+1.5*(.25+.75*length/self.average)) for t in overlap)
            if score>0:
                ranked.append({'chunk':chunk,'score':float(score),'coverage':len(overlap)/len(query),
                               'matched_terms':sorted(overlap)})
        return sorted(ranked,key=lambda r:(-r['score'],r['chunk'].id))[:k]
