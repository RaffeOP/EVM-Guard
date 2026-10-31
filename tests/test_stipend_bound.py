"""Stipend-only calls are excluded from SWC-107 only when their gas bound is at most 2300."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from evm_dataflow import AbstractValue, _binary_bound, derive, value_bound  # noqa: E402
from hazard_rules import _is_stipend_only  # noqa: E402

STIPEND = 2300
ONE_BOOLEAN = AbstractValue(upper=1)


class StipendBoundTest(unittest.TestCase):
    def test_constant_stipend_gas_is_stipend_only(self):
        self.assertTrue(_is_stipend_only({"gas": AbstractValue(const=STIPEND)}))

    def test_constant_full_gas_is_not_stipend_only(self):
        self.assertFalse(_is_stipend_only({"gas": AbstractValue(const=STIPEND + 1)}))

    def test_unknown_gas_is_not_stipend_only(self):
        self.assertFalse(_is_stipend_only({"gas": AbstractValue()}))

    def test_product_of_stipend_and_boolean_is_stipend_only(self):
        gas = _binary_bound("MUL", AbstractValue(const=STIPEND), ONE_BOOLEAN)
        self.assertTrue(_is_stipend_only({"gas": AbstractValue(upper=gas)}))

    def test_product_with_unbounded_factor_is_not_stipend_only(self):
        self.assertIsNone(_binary_bound("MUL", AbstractValue(const=STIPEND), AbstractValue()))

    def test_and_takes_smaller_known_bound(self):
        self.assertEqual(_binary_bound("AND", AbstractValue(const=5000), AbstractValue()), 5000)

    def test_derive_keeps_bound_and_value_bound_prefers_constant(self):
        value = derive([AbstractValue()], upper=7)
        self.assertEqual(value_bound(value), 7)
        self.assertEqual(value_bound(AbstractValue(const=3, upper=9)), 3)


if __name__ == "__main__":
    unittest.main()
