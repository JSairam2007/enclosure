from debounce import Debouncer

sequence = ["SEALED", "SEALED", "SEALED", "OPEN", "SEALED",
            "OPEN", "OPEN", "OPEN", "OPEN"]
gate = Debouncer(required=3)
print("Input       Stable output   Trigger")
for item in sequence:
    stable, changed = gate.update(item)
    print(f"{item:<11} {stable:<15} {changed}")
