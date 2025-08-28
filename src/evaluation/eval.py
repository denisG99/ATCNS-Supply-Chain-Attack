from src.detector import Detector

if __name__ =="__main__":
    detector = Detector("./sample.py", "eval")

    detector.shadowing_detection()