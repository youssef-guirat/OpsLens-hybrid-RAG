import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

UPSTREAM_COMMIT = "96dc460e7f82a376d33fa1f11437fe6175c65c1a"
REPOSITORY = "https://github.com/kubernetes/website"
RAW_ROOT = f"https://raw.githubusercontent.com/kubernetes/website/{UPSTREAM_COMMIT}"

DOCUMENTS = {
    "debug-running-pod.md": "content/en/docs/tasks/debug/debug-application/debug-running-pod.md",
    "debug-service.md": "content/en/docs/tasks/debug/debug-application/debug-service.md",
    "determine-pod-failure.md": (
        "content/en/docs/tasks/debug/debug-application/determine-reason-pod-failure.md"
    ),
    "debug-cluster.md": "content/en/docs/tasks/debug/debug-cluster/_index.md",
    "observability.md": "content/en/docs/concepts/cluster-administration/observability.md",
    "logging-architecture.md": "content/en/docs/concepts/cluster-administration/logging.md",
    "pod-lifecycle.md": "content/en/docs/concepts/workloads/pods/pod-lifecycle.md",
    "services.md": "content/en/docs/concepts/services-networking/service.md",
    "health-probes.md": (
        "content/en/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes.md"
    ),
}


def download(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "OpsLens-RAG-Demo/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def frontmatter(source_url: str) -> str:
    return (
        "---\n"
        f'source_url: "{source_url}"\n'
        f'upstream_repository: "{REPOSITORY}"\n'
        'license: "CC-BY-4.0"\n'
        "---\n\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch an attributed Kubernetes docs subset")
    parser.add_argument("--output", type=Path, default=Path("data/documents/kubernetes"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    for filename, upstream_path in DOCUMENTS.items():
        raw_url = f"{RAW_ROOT}/{upstream_path}"
        source_url = f"{REPOSITORY}/blob/{UPSTREAM_COMMIT}/{upstream_path}"
        try:
            content = download(raw_url)
            payload = f"{frontmatter(source_url)}{content}"
            destination = args.output / filename
            destination.write_text(payload, encoding="utf-8")
            records.append(
                {
                    "local_path": destination.as_posix(),
                    "source_url": source_url,
                    "raw_url": raw_url,
                    "license": "CC-BY-4.0",
                    "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
                    "retrieved_at": datetime.now(UTC).isoformat(),
                    "upstream_ref": UPSTREAM_COMMIT,
                }
            )
            print(f"fetched {filename}")
        except (urllib.error.URLError, TimeoutError) as exc:
            failures.append({"filename": filename, "url": raw_url, "error": str(exc)})
            print(f"warning: could not fetch {filename}: {exc}")

    manifest = {
        "repository": REPOSITORY,
        "license": "CC-BY-4.0",
        "documents": records,
        "failures": failures,
    }
    Path("data/provenance.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"downloaded={len(records)} failed={len(failures)}")
    if not records:
        raise SystemExit("No documents were downloaded")


if __name__ == "__main__":
    main()

