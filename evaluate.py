import json
import time
from collections import Counter
from main import extract_schema, text_to_sql, run_sql, db_path


def normalize(value):
    # Round numbers so 12 and 12.0 (or 3.14159 and 3.14) count as the same
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    return str(value).strip()


def results_match(gold_rows, pred_rows):
    gold = [tuple(normalize(v) for v in row) for row in gold_rows]
    pred = [tuple(normalize(v) for v in row) for row in pred_rows]

    # 1. Exact match (ignoring row order)
    if Counter(gold) == Counter(pred):
        return True

    # 2. Lenient match: same number of rows, and every gold column
    #    appears in the prediction (the AI may add extra columns like IDs or names)
    if len(gold) != len(pred) or not gold:
        return False
    pred_columns = [Counter(col) for col in zip(*pred)]
    for gold_col in zip(*gold):
        if Counter(gold_col) not in pred_columns:
            return False
    return True


def main():
    with open("eval_questions.json") as f:
        tests = json.load(f)

    schema = extract_schema(db_path)
    results = []
    passed = 0

    for i, test in enumerate(tests, start=1):
        question = test["question"]
        _, gold_rows = run_sql(db_path, test["gold_sql"])

        try:
            pred_sql = text_to_sql(schema, question)
            _, pred_rows = run_sql(db_path, pred_sql)
            correct = results_match(gold_rows, pred_rows)
            error = None
        except Exception as e:
            pred_sql = pred_sql if "pred_sql" in locals() else ""
            correct = False
            error = str(e)

        passed += correct
        status = "PASS" if correct else "FAIL"
        print(f"[{i:02d}] {status}  {question}")

        results.append({
            "question": question,
            "gold_sql": test["gold_sql"],
            "predicted_sql": pred_sql,
            "correct": correct,
            "error": error,
        })
        time.sleep(2)  # stay under Groq's free-tier rate limits

    accuracy = passed / len(tests) * 100
    print(f"\nExecution accuracy: {passed}/{len(tests)} = {accuracy:.1f}%")

    with open("eval_results.json", "w") as f:
        json.dump({"accuracy": accuracy, "results": results}, f, indent=2)
    print("Details saved to eval_results.json")


if __name__ == "__main__":
    main()