from auxiliary.malicious_func import function
from auxiliary.benign_func import function

def encode_str():
    def prova():
        from auxiliary.malicious_func import function

        print(f"Incide encode_str: ", end="")
        function()

    prova()

if __name__ =="__main__":
    function()
    encode_str()