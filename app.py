from src.estimator import estimator
from src.logging_service import Logger
from flask import Flask, request, Response, jsonify, make_response, g
from flask_restful import Resource, Api
from json import dumps, loads
import datetime
from functools import wraps
import math
from dicttoxml import dicttoxml
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
        return jsonify({"error":"An error occured during the request"}), 400

@app.route('/', methods=['GET'])
def index():
    return "<h3>Welcome to the Home Page</h3>"

'''  The method below will be used to obtain information from a user about covid 19 statistics in their country and returns am estimation of the impact'''
@app.route('/api/v1/on-covid-19', methods=['POST', 'GET'], endpoint='estimator')
@app.route('/api/v1/on-covid-19/json', methods=['POST', 'GET'], endpoint='estimator')
def get_covid_statistics():
      try:

            data = request.get_json()

            # To check if the username and password keys have been sent in the request body

            if data is None:
                return jsonify({'message': 'No data has been submitted'}), 400
            '''
              check and see if any of the data is missing in the submitted request
            '''
            if data['periodType'] not in ['days','weeks','months'] :
                return jsonify({'message': 'Period type chosen is wrong; use days, weeks or months'}), 400


            '''
            We now obtain the data in the submitted and return the estimated covid 19 results
            '''
            return Response(response=dumps(estimator(data)), status=200, content_type='application/json')
            
            
      except Exception as ex:
        the_logger.log_error('Request error: {0} '.format(ex))
        return jsonify({"error":"An error occured during the request"}), 400

'''  The method below will be used to obtain information from a user about covid 19 statistics in their country and returns am estimation of the impact'''
@app.route('/api/v1/on-covid-19/xml', methods=['POST', 'GET'], endpoint='estimator_xml')
def get_covid_statistics_xml():
      try:

            data = request.get_json()

            # To check if the username and password keys have been sent in the request body

            if data is None:
                return jsonify({'message': 'No data has been submitted'}), 400
            '''
              check and see if any of the data is missing in the submitted request
            '''
            if data['periodType'] not in ['days','weeks','months'] :
                return jsonify({'message': 'Period type chosen is wrong; use days, weeks or months'}), 400


            '''
            We now obtain the data in the submitted and return the estimated covid 19 results
            '''
            xml_response = dicttoxml(estimator(data))
            return Response(response=xml_response, status=200, content_type='application/xml')
            
            
      except Exception as ex:
        the_logger.log_error('Request error: {0} '.format(ex))
        return jsonify({"error":"An error occured during the request"}), 400


'''  The method below will be used to obtain the logs'''
@app.route('/api/v1/on-covid-19/logs', methods=['GET', 'POST'], endpoint='logs')
def get_covid_logs():
  try:
    all_logs=""
    logs = Logs.query.all()
    the_logger.log_information('Query list result from logs: {0}'.format(logs))
    for row in logs:
        the_logger.log_information('Query result from logs: {0}'.format(row.log_text))
        
        all_logs += '\n'+row.log_text
    return Response(response=all_logs, status=200, mimetype='text/plain')
  except Exception as ex:
        the_logger.log_error('Request error: {0} '.format(ex))
        return jsonify({"error":"An error occured during the request"}), 400




if __name__ == "__main__":
  try:
    app.run(host='0.0.0.0',debug=True)
  except Exception as ex:
    the_logger.log_error(ex)