import unittest

from llm_power_profiler.usage import parse_openai_usage


class UsageTest(unittest.TestCase):
    def test_parse_openai_usage(self) -> None:
        usage = parse_openai_usage(
            {
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 34,
                    "total_tokens": 46,
                }
            }
        )

        self.assertEqual(
            usage,
            {
                "prompt_tokens": 12,
                "completion_tokens": 34,
                "total_tokens": 46,
            },
        )

    def test_missing_usage_returns_none(self) -> None:
        self.assertIsNone(parse_openai_usage({"choices": []}))

    def test_invalid_token_values_fall_back_to_zero(self) -> None:
        usage = parse_openai_usage(
            {
                "usage": {
                    "prompt_tokens": "7",
                    "completion_tokens": None,
                    "total_tokens": "bad",
                }
            }
        )

        self.assertEqual(
            usage,
            {
                "prompt_tokens": 7,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        )


if __name__ == "__main__":
    unittest.main()
