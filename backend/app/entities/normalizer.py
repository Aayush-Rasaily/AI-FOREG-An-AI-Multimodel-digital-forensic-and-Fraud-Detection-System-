"""Deterministic normalization helpers for entity identity keys."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from backend.app.correlation.matchers import (
    extract_emails,
    extract_identifiers,
    extract_phones,
    normalize_email,
    normalize_phone,
)

URL_RE = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+",
    re.IGNORECASE,
)
IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b",
)
# Common crypto address shapes (BTC/ETH-like) — exact string identity only.
WALLET_RE = re.compile(
    r"\b(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{25,62})\b",
)
BANK_RE = re.compile(
    r"\b(?:ACCT|ACCOUNT|IBAN)[-:\s]?[A-Z0-9]{8,34}\b",
    re.IGNORECASE,
)
ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.'\- ]{3,40}\b"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Blvd|Lane|Ln)\b",
    re.IGNORECASE,
)


def normalize_domain(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = cleaned.removeprefix("http://").removeprefix("https://")
    cleaned = cleaned.split("/")[0].split("?")[0]
    if cleaned.startswith("www."):
        cleaned = cleaned[4:]
    return cleaned


def normalize_website(value: str) -> str:
    text = value.strip()
    if not text.lower().startswith(("http://", "https://")):
        text = f"https://{text}"
    parsed = urlparse(text)
    host = (parsed.netloc or parsed.path).lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/") if parsed.path not in {"", "/"} else ""
    return f"{host}{path}".lower()


def normalize_ip(value: str) -> str:
    return value.strip()


def normalize_wallet(value: str) -> str:
    return value.strip()


def normalize_bank_account(value: str) -> str:
    return re.sub(r"[\s:\-]", "", value).upper()


def normalize_hash(value: str) -> str:
    return value.strip().lower()


def normalize_generic(value: str) -> str:
    return value.strip().lower()


def normalize_location(value: str) -> str:
    return value.strip()


def extract_urls(text: str) -> set[str]:
    return {match.strip().rstrip(".,);]") for match in URL_RE.findall(text)}


def extract_ips(text: str) -> set[str]:
    return {normalize_ip(match) for match in IP_RE.findall(text)}


def extract_wallets(text: str) -> set[str]:
    return {normalize_wallet(match) for match in WALLET_RE.findall(text)}


def extract_bank_accounts(text: str) -> set[str]:
    return {normalize_bank_account(match) for match in BANK_RE.findall(text)}


def extract_addresses(text: str) -> set[str]:
    return {match.strip() for match in ADDRESS_RE.findall(text)}


def domains_from_urls(urls: set[str]) -> set[str]:
    domains: set[str] = set()
    for url in urls:
        domain = normalize_domain(url)
        if domain and "." in domain:
            domains.add(domain)
    return domains


def media_entity_type_for_mime(mime_type: str) -> str:
    lowered = (mime_type or "").lower()
    if lowered.startswith("image/"):
        return "image"
    if lowered.startswith("video/"):
        return "video"
    if lowered.startswith("audio/"):
        return "audio"
    if lowered in {"application/pdf"} or "document" in lowered or "text/" in lowered:
        return "document"
    return "document"


__all__ = [
    "domains_from_urls",
    "extract_addresses",
    "extract_bank_accounts",
    "extract_emails",
    "extract_identifiers",
    "extract_ips",
    "extract_phones",
    "extract_urls",
    "extract_wallets",
    "media_entity_type_for_mime",
    "normalize_bank_account",
    "normalize_domain",
    "normalize_email",
    "normalize_generic",
    "normalize_hash",
    "normalize_ip",
    "normalize_location",
    "normalize_phone",
    "normalize_wallet",
    "normalize_website",
]
