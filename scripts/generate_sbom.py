"""
GuardWAF Software Bill of Materials (SBOM) Generator.
Generates an SPDX-compliant SBOM JSON file documenting all Python dependencies, version specs, and metadata.
"""

import sys
import json
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timezone
import importlib.metadata

def generate_sbom() -> dict:
    packages = []
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        version = dist.version
        summary = dist.metadata.get("Summary", "")
        license_type = dist.metadata.get("License", "Unknown")
        packages.append({
            "name": name,
            "SPDXID": f"SPDXRef-Package-{name}-{version}",
            "versionInfo": version,
            "summary": summary,
            "licenseConcluded": license_type,
            "supplier": "NOASSERTION"
        })

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "GuardWAF-Platform-SBOM",
        "documentNamespace": f"https://guardwaf.io/spdxdocs/guardwaf-v1.0-{int(datetime.now(timezone.utc).timestamp())}",
        "creationInfo": {
            "created": datetime.now(timezone.utc).isoformat(),
            "creators": ["Tool: GuardWAF-SBOM-Generator-1.0"]
        },
        "packages": sorted(packages, key=lambda p: p["name"].lower())
    }
    return sbom

def main():
    parser = argparse.ArgumentParser(description="Generate SPDX SBOM JSON")
    parser.add_argument("--output", default="sbom.spdx.json", help="Output filepath")
    args = parser.parse_args()

    sbom_data = generate_sbom()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(sbom_data, f, indent=2)

    print(f"✅ SBOM successfully generated: '{args.output}' ({len(sbom_data['packages'])} packages documented).")

if __name__ == "__main__":
    main()
