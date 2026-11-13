"""Consecutive-frame debounce for carton inspection classes."""
class Debouncer:
    def __init__(self, required=3):
        if required < 1:
            raise ValueError("required must be >= 1")
        self.required = required
        self.candidate = None
        self.count = 0
        self.stable = "WAITING"

    def update(self, value):
        if value not in ("SEALED", "OPEN"):
            self.candidate, self.count = None, 0
            return self.stable, False
        if value == self.candidate:
            self.count += 1
        else:
            self.candidate, self.count = value, 1
        if self.count >= self.required and self.stable != value:
            self.stable = value
            return self.stable, True
        return self.stable, False
