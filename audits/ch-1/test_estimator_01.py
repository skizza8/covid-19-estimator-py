#!/usr/bin/python3
import asyncio

from src.estimator import estimator
import audits.test_utils as test_utils

cases = [
    ["days", "ch-1"],
    ["weeks", "ch-1"],
    ["months", "ch-1"]
]


def test_challenge1():
  for [period_type, challenge] in cases:
    loop = asyncio.get_event_loop()
    input = loop.run_until_complete(
        test_utils.mock_estimation_for(period_type))

    # nodes from end point
    data = input["data"]
    estimate = input["estimate"]

    output = estimator(data)
    values = test_utils.value_on_fields(output, estimate, challenge)
    for [produced, expected] in values:
      assert test_utils.format_float(produced) == \
          test_utils.format_float(expected)
