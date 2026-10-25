# Design decisions and limits

## Retrieval first

BM25 is deterministic, small and easy to inspect. The tokenizer normalises
case, keeps alphanumeric terms and removes a fixed stopword set. Chunks follow
Markdown headings and line boundaries, targeting 180 words. Stable IDs hash
the relative filename, start line and content. Source references include line
ranges so a reviewer can trace the answer to the corpus.

This baseline does not have embeddings, semantic reranking or conversational
memory. It can miss paraphrases, fail on ambiguous wording and retrieve
lexically relevant evidence that does not fully answer the question. Long
individual source lines can exceed the target chunk size.

## Evidence and abstention

Top-3 chunks are ranked by BM25. Chunks and source sentences must cover at
least 35% of the non-stopword query terms. Up to two exact sentences are
returned. This is a transparent lexical heuristic, not calibrated confidence
or a semantic answerability classifier. A supported phrase in the source may
still need a human to interpret the full policy and its exceptions.

## Optional synthesis

An explicit server flag enables optional provider use; the browser must also
select it. The prompt treats document content as untrusted data. A structured
response restricts citation IDs to supplied evidence; local validation checks
shape, non-empty references and matching inline IDs. Errors fall back to exact
extracts. No secret is returned in errors or committed in the repository.

These controls do not eliminate prompt injection or prove factual entailment.
No production security or grounding guarantee is claimed. The provider adapter
has mocked tests; no live model call was executed for the portfolio results.

## Evaluation

The 12 questions and four documents were authored together for an explicit
smoke fixture. Retrieval recall checks whether the expected document appears
in the top three. Phrase matching checks a specified answer fragment. The
unsupported-question rate checks four negative examples. Citation checks
verify IDs and exact quoted text. None measures broad semantic correctness,
production latency, robustness across domains or live LLM quality.

## Serving

This standard-library demo serves only a fixed HTML page and named API routes.
It does not expose arbitrary filesystem paths or accept remote document uploads.
The corpus is configured by a local command-line path. Input sizes are bounded;
JSON is required for POST requests; cross-origin browser calls are rejected.
It has no authentication, TLS termination or production rate limiting.

## Next experiments

1. Evaluate on independently authored questions and longer, conflicting documents.
2. Add paraphrase retrieval and compare BM25, embeddings and hybrid ranking.
3. Calibrate answerability on held-out questions, including near-miss negatives.
4. Bound exceptionally long source lines without losing exact provenance.
5. Measure generation entailment, injection resistance, cost and latency separately.

## Interview walkthrough

Trace one question from tokenisation to ranking, source selection and citation.
Show an abstention, an invalid model citation and the provider failure fallback.
Explain why exact extraction is useful and why it is not a complete semantic
QA system. Then describe how an independent evaluation would change the design.
