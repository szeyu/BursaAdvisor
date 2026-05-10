"""
BursaAdvisor inference engine.

Sector rules are auto-discovered from rules/sectors/*.py — teammates never edit this file.
To add a new sector: drop a file in rules/sectors/ with a class ending in "Rules". Done.
"""
import importlib
import pkgutil
from pathlib import Path
from experta import KnowledgeEngine

from .rules.hard_stops import HardStopRules
from .rules.profile import ProfileRules
from .rules.fundamentals import FundamentalRules
from .rules.suitability import SuitabilityRules
from .rules.technicals import TechnicalRules


def _discover_sector_mixins() -> list[type]:
    pkg_path = Path(__file__).parent / "rules" / "sectors"
    mixins = []
    for mod_info in pkgutil.iter_modules([str(pkg_path)]):
        mod = importlib.import_module(
            f".rules.sectors.{mod_info.name}", package=__package__
        )
        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if (
                isinstance(obj, type)
                and attr_name.endswith("Rules")
                and obj.__module__ == mod.__name__
            ):
                mixins.append(obj)
    return mixins


_sector_mixins = _discover_sector_mixins()

# MRO: hard stops (100) → profile (70) → fundamentals (50) → sectors (20) → suitability (15) → technicals (10/0) → engine
BursaAdvisor = type(
    "BursaAdvisor",
    (HardStopRules, ProfileRules, FundamentalRules, *_sector_mixins, SuitabilityRules, TechnicalRules, KnowledgeEngine),
    {},
)
