from typing import Dict, List, Set

class ForeignKeyCycleDetector:
    @staticmethod
    def has_cycles(dependency_graph: Dict[str, List[str]]) -> bool:
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in dependency_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for table in dependency_graph:
            if table not in visited:
                if dfs(table):
                    return True
        return False
