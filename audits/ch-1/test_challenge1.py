# test_hello_add.py
from src.estimator import app
from flask import json

def test_add():        
    response = app.test_client().post(
        '/api/v1/on-covid-19',
        data=json.dumps({
        "region": {	
        "name": "Africa",
        "avgAge": 19.7,
        "avgDailyIncomeInUSD": 1,
        "avgDailyIncomePopulation": 0.8
        },
        "periodType": "days",
        "timeToElapse": 3,
        "reportedCases": 674,
        "population": 66622705,
        "totalHospitalBeds": 10000
        }
        ),
        content_type='application/json',
    )

    data = json.loads(response.get_data(as_text=True))

    assert response.status_code == 200
    assert isinstance(data,dict)