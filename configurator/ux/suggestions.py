from typing import Any, List


class SuggestionEngine:
    """Provides smart suggestions for modules based on current selection."""

    def suggest_modules(self, current_modules: List[str]) -> List[str]:
        """
        Suggest modules that complement the current selection.

        Args:
            current_modules: List of currently enabled modules.

        Returns:
            List of suggested module names.
        """
        suggestions = []

        # Dev Tools
        if "python" in current_modules or "nodejs" in current_modules:
            if "vscode" not in current_modules:
                suggestions.append("vscode")
            if "git" not in current_modules:
                suggestions.append("git")

        # Docker
        if "docker" in current_modules and "devops" not in current_modules:
            suggestions.append("devops")

        # Desktop
        if "desktop" in current_modules:
            if "cursor" not in current_modules and "vscode" not in current_modules:
                suggestions.append("cursor")

        # Deduplicate and remove already selected
        # Deduplicate and remove already selected
        return [s for s in suggestions if s not in current_modules]

    def suggest_config(self, module_name: str) -> dict[str, Any]:
        """
        Suggest configuration options for a module.
        """
        if module_name == "python":
            return {"install_poetry": True, "versions": ["3.11", "3.12"]}
        if module_name == "docker":
            return {"users": ["$USER"]}
        if module_name == "vscode":
            return {"extensions": ["ms-python.python"]}
        return {}

    def get_popular_combinations(self) -> List[List[str]]:
        return [["python", "vscode", "git"], ["docker", "devops"], ["desktop", "cursor"]]
