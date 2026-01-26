from difflib import SequenceMatcher
from typing import List

from configurator.dependencies.registry import DependencyRegistry


class ModuleSearch:
    """
    Search functionality for modules.
    """

    def __init__(self):
        self.registry = DependencyRegistry()
        # Cache module list?

    def search(self, query: str, limit: int = 10) -> List[dict]:
        """
        Fuzzy search for modules.
        Returns list of module info dicts with score.
        """
        query = query.lower()
        # results = []

        # Get all known modules (from registry or other source if available)
        # For now we use the registry's known dependencies + maybe a hardcoded list of all modules
        # Since we don't have a global "all modules" list easily accessible without scanning,
        # we will assume the registry has most important ones, or we rely on what's passed in.

        # Let's check registry first
        # Ideally this class should be initialized with a list of available modules
        results: List[dict] = []
        return results

    def search_in_list(self, query: str, modules: List[str], limit: int = 10) -> List[str]:
        """
        Identify modules in a list that match the query.
        """
        if not query:
            return modules[:limit]

        matches = []
        for module in modules:
            score = SequenceMatcher(None, query.lower(), module.lower()).ratio()
            if query.lower() in module.lower():
                score += 0.5  # Boost exact substring matches

            if score > 0.3:
                matches.append((score, module))

        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:limit]]

    def search_by_category(self, category: str) -> List[str]:
        # Placeholder
        return []

    def search_by_tag(self, tag: str) -> List[str]:
        # Placeholder
        return []


# Simple Autocomplete as well
class Autocomplete:
    def __init__(self, words: List[str]):
        self.words = words

    def complete(self, text: str) -> List[str]:
        return [w for w in self.words if w.startswith(text)]
