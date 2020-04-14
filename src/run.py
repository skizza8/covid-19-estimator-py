from estimator import app
from logging_service import Logger


the_logger = Logger()

if __name__ == "__main__":
  try:
    app.run(host='0.0.0.0',debug=True)
  except Exception as ex:
    the_logger.log_error(ex)