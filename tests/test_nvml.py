import unittest

from llm_power_profiler.nvml import parse_gpu_indices


class NVMLTest(unittest.TestCase):
    def test_parse_gpu_indices_defaults_to_all(self) -> None:
        self.assertIsNone(parse_gpu_indices(None))
        self.assertIsNone(parse_gpu_indices(""))
        self.assertIsNone(parse_gpu_indices("all"))

    def test_parse_gpu_indices_list(self) -> None:
        self.assertEqual(parse_gpu_indices("0,1, 3"), [0, 1, 3])

    def test_invalid_gpu_index_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_gpu_indices("0,h100")


if __name__ == "__main__":
    unittest.main()
