from src.detector import Detector

import os

if __name__ =="__main__":
    print(os.getcwd())
    detector = Detector("./evaluation/sample_class.py", "class-eval", True)

    shadowing, yara = detector.shadowing_detection()
    print(f"Shadowings: {shadowing}\nYara rules: {yara}")