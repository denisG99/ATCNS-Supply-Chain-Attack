import yara
import os

from classes import result, scope_graph
from classes.heuristics import ASTHeuristics
from classes.scope_graphv2 import ScopeGraph
from classes.result import Result

class HeuristicEngine:
    """
    YARA engine + custom heuristic engine based on AST and scope graph
    """
    def __yara_engine_init(self, heuristic_path: str="./heuristics") -> None:
        for file in os.listdir(heuristic_path):
            self.__rules.append(yara.compile(f"{heuristic_path}/{file}"))

    def __init__(self, code_path: str, scope_graph:ScopeGraph, heuristic_path: str="./heuristics") -> None:
        self.__rules: list = []
        self.__code_path = code_path

        self.__yara_engine_init(heuristic_path)
        # Custom heuristic engine initialization (AST and scope-graph based)
        self.__ast_heuristics = ASTHeuristics(self.__code_path, scope_graph)

    def __get_yara_matching_line(self, match) -> list[int]:
        """
        Extracts and returns the line numbers in the file where the provided YARA match patterns occur.

        This method processes the code present in the file at the specified path and calculates
        the line numbers corresponding to the offsets of matched patterns provided by the YARA
        library. It reads the file content, determines the offset of each matching instance,
        and translates the offset into line numbers by counting newline characters.

        Parameters:
            :param match (Match object):
                A YARA Match object that contains information about matched patterns, including their string instance offsets.

        :returns: list[int]:
            A list of integers representing the line numbers in the file where the matched patterns occur.
        """
        with open(self.__code_path) as f:
            code = f.read()

        lines = []

        for string in match.strings:
            for instance in string.instances:
                offset = instance.offset

                lines.append(code[:offset].count('\n') + 1)
        return lines

    def rule_apply(self) -> list[Result]:
        results: list[Result] = self.__ast_heuristics.get_results()

        # YARA rule application
        for rule in self.__rules:
            for match in rule.match(self.__code_path):
                results.append(Result(name=match.rule, lines=self.__get_yara_matching_line(match)))

        return results

if __name__ == "__main__":
    import ast

    tree = ast.parse(open("../../yara/samples/sample_class.py").read())

    scope_graph = ScopeGraph()
    scope_graph.visit(tree)

    heuristic_engine = HeuristicEngine("../../yara/samples/sample_class.py",scope_graph)

    print(heuristic_engine.rule_apply())