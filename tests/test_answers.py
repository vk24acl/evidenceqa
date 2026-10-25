from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from evidenceqa.answer import ask
from evidenceqa.evaluate import ROOT,evaluate
from evidenceqa.generation import validate_answer
from evidenceqa.retrieval import Chunk,Index,read_chunks


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.index=Index(read_chunks(ROOT/'corpus'))

    def test_known_answer_quotes_exact_source(self):
        result=ask(self.index,'What is the refund window after purchase?')
        self.assertFalse(result['abstained']);self.assertIn('14 calendar days',result['answer'])
        for citation in result['citations']:self.assertIn(citation['quote'],citation['text'])

    def test_unrelated_question_abstains_without_citations(self):
        result=ask(self.index,'Which planet has the most moons?')
        self.assertTrue(result['abstained']);self.assertEqual(result['citations'],[])

    def test_chunk_ids_stable_and_lines_reconstruct_text(self):
        again=read_chunks(ROOT/'corpus')
        self.assertEqual([c.id for c in self.index.chunks],[c.id for c in again])
        for c in again:
            lines=(ROOT/'corpus'/c.document).read_text().splitlines()
            self.assertEqual(c.text,'\n'.join(lines[c.start_line-1:c.end_line]).strip())

    def test_empty_and_oversized_questions_rejected(self):
        for question in ['',None,'x'*2001]:
            with self.assertRaises(ValueError):ask(self.index,question)

    def test_punctuation_only_query_abstains(self):
        self.assertTrue(ask(self.index,'???')['abstained'])

    def test_unknown_llm_citation_is_rejected(self):
        with self.assertRaises(ValueError):validate_answer({'answer':'Invented [bad]','citations':['bad']},{'good'})

    def test_missing_inline_llm_citation_is_rejected(self):
        with self.assertRaises(ValueError):validate_answer({'answer':'Unsupported assertion','citations':['good']},{'good'})

    def test_llm_provider_failure_falls_back_to_extracts(self):
        with patch('evidenceqa.generation.synthesize',side_effect=RuntimeError('offline')):
            result=ask(self.index,'What is the refund window after purchase?',use_llm=True)
        self.assertEqual(result['mode'],'extractive');self.assertIn('14 calendar days',result['answer'])
        self.assertIn('fallback_reason',result)

    def test_valid_mocked_synthesis_keeps_only_supplied_citations(self):
        original=ask(self.index,'What is the refund window after purchase?')
        cid=original['citations'][0]['id']
        with patch('evidenceqa.generation.synthesize',return_value={'answer':f'Within 14 calendar days [{cid}]','citations':[cid]}):
            result=ask(self.index,'What is the refund window after purchase?',use_llm=True)
        self.assertEqual(result['mode'],'llm');self.assertEqual(result['citations'][0]['id'],cid)

    def test_empty_corpus_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):read_chunks(directory)

    def test_authored_fixture_has_valid_citations(self):
        result=evaluate()
        self.assertEqual(result['cases'],12)
        self.assertEqual(result['retrieval_recall_at_3'],1)
        self.assertEqual(result['citation_id_validity_rate'],1)


if __name__=='__main__':unittest.main()
