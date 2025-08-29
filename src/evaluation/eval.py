from src.detector import Detector

if __name__ =="__main__":
    detector = Detector("./sample_class.py", "class-eval")

    detector.shadowing_detection()