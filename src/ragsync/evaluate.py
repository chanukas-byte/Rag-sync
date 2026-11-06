import json
from pathlib import Path

from ragsync.chat import retrieve
from ragsync.sources.hybrid import hybrid_retrieve

QUESTIONS_PATH = Path("eval/questions.jsonl")
K = 5


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict]:
    lines = path.read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def first_rank(chunks: list[dict], expected_doc: str) -> int | None:
    for position, chunk in enumerate(chunks, start=1):
        if chunk["title"].startswith(expected_doc):
            return position
    return None


def score(ranks: list[int | None]) -> dict:
    total = len(ranks)
    if total == 0:
        return {"questions": 0, "hit_rate": 0.0, "mrr": 0.0}
    hits = sum(1 for rank in ranks if rank is not None)
    mrr = sum(1 / rank for rank in ranks if rank is not None) / total
    return {"questions": total, "hit_rate": hits / total, "mrr": mrr}


def evaluate(path: Path = QUESTIONS_PATH, k: int = K, retriever=None) -> dict:
    retriever = retriever or retrieve
    ranks = []
    for item in load_questions(path):
        chunks = retriever(item["question"], k)
        rank = first_rank(chunks, item["expected_doc"])
        ranks.append(rank)
        label = f"rank {rank}" if rank else "MISS"
        print(f"{label:>7}  {item['question']}")
    result = score(ranks)
    print()
    print(f"Questions:       {result['questions']}")
    print(f"Hit rate@{k}:     {result['hit_rate']:.0%}")
    print(f"MRR:             {result['mrr']:.3f}")
    return result


if __name__ == "__main__":
    import sys

    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    path = Path(args[0]) if args else QUESTIONS_PATH
    if "--hybrid" in sys.argv:
        print("Mode: hybrid")
        evaluate(path, retriever=hybrid_retrieve)
    else:
        print("Mode: vector only")
        evaluate(path)
