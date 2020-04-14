from flask import Flask, request, Response, jsonify, make_response, g
from flask_restful import Resource, Api
from json import dumps, loads
from logging_service import Logger
import datetime
from functools import wraps
import math
from json2xml import json2xml
from json2xml.utils import readfromurl, readfromstring, readfromjson
import time
from flask_sqlalchemy import SQLAlchemy


the_logger = Logger()

app = Flask(__name__)

api = Api(app)

'''
Methods to log the requests to a database
'''

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/covid19_logs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Logs(db.Model):
    '''Logs table'''

    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key = True)
    log_text = db.Column(db.Text(150))

@app.before_first_request
def create_tables():
    db.create_all()



@app.before_request
def start_timer():
    g.start = time.time()

@app.after_request
def log_request(response):
  try:
    if request.path == '/favicon.ico':
        return response
    elif request.path.startswith('/static'):
        return response
    elif 'logs' in request.path:
        return response

    method = request.method
    path = request.path
    status = response.status_code
    now = time.time()
    duration = round(now - g.start, 2)

    the_log_text = '{0}\t\t{1}\t\t{2}\t\t{3}\tms'.format(method,path,status,duration)

    the_logger.log_information('Logger for requests\t\t{0}'.format(the_log_text))

    '''
    Add log text to database
    '''
    new_log = Logs(log_text = the_log_text)

    db.session.add(new_log)
    db.session.commit()

    return response
  except Exception as ex:
        the_logger.log_error('Logging the info Request error: {0} '.format(ex))
        return jsonify({"error":"An error occured during the request"})

'''  The method below will be used to obtain information from a user about covid 19 statistics in their country and returns am estimation of the impact'''
@app.route('/api/v1/on-covid-19', methods=['POST'])
def get_covid_statistics():
      try:

            data = request.get_json()

            # To check if the username and password keys have been sent in the request body

            if data is None:
                return jsonify({'message': 'No data has been submitted'})
            '''
              check and see if any of the data is missing in the submitted request
            '''
            if data['periodType'] not in ['days','weeks','months'] :
                return jsonify({'message': 'Period type chosen is wrong; use days, weeks or months'})


            '''
            We now obtain the data in the submitted and return the estimated covid 19 results
            '''
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
            the_logger.log_information(impact.get_json())

            severe_impact = jsonify({'currentlyInfected':severe_impact_currently_infected,'infectionsByRequestedTime':severe_impact_infections_by_requested_time,'severeCasesByRequestedTime':severe_impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':severe_impact_available_beds, 'casesForICUByRequestedTime':severe_impact_need_ICU, 'casesForVentilatorsByRequestedTime':severe_impact_need_ventilators, 'dollarsInFlight':severe_impact_impact_lost_daily})
            the_logger.log_information(severe_impact.get_json())


            return jsonify({'data': data, 'impact':impact.get_json(), 'severeImpact':severe_impact.get_json()}), 200
      except Exception as ex:
        the_logger.log_error('Request error: {0} '.format(ex))
        return jsonify({"error":"An error occured during the request"})

'''  The method below will be used to obtain information from a user about covid 19 statistics in their country and returns am estimation of the impact'''
@app.route('/api/v1/on-covid-19/json', methods=['POST'])
def get_covid_statistics_json():
      try:
            data = request.get_json()

            # To check if the username and password keys have been sent in the request body

            if data is None:
                return jsonify({'message': 'No data has been submitted'})
            '''
              check and see if any of the data is missing in the submitted request
            '''
            if data['periodType'] not in ['days','weeks','months'] :
                return jsonify({'message': 'Period type chosen is wrong; use days, weeks or months'})


            '''
            We now obtain the data in the submitted and return the estimated covid 19 results
            '''
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
            the_logger.log_information(impact.get_json())

            severe_impact = jsonify({'currentlyInfected':severe_impact_currently_infected,'infectionsByRequestedTime':severe_impact_infections_by_requested_time,'severeCasesByRequestedTime':severe_impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':severe_impact_available_beds, 'casesForICUByRequestedTime':severe_impact_need_ICU, 'casesForVentilatorsByRequestedTime':severe_impact_need_ventilators, 'dollarsInFlight':severe_impact_impact_lost_daily})
            the_logger.log_information(severe_impact.get_json())


            return jsonify({'data': data, 'impact':impact.get_json(), 'severeImpact':severe_impact.get_json()}), 200
      except Exception as ex:
        the_logger.log_error('Request error: {0} '.format(ex))
        return jsonify({"error":"An error occured during the request"})


'''  The method below will be used to obtain information from a user about covid 19 statistics in their country and returns am estimation of the impact'''
@app.route('/api/v1/on-covid-19/xml', methods=['POST'])
def get_covid_statistics_xml():
      try:
            data = request.get_json()

            # To check if the username and password keys have been sent in the request body

            if data is None:
                return jsonify({'message': 'No data has been submitted'})
            '''
              check and see if any of the data is missing in the submitted request
            '''
            if data['periodType'] not in ['days','weeks','months'] :
                return jsonify({'message': 'Period type chosen is wrong; use days, weeks or months'})


            '''
            We now obtain the data in the submitted and return the estimated covid 19 results
            '''
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
            the_logger.log_information(impact.get_json())

            severe_impact = jsonify({'currentlyInfected':severe_impact_currently_infected,'infectionsByRequestedTime':severe_impact_infections_by_requested_time,'severeCasesByRequestedTime':severe_impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':severe_impact_available_beds, 'casesForICUByRequestedTime':severe_impact_need_ICU, 'casesForVentilatorsByRequestedTime':severe_impact_need_ventilators, 'dollarsInFlight':severe_impact_impact_lost_daily})
            the_logger.log_information(severe_impact.get_json())


            json_data = {"data": data, "impact":impact.get_json(), "severeImpact":severe_impact.get_json()}

            the_logger.log_information('json data to be converted to xml: {0}'.format(json_data))

            json_string = '''{0}'''.format(json_data)
            the_logger.log_information('json string: {0}'.format(json_string))
            value = loads(json_string.replace("'", "\""))
            the_logger.log_information('json loads: {0}'.format(value))
            json_dump = dumps(value)
            the_logger.log_information('json dumps: {0}'.format(json_dump))

            xml_data = convert_json_to_xml(json_dump)

            the_logger.log_information('xml_data_request: {0}'.format(xml_data))

            return xml_data, 200 ,{'Content-Type': 'application/xml'}
      except Exception as ex:
        the_logger.log_error('Request error: {0} '.format(ex))
        return jsonify({"error":"An error occured during the request"})


'''  The method below will be used to obtain the logs'''
@app.route('/api/v1/on-covid-19/logs', methods=['GET'])
def get_covid_logs():
  try:
    all_logs=""
    logs = Logs.query.all()
    the_logger.log_information('Query list result from logs: {0}'.format(logs))
    for row in logs:
        the_logger.log_information('Query result from logs: {0}'.format(row.log_text))
        
        all_logs += '\n'+row.log_text
    return all_logs
  except Exception as ex:
        the_logger.log_error('Request error: {0} '.format(ex))
        return jsonify({"error":"An error occured during the request"})





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

def convert_json_to_xml(json_data):
  # get the xml from a json string
  the_logger.log_information('Starting Json to XML method.......')
  try:
    
    data = readfromstring(json_data)
    the_logger.log_information('string_data_method: {0}'.format(data))
    xml_data = json2xml.Json2xml(data,wrapper="covid19", pretty=True).to_xml()
    the_logger.log_information('xml_data_method: {0}'.format(xml_data))
    return xml_data
  except Exception as ex:
    the_logger.log_error('json_to_xml error: {0}'.format(ex))
    return None


def estimator(input_data):
    try:
                data = loads(input_data)

                #print(data)

                # To check if the username and password keys have been sent in the request body

                if data is None:
                    return dumps({'message': 'No data has been submitted'})
                '''
                  check and see if any of the data is missing in the submitted request
                '''
                if data['periodType'] not in ['days','weeks','months'] :
                    return dumps({'message': 'Period type chosen is wrong; use days, weeks or months'})


                '''
                We now obtain the data in the submitted and return the estimated covid 19 results
                '''
                '''
                Challenge 1, Determine the currently Infected using the reported cases
                '''

                impact_currently_infected, severe_impact_currently_infected = currently_infected(data['reportedCases'])
                print('impact_currently_infected: {0}'.format(impact_currently_infected))
                print('severe_impact_currently_infected: {0}'.format(severe_impact_currently_infected))

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
                impact = dumps({'currentlyInfected':impact_currently_infected,'infectionsByRequestedTime':impact_infections_by_requested_time,'severeCasesByRequestedTime':impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':impact_available_beds, 'casesForICUByRequestedTime':impact_need_ICU, 'casesForVentilatorsByRequestedTime':impact_need_ventilators, 'dollarsInFlight':impact_impact_lost_daily})
                print(impact)

                severe_impact = dumps({'currentlyInfected':severe_impact_currently_infected,'infectionsByRequestedTime':severe_impact_infections_by_requested_time,'severeCasesByRequestedTime':severe_impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':severe_impact_available_beds, 'casesForICUByRequestedTime':severe_impact_need_ICU, 'casesForVentilatorsByRequestedTime':severe_impact_need_ventilators, 'dollarsInFlight':severe_impact_impact_lost_daily})
                print(severe_impact)


                '''
                Create json objects for both the results of impact and severe impact
                '''
                impact = dumps({'currentlyInfected':impact_currently_infected,'infectionsByRequestedTime':impact_infections_by_requested_time,'severeCasesByRequestedTime':impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':impact_available_beds, 'casesForICUByRequestedTime':impact_need_ICU, 'casesForVentilatorsByRequestedTime':impact_need_ventilators, 'dollarsInFlight':impact_impact_lost_daily})
                print(impact)

                severe_impact = dumps({'currentlyInfected':severe_impact_currently_infected,'infectionsByRequestedTime':severe_impact_infections_by_requested_time,'severeCasesByRequestedTime':severe_impact_severe_cases_require_hospilisation, 'hospitalBedsByRequestedTime':severe_impact_available_beds, 'casesForICUByRequestedTime':severe_impact_need_ICU, 'casesForVentilatorsByRequestedTime':severe_impact_need_ventilators, 'dollarsInFlight':severe_impact_impact_lost_daily})
                print(severe_impact)


                output = dumps({'data': data, 'impact':impact, 'severeImpact':severe_impact})
                return output

                
    except Exception as ex:
      print('Request error: {0} '.format(ex))
      return dumps({"error":"An error occured during the request"})