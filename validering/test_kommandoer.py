import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.Translate import get_dic_for_PSU

psus = ["hmp4040", "k2400", "k2450", "k6500"]

test_file = "kommandoer_fra_simen.json"

"""Compares commands in dict with commands in json file, to make sure they are the same.
This is to make sure that the commands we use in the code are the same as the ones we expect from the json file."""
def test_get_dic_psu():
    for psu in psus:
        dic = get_dic_for_PSU(psu)
        with open(os.path.join(os.path.dirname(__file__), test_file)) as f:
            test_data = json.load(f)
        test_kommandoer = test_data[psu.upper()]
        for key in test_kommandoer:
            test = test_kommandoer[key]
            translate = dic[key].format("")
            assert test == translate, f"Error in {psu} for command {key}: expected '{test}', got '{translate}'"


if __name__ == "__main__":
    test_get_dic_psu()
    print("All tests passed!")