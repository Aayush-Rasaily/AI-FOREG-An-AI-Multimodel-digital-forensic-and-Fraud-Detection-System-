"""Policy constants and deterministic scoring weights for the knowledge graph."""

from __future__ import annotations

KG_ENGINE_VERSION = "9b.1.0"
KG_POLICY_VERSION = "1.0"

# Identity-key merge confidence (exact match only — no fuzzy AI).
MERGE_CONFIDENCE: dict[str, float] = {
    "HASH": 1.0,
    "EMAIL": 0.98,
    "PHONE": 0.97,
    "IMEI": 0.96,
    "MAC": 0.96,
    "SERIAL": 0.95,
    "DEVICE_ID": 0.95,
    "SIGNATURE": 0.94,
    "CRYPTO_WALLET": 0.94,
    "BANK_ACCOUNT": 0.93,
    "LICENSE_PLATE": 0.92,
    "IP_ADDRESS": 0.90,
    "DOMAIN": 0.88,
    "URL": 0.88,
    "GPS": 0.90,
    "QR": 0.95,
    "FILENAME_HASH": 0.99,
    "DEFAULT": 0.80,
}

RELATIONSHIP_BASE_WEIGHT: dict[str, float] = {
    "USES_DEVICE": 0.85,
    "OWNS": 0.90,
    "CREATED": 0.88,
    "SENT": 0.86,
    "RECEIVED": 0.86,
    "LOCATED_AT": 0.84,
    "CAPTURED_BY": 0.87,
    "REFERENCES": 0.80,
    "DERIVED_FROM": 0.92,
    "SIMILAR_TO": 0.75,
    "CORRELATED_WITH": 0.88,
    "SHARES_IDENTIFIER": 0.95,
    "MENTIONS": 0.78,
    "CONNECTED_TO": 0.70,
    "PART_OF": 0.85,
    "SUPPORTS": 0.82,
    "CONTRADICTS": 0.82,
    "OBSERVED_AT": 0.80,
    "ASSOCIATED_WITH": 0.72,
}

SUPPORT_BOOST = 0.02
SUPPORT_BOOST_CAP = 0.10
PROVENANCE_BOOST = 0.01
PROVENANCE_BOOST_CAP = 0.05
