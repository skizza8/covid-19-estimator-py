from json import dumps, loads
import math 
from src.logging_service import Logger
from flask.json import jsonify

the_logger = Logger()

def estimator(data):
    
    '''
    Challenge 1, Determine the currently Infected using the reported cases
    '''

    impact_currently_infected, severe_impact_currently_infected = currently_infected(data['reportedCases'])
    the_logger.log_information('impact_currently_infected: {0}'.format(impact_currently_infected))
    the_logger.log_information('severe_impact_currently_infected: {0}'.format(severe_impact_currently_infected))

    '''
    Challenge 1, Determine the probable infections over a period of time. This is obtained using the current infections
    '''

    impact_infections_by_requested_time = infections_by_requested_time(impact_currently_infected,data['periodType'],data['timeToElapse'])
    severe_impact_infections_by_requested_time = infections_by_requested_time(severe_impact_currently_infected,data['periodType'],data['timeToElapse'])

    '''
    Challenge 2, Determine severe cases that may require hospilisation.
    '''
    impact_severe_cases_require_hospilisation = severe_cases_require_hospitalisation(impact_infections_by_requested_time)
    severe_impact_severe_cases_require_hospilisation = severe_cases_require_hospitalisation(severe_impact_infections_by_requested_time)

    '''
    Challenge 2, Determine the hospital beds that will be available to covid 19 patients
    '''

    impact_available_beds = hospital_beds_avaialble_for_covid_patients(data['totalHospitalBeds'], impact_severe_cases_require_hospilisation)
    severe_impact_available_beds = hospital_beds_avaialble_for_covid_patients(data['totalHospitalBeds'], severe_impact_severe_cases_require_hospilisation)

    '''
    Challenge 3, Determine the number of patients that would require ICU
    '''

    impact_need_ICU = severe_cases_require_ICU(impact_severe_cases_require_hospilisation)
    severe_impact_need_ICU = severe_cases_require_ICU(severe_impact_severe_cases_require_hospilisation)

    '''
    Challenge 3, Determine the number of patients that would require ventilators
    '''

    impact_need_ventilators = severe_cases_require_ventilation(impact_severe_cases_require_hospilisation)
    severe_impact_need_ventilators = severe_cases_require_ventilation(severe_impact_severe_cases_require_hospilisation)

    '''
    Challenge 3, Determine the amount of money lost daily 
    '''

    impact_impact_lost_daily = average_income_lost_per_day_dollars(impact_infections_by_requested_time,data['periodType'],data['timeToElapse'], data['region']['avgDailyIncomeInUSD'], data['region']['avgDailyIncomePopulation'])

    severe_impact_impact_lost_daily = average_income_lost_per_day_dollars(severe_impact_infections_by_requested_time,data['periodType'],data['timeToElapse'], data['region']['avgDailyIncomeInUSD'], data['region']['avgDailyIncomePopulation'])


    '''
    Create json objects for both the results of impact and severe impact
    '''
    impact = jsonify({'currentlyInfected':impact_currently_infected,'infectionsByRequestedTime':impact_infections_by_requested_time,'severeCasesByRequestedTime':impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':impact_available_beds, 'casesForICUByRequestedTime':impact_need_ICU, 'casesForVentilatorsByRequestedTime':impact_need_ventilators, 'dollarsInFlight':impact_impact_lost_daily})
    the_logger.log_information(impact)

    severe_impact = jsonify({'currentlyInfected':severe_impact_currently_infected,'infectionsByRequestedTime':severe_impact_infections_by_requested_time,'severeCasesByRequestedTime':severe_impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':severe_impact_available_beds, 'casesForICUByRequestedTime':severe_impact_need_ICU, 'casesForVentilatorsByRequestedTime':severe_impact_need_ventilators, 'dollarsInFlight':severe_impact_impact_lost_daily})
    the_logger.log_information(severe_impact)


    '''
    Create json objects for both the results of impact and severe impact
    '''
    impact = jsonify({'currentlyInfected':impact_currently_infected,'infectionsByRequestedTime':impact_infections_by_requested_time,'severeCasesByRequestedTime':impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':impact_available_beds, 'casesForICUByRequestedTime':impact_need_ICU, 'casesForVentilatorsByRequestedTime':impact_need_ventilators, 'dollarsInFlight':impact_impact_lost_daily})
    the_logger.log_information(impact)

    severe_impact = jsonify({'currentlyInfected':severe_impact_currently_infected,'infectionsByRequestedTime':severe_impact_infections_by_requested_time,'severeCasesByRequestedTime':severe_impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':severe_impact_available_beds, 'casesForICUByRequestedTime':severe_impact_need_ICU, 'casesForVentilatorsByRequestedTime':severe_impact_need_ventilators, 'dollarsInFlight':severe_impact_impact_lost_daily})
    the_logger.log_information(severe_impact)


    output = {"data": data, "impact":impact.get_json(), "severeImpact":severe_impact.get_json()}
    return output

def currently_infected(reportedCases):
  impact_currently_infected = reportedCases * 10
  severe_impact_currently_infected = reportedCases * 50
  return impact_currently_infected, severe_impact_currently_infected

def infections_by_requested_time(currently_infected,periodType,timeToElapse):

  if periodType =='weeks':
    num_of_days = timeToElapse * 7
  elif periodType =='months':
    num_of_days = timeToElapse * 30
  else:
    num_of_days = timeToElapse
    
  
  return math.trunc(currently_infected * 2 ** (num_of_days/3))

def severe_cases_require_hospitalisation(infections_by_requested_time):
  return math.trunc((15/100)* infections_by_requested_time)

def hospital_beds_avaialble_for_covid_patients(hospital_beds, severe_cases_requiring_hospitalisation):
    available_beds = math.trunc((35/100) * hospital_beds)
    hospital_beds_for_covid_patients = available_beds - severe_cases_requiring_hospitalisation
    return hospital_beds_for_covid_patients

def severe_cases_require_ICU(infections_by_requested_time):
  return math.trunc((5/100)* infections_by_requested_time)

def severe_cases_require_ventilation(infections_by_requested_time):
  return math.trunc((2/100)* infections_by_requested_time)


def average_income_lost_per_day_dollars(infections_by_requested_time,periodType,timeToElapse, average_income_per_day, average_income_population_per_day):

  if periodType =='weeks':
    num_of_days = timeToElapse * 7
  elif periodType =='months':
    num_of_days = timeToElapse * 30
  else:
    num_of_days = timeToElapse
  
  income_lost_per_day = (infections_by_requested_time * average_income_per_day * average_income_population_per_day)/num_of_days
  return math.trunc(income_lost_per_day)
