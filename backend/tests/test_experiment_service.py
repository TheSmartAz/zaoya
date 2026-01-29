import unittest
from uuid import uuid4

from app.services.experiment_service import ExperimentService
from app.models.db.experiment import ExperimentVariant


class ExperimentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ExperimentService(db=None)
        self.experiment_id = uuid4()
        self.variants = [
            ExperimentVariant(
                id=uuid4(),
                experiment_id=self.experiment_id,
                name="Control",
                is_control=True,
            ),
            ExperimentVariant(
                id=uuid4(),
                experiment_id=self.experiment_id,
                name="Variant A",
                is_control=False,
            ),
        ]

    def test_assign_variant_deterministic(self) -> None:
        traffic_split = [50, 50]
        visitor_id = "visitor_123"
        first = self.service._assign_variant(
            visitor_id=visitor_id,
            experiment_id=self.experiment_id,
            variants=self.variants,
            traffic_split=traffic_split,
        )
        for _ in range(10):
            again = self.service._assign_variant(
                visitor_id=visitor_id,
                experiment_id=self.experiment_id,
                variants=self.variants,
                traffic_split=traffic_split,
            )
            self.assertEqual(first.id, again.id)

    def test_assign_variant_distribution(self) -> None:
        traffic_split = [50, 50]
        counts = {self.variants[0].id: 0, self.variants[1].id: 0}
        for i in range(2000):
            visitor_id = f"visitor_{i}"
            variant = self.service._assign_variant(
                visitor_id=visitor_id,
                experiment_id=self.experiment_id,
                variants=self.variants,
                traffic_split=traffic_split,
            )
            counts[variant.id] += 1

        ratio = counts[self.variants[0].id] / 2000
        self.assertGreater(ratio, 0.45)
        self.assertLess(ratio, 0.55)

    def test_z_test_significant(self) -> None:
        is_significant, p_value = self.service._z_test(
            control_conversions=100,
            control_visitors=1000,
            treatment_conversions=150,
            treatment_visitors=1000,
        )
        self.assertTrue(is_significant)
        self.assertIsNotNone(p_value)
        self.assertLess(p_value, 0.05)

    def test_z_test_not_significant(self) -> None:
        is_significant, p_value = self.service._z_test(
            control_conversions=100,
            control_visitors=1000,
            treatment_conversions=100,
            treatment_visitors=1000,
        )
        self.assertFalse(is_significant)
        self.assertIsNotNone(p_value)
        self.assertGreaterEqual(p_value, 0.05)

    def test_z_test_zero_visitors(self) -> None:
        is_significant, p_value = self.service._z_test(
            control_conversions=0,
            control_visitors=0,
            treatment_conversions=10,
            treatment_visitors=100,
        )
        self.assertFalse(is_significant)
        self.assertIsNone(p_value)


if __name__ == "__main__":
    unittest.main()
