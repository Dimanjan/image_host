
from rapidfuzz import fuzz

query = "basketball kala pthar"
target = "Kala Patthar Basketball"
distractor = "Basketball"

score_target = fuzz.token_sort_ratio(query.lower(), target.lower())
score_distractor = fuzz.token_sort_ratio(query.lower(), distractor.lower())

print(f"Query: '{query}'")
print("-" * 40)
print(f"1. Match: '{target}'")
print(f"   Score: {score_target:.2f}")
print(f"   Result: {'FOUND' if score_target >= 50 else 'HIDDEN'}")
print("-" * 40)
print(f"2. Match: '{distractor}'")
print(f"   Score: {score_distractor:.2f}")
print(f"   Result: {'FOUND' if score_distractor >= 50 else 'HIDDEN'}")
