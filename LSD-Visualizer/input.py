import json

from itertools import chain
"""
This script is an automatic way to build an input string for the extension based on the result of our detector results
"""
INPUT_FILE = "./sample.json" # CHANGE WITH DESIRED PATH

if __name__ == "__main__":
    input_history = json.load(open(INPUT_FILE))
    output = dict()

    for key in input_history:
        if input_history[key]["shadowing"] == "true":
            lines = []

            lines.extend(result["line"] for result in input_history[key]["shadowing_res"])
            lines.extend(match["line"] for match in input_history[key]["yara"])

            output[key] = list(chain.from_iterable(lines))

    print(output)