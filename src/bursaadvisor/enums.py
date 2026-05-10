from enum import StrEnum


class Sector(StrEnum):
    BANKING = "Banking"
    PLANTATION = "Plantation"
    REITS = "REITs"
    TECHNOLOGY = "Technology"
    HEALTHCARE = "Healthcare"
    GLOVES = "Gloves"
    UTILITIES = "Utilities"
    CONSUMER = "Consumer"
    PROPERTY = "Property"
    CONSTRUCTION = "Construction"
    UNKNOWN = "Unknown"


class Verdict(StrEnum):
    BUY = "BUY"
    WATCH = "WATCH"
    AVOID = "AVOID"


class RiskTolerance(StrEnum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


# Sectors where short horizon or low savings triggers a BUY → WATCH downgrade.
# If you add a new volatile sector, add it here too.
VOLATILE_SECTORS = {
    Sector.TECHNOLOGY,
    Sector.GLOVES,
    Sector.CONSTRUCTION,
    Sector.PLANTATION,
    Sector.PROPERTY,
}
