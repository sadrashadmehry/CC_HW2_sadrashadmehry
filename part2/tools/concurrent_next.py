"""Consume a seeded student-000.. queue with concurrent POST /next requests.

First run concurrent_join.py WITHOUT --drain on a separate empty test queue.
This tool consumes that queue. Requests are never retried.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def post_next(base):
    try:
        request = Request(base + "/next", data=b"", method="POST")
        with urlopen(request, timeout=60) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8")
    except (URLError, OSError) as error:
        return 0, str(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--workers", type=int, default=200)
    args = parser.parse_args()
    if args.count < 1 or args.workers < 1:
        parser.error("count and workers must be positive")
    base = args.url.rstrip("/")
    start = threading.Event()

    def take_one(_):
        start.wait()
        return post_next(base)

    with ThreadPoolExecutor(max_workers=min(args.workers, args.count)) as pool:
        futures = [pool.submit(take_one, i) for i in range(args.count)]
        start.set()
        results = [future.result() for future in futures]
    names = [body for status, body in results if status == 200]
    errors = [{"status": status, "body": body} for status, body in results if status != 200]
    actual = Counter(names)
    wanted = Counter(f"student-{i:03d}" for i in range(args.count))
    duplicates = {name: count for name, count in actual.items() if count > 1}
    final_status, final_body = post_next(base)
    passed = not errors and actual == wanted and (final_status, final_body) == (404, "empty")
    print(json.dumps({"sent": args.count, "successful": len(names),
                      "duplicate_names": duplicates,
                      "missing_names": list((wanted - actual).elements()),
                      "extra_names": list((actual - wanted).elements()),
                      "errors": errors,
                      "final_next": {"status": final_status, "body": final_body},
                      "passed": passed}, indent=2, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
