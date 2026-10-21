"""Small Mamdani fuzzy controller for ghost aggression."""
class FuzzyController:
    """Maps distance, pellet protection, and remaining lives to aggression 0-100."""

    OUTPUTS = {
        "low": (0, 0, 35, 60),
        "medium": (35, 55, 75),
        "high": (55, 80, 100, 100),
    }

    @staticmethod
    def _left_shoulder(value: float, full_until: float, zero_at: float) -> float:
        if value <= full_until:
            return 1.0
        if value >= zero_at:
            return 0.0
        return (zero_at - value) / (zero_at - full_until)

    @staticmethod
    def _right_shoulder(value: float, zero_until: float, full_at: float) -> float:
        if value <= zero_until:
            return 0.0
        if value >= full_at:
            return 1.0
        return (value - zero_until) / (full_at - zero_until)

    @staticmethod
    def _triangle(value: float, left: float, peak: float, right: float) -> float:
        if value <= left or value >= right:
            return 0.0
        if value == peak:
            return 1.0
        if value < peak:
            return (value - left) / (peak - left)
        return (right - value) / (right - peak)

    @classmethod
    def aggression(
        cls,
        distance_tiles: float,
        protection: float,
        lives: int,
    ) -> float:
        """Return a centroid-defuzzified aggression score from 0 to 100.

        ``protection`` is the remaining power-pellet duration as a fraction
        from 0 (unprotected) to 1 (full duration).
        """
        distance = max(0.0, distance_tiles)
        protection = min(1.0, max(0.0, protection))
        lives = max(0, lives)

        near = cls._left_shoulder(distance, 2.0, 7.0)
        far = cls._right_shoulder(distance, 5.0, 10.0)
        medium_distance = cls._triangle(distance, 2.0, 6.0, 10.0)

        vulnerable = cls._left_shoulder(protection, 0.0, 0.3)
        protected = cls._right_shoulder(protection, 0.2, 0.65)
        expiring = cls._triangle(protection, 0.15, 0.4, 0.7)

        critical = cls._left_shoulder(float(lives), 1.0, 2.5)
        healthy = cls._right_shoulder(float(lives), 2.0, 3.0)
        moderate = cls._triangle(float(lives), 1.0, 2.0, 3.0)

        rules = (
            (min(protected, 1.0), "low"),
            (min(vulnerable, near, critical), "high"),
            (min(vulnerable, near, healthy), "medium"),
            (min(vulnerable, near, moderate), "high"),
            (min(vulnerable, far), "low"),
            (min(vulnerable, medium_distance, critical), "high"),
            (min(vulnerable, medium_distance), "medium"),
            (min(expiring, near), "medium"),
            (min(expiring, medium_distance), "low"),
            (min(vulnerable, near), "high"),
        )

        samples = range(101)
        numerator = 0.0
        denominator = 0.0
        for output in samples:
            membership = 0.0
            for strength, label in rules:
                if strength:
                    membership = max(
                        membership,
                        min(strength, cls._output_membership(float(output), label)),
                    )
            numerator += output * membership
            denominator += membership
        return numerator / denominator if denominator else 0.0

    @classmethod
    def _output_membership(cls, value: float, label: str) -> float:
        points = cls.OUTPUTS[label]
        if label == "medium":
            return cls._triangle(value, *points)
        left, full_left, full_right, right = points
        if value < left or value > right:
            return 0.0
        if full_left <= value <= full_right:
            return 1.0
        if value < full_left:
            return (value - left) / (full_left - left)
        return (right - value) / (right - full_right)
