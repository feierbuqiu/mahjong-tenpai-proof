import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "work", "strategy")); sys.path.insert(0, os.path.join(ROOT, "work", "strategy", "out"))
exec(open(os.path.join(HERE, "verify_l6.py"), encoding="utf-8").read().split('if __name__ == "__main__"')[0])
init(None)
r = batch_worker((0, 2000))
print("first2000", r)
