#!/usr/bin/python3
import requests
import asyncio
from functools import reduce

FIELDS = {
  "ch-1": ["currentlyInfected", "infectionsByRequestedTime"],
  "ch-2": ["severeCasesByRequestedTime", "hospitalBedsByRequestedTime"],
  "ch-3": ["casesForICUByRequestedTime", "casesForVentilatorsByRequestedTime", 'dollarsInFlight']
}

def impact_data_structure_callback(acc, field):
  assert ((type(acc["impact"][field]) == type(1)) or (type(acc["impact"][field]) == type(999999.9999)))
  assert ((type(acc["severeImpact"][field]) == type(1)) or (type(acc["severeImpact"][field]) == type(999999.9999)))
  return acc

def get_impact_data_structure(challenge):
  initial_value = { "impact": {}, "severeImpact": {}}
  return reduce(impact_data_structure_callback, FIELDS[challenge], initial_value)

def value_on_fields_callback(estimated, produced):
  def callback(table, f):
    table.append([estimated["impact"][f], produced["impact"][f]])
    table.append([estimated["severeImpact"][f], produced["severeImpact"][f]])
    return table 
  return callback

def value_on_fields(estimated, produced, challenge):
  return reduce(value_on_fields_callback(estimated, produced), FIELDS[challenge], [])

def get_response(response):
  return response.url

async def mock_estimation_for(period_type):
  API_BASE = "https://us-central1-buildforsdg.cloudfunctions.net/api"
  END_POINT = "{}/gen/covid-19-scenario/{}".format(API_BASE, period_type.lower())
  loop = asyncio.get_event_loop()
  future1 = loop.run_in_executor(None, requests.get, END_POINT)
  response1 = await future1
  return response1.json()

def format_float(f):
  # 4.2930563447909253e+18 == 4293056344790925300 produces False
  # therefore always typecase all to float to solve issue 
  # eg. float(4.2930563447909253e+18) == float(4293056344790925300) produces True
  return float(f)
