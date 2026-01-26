# configurator/core/dependencies.py

"""
Defines the complete dependency graph for all 20 modules.
This acts as the source of truth for execution order.
"""

from typing import Dict, List

import networkx as nx

COMPLETE_MODULE_DEPENDENCIES: Dict[str, List[str]] = {
    # Phase 1: System base (no dependencies)
    "system": [],
    # Phase 2: Security (requires system)
    "security": ["system"],
    # Phase 3: User management (requires system + security)
    "rbac": ["system", "security"],
    # Phase 4: Desktop (requires system + security for firewall)
    "desktop": ["system", "security"],
    # Phase 5: Languages (all require system only, can be parallel)
    "python": ["system"],
    "nodejs": ["system"],
    "golang": ["system"],
    "rust": ["system"],
    "java": ["system"],
    "php": ["system"],
    # Phase 6: Tools
    "docker": ["system", "security"],  # Needs firewall rules
    "git": ["system"],
    "databases": ["system"],  # Just client tools, no server
    "devops": ["system", "docker"],  # kubectl concepts need docker
    "utilities": ["system"],
    # Phase 7: Editors (all independent, can be parallel)
    "vscode": ["system"],
    "cursor": ["system"],
    "neovim": ["system"],
    # Phase 8: Networking (require security for firewall)
    "wireguard": ["system", "security"],
    "caddy": ["system", "security"],
    # Phase 9: Monitoring (last, can monitor docker if present)
    "netdata": ["system"],
}


def validate_dependencies() -> bool:
    """Validate dependency graph has no cycles."""
    graph = nx.DiGraph()
    for module, deps in COMPLETE_MODULE_DEPENDENCIES.items():
        graph.add_node(module)
        for dep in deps:
            graph.add_edge(dep, module)

    # Check for cycles
    try:
        cycles = list(nx.simple_cycles(graph))
        if cycles:
            raise ValueError(f"Circular dependencies detected: {cycles}")
    except nx.NetworkXNoCycle:
        pass  # No cycles, good!

    return True
