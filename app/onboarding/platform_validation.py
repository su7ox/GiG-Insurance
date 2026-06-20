# Mock platform database — simulates Zepto/Blinkit partner verification
# In production this would call the real platform API

MOCK_WORKERS = {
    "zepto": {
        "ZPT001": {"name": "Rahul Sharma", "phone": "919999999999", "zone": "Noida Sector 18"},
        "ZPT002": {"name": "Amit Kumar", "phone": "918888888888", "zone": "Noida Sector 62"},
    },
    "blinkit": {
        "BLK001": {"name": "Suresh Yadav", "phone": "917777777777", "zone": "Gurgaon Sector 14"},
        "BLK002": {"name": "Vijay Singh", "phone": "916666666666", "zone": "Gurgaon Sector 29"},
    },
}


def validate_partner_id(platform: str, partner_id: str) -> dict | None:
    """
    Validate partner ID against mock platform database.
    Returns worker data if valid, None if not found.
    """
    platform = platform.lower().strip()
    partner_id = partner_id.upper().strip()
    return MOCK_WORKERS.get(platform, {}).get(partner_id, None)


def get_supported_platforms() -> list[str]:
    return list(MOCK_WORKERS.keys())