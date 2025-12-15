from src.detector import Detector

if __name__ =="__main__":
    detector = Detector("./sample.py", "class-eval")

    print(f"Shadowings: {detector.shadowing_detection()}")