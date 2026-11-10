# Third-Party Notices

## Kubernetes documentation

OpsLens can download a selected subset of the Kubernetes documentation from:

- Repository: <https://github.com/kubernetes/website>
- Copyright: The Kubernetes Authors and contributors
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)
- License text: <https://creativecommons.org/licenses/by/4.0/>

Each downloaded document receives frontmatter containing its upstream source URL and license. `data/provenance.json` records the raw URL, retrieval time, upstream reference, and SHA-256 content hash.

Kubernetes is a registered trademark of The Linux Foundation. This project is independent and is not endorsed by the Kubernetes project or The Linux Foundation.

## Hugging Face models

The default configuration downloads these model artifacts at runtime:

- `sentence-transformers/all-MiniLM-L6-v2`
- `cross-encoder/ms-marco-MiniLM-L-6-v2`

Model licenses and model cards are maintained on their respective Hugging Face pages. Review them before redistribution or commercial use. Model weights are not committed to this repository.

## Python dependencies

Python packages are installed from their upstream distributions. Their own licenses apply; see `pyproject.toml` and the generated lockfile for the resolved dependency list.

