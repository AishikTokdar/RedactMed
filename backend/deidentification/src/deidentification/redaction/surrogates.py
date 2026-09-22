"""Synthetic surrogate generation for clinical text de-identification."""

from __future__ import annotations

import hashlib

SURROGATE_NAMES = [
    "Amit Verma", "Sunita Rao", "Dr. Arvind Patel", "Dr. Shalini Iyer",
    "John Miller", "Emily Watson", "Dr. Robert Chen", "Dr. Sarah Jenkins",
    "Pooja Deshmukh", "Vikram Malhotra", "Dr. Meera Nambiar", "David Brooks",
    "Kavita Reddy", "Sanjay Singhania", "Dr. Neha Kulkarni", "Michael Chang",
]

SURROGATE_LOCATIONS = [
    "Oakridge Medical Center, Chicago, IL",
    "Green Valley Clinic, Austin, TX",
    "City Care Hospital, Banjara Hills, Hyderabad",
    "Apex Specialty Clinic, Indiranagar, Bengaluru",
    "St. Jude Community Hospital, Seattle, WA",
    "Sunrise Healthcare Pavilion, Pune, Maharashtra",
]

SURROGATE_ADDRESSES = [
    "742 Evergreen Terrace, Springfield, OR 97477",
    "Flat 301, Palm Grove Apts, Road 10, Jubilee Hills, Hyderabad 500033",
    "124 Conch Street, Austin, TX 78701",
    "House 14B, Shanti Niketan, Viman Nagar, Pune 411014",
    "500 Pine Street, Suite 400, Seattle, WA 98101",
]

SURROGATE_ORGANIZATIONS = [
    "Memorial Health System",
    "Sunrise General Hospital",
    "Apex Clinical Laboratories",
    "Metropolitan Heart Institute",
    "CareFirst Medical Foundation",
]

SURROGATE_DOMAINS = [
    "healthmemorial.org",
    "sunrisecare.org",
    "apexclinics.net",
    "metrohealth.org",
]

SURROGATE_PHONES = [
    "+1 (555) 234-5678",
    "+1 (555) 876-5432",
    "+91 98201 12345",
    "+91 94440 67890",
]


class SurrogateFormatter:
    """Replaces PHI with realistic synthetic counterparts preserving text fluency."""

    def __init__(self, salt: str = "redactmed-surrogate-salt") -> None:
        self.salt = salt
        self._cache: dict[tuple[str, str], str] = {}

    def _hash_index(self, category: str, value: str, pool_size: int) -> int:
        digest = hashlib.sha256(f"{self.salt}:{category}:{value}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % pool_size

    def get_tag(self, pii_type: str, value: str) -> str:
        cache_key = (pii_type.lower(), value.strip().lower())
        if cache_key in self._cache:
            return self._cache[cache_key]

        ptype = pii_type.lower()
        if ptype in ("person_name", "nam"):
            idx = self._hash_index("name", value, len(SURROGATE_NAMES))
            surrogate = SURROGATE_NAMES[idx]
            if value.lower().startswith("dr.") and not surrogate.lower().startswith("dr."):
                surrogate = f"Dr. {surrogate}"
        elif ptype in ("address", "adr"):
            idx = self._hash_index("address", value, len(SURROGATE_ADDRESSES))
            surrogate = SURROGATE_ADDRESSES[idx]
        elif ptype in ("phone_number", "phn", "fax_number", "fax"):
            idx = self._hash_index("phone", value, len(SURROGATE_PHONES))
            surrogate = SURROGATE_PHONES[idx]
        elif ptype in ("email", "eml"):
            idx_domain = self._hash_index("domain", value, len(SURROGATE_DOMAINS))
            user_part = hashlib.sha256(f"{self.salt}:{value}".encode("utf-8")).hexdigest()[:8]
            surrogate = f"user.{user_part}@{SURROGATE_DOMAINS[idx_domain]}"
        elif ptype in ("medical_record_number", "mrn", "account_number", "acc"):
            int_seed = int(hashlib.sha256(f"{self.salt}:{value}".encode("utf-8")).hexdigest()[:6], 16)
            surrogate = f"MRN-{int_seed:06d}"
        elif ptype in ("aadhaar_number", "adh"):
            int_seed = int(hashlib.sha256(f"{self.salt}:{value}".encode("utf-8")).hexdigest()[:12], 16) % 1000000000000
            s = f"{int_seed:012d}"
            surrogate = f"{s[:4]}-{s[4:8]}-{s[8:12]}"
        elif ptype in ("pan_number", "pan"):
            d = hashlib.sha256(f"{self.salt}:{value}".encode("utf-8")).hexdigest().upper()
            surrogate = f"ABCDE{d[:4]}F"
        elif ptype in ("abha_id", "abh"):
            int_seed = int(hashlib.sha256(f"{self.salt}:{value}".encode("utf-8")).hexdigest()[:14], 16) % 100000000000000
            s = f"{int_seed:014d}"
            surrogate = f"{s[:2]}-{s[2:6]}-{s[6:10]}-{s[10:14]}"
        elif ptype in ("national_id", "nid"):
            int_seed = int(hashlib.sha256(f"{self.salt}:{value}".encode("utf-8")).hexdigest()[:10], 16) % 10000000000
            s = f"{int_seed:010d}"
            surrogate = f"{s[:3]} {s[3:6]} {s[6:10]}"
        elif ptype in ("url", "ip_address", "ip"):
            surrogate = "https://internal.clinical-portal.org/records"
        else:
            surrogate = f"[{pii_type.upper()}]"

        self._cache[cache_key] = surrogate
        return surrogate

    def reset(self) -> None:
        self._cache.clear()
