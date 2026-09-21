import yara
import os

from classes import scope_graph
from classes.heuristics import ASTHeuristics
from classes.scope_graphv2 import ScopeGraph
from classes.result import Result

class HeuristicEngine:
    """
    HeuristicEngine is a hybrid analysis engine that combines YARA-based rules and AST-based
    heuristics for scanning and analyzing code files.

    This class is designed to facilitate custom heuristic-based code scanning by integrating YARA
    rules with abstract syntax tree (AST) and scope graph analysis. It initializes a heuristic
    engine from provided YARA rule files and generates results based on matches found either through
    AST-based analysis or YARA rules.

    Attributes:
        __rules (list):
            A private list of compiled YARA rule objects used for code analysis.
        __code_path (str):
            A private string representing the file path to the source code to be analyzed.
        __ast_heuristics (ASTHeuristics):
            A private instance of the ASTHeuristics class, used for AST and scope-graph-based analysis.
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

    @staticmethod
    def __filter_FP(arr: list[Result]) -> list[Result]:
        """
        filtering results removing FP:
            * patch_decorator_import & patch_decorator_import;
            * contextmanager_import & contextmanager_usage & with_statement;
            * only with_statement

        Parameters:
            :param arr (list):
                list of results

        Returns:
            :return (list):
                a filtered list of results
        """
        name_aux = [elem.get_name() for elem in arr]

        if "patch_decorator_import" not in name_aux or "patch_decorator_usage" not in name_aux:
            arr = [elem for elem in arr if elem.get_name() != "patch_decorator_import" and elem.get_name() != "patch_decorator_usage"]

        if "contextmanager_import" not in name_aux or "contextmanager_usage" not in name_aux:
            arr = [elem for elem in arr if elem.get_name() != "contextmanager_import" and elem.get_name() != "contextmanager_usage"]

        return arr

    def rule_apply(self) -> list[Result]:
        results: list[Result] = self.__ast_heuristics.get_results()

        # YARA rule application
        for rule in self.__rules:
            for match in rule.match(self.__code_path):
                results.append(Result(name=match.rule, lines=self.__get_yara_matching_line(match)))

        return self.__filter_FP(results)

if __name__ == "__main__":
    from classes.scope_graphv2 import ScopeGraph
    import ast

    tree = ast.parse(open("../../PoC/PoC_with.py").read())

    scope_graph = ScopeGraph()
    engine = HeuristicEngine("../../PoC/PoC_with.py", scope_graph)

    print(engine.rule_apply())
