#import dependencies
import numpy as np
import re
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql import exists  
from flask import Flask, jsonify

#create engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station



app = Flask(__name__)


#define home route
@app.route("/")
def home():
    """List all available api routes."""
    return (
        F"Welcome to Weather API! <br/>"
        f"Here are the available routes:<br/>"
        f"For percipitation data: /api/v1.0/precipitation<br/>"
        f"For Station Info: /api/v1.0/stations<br/>"
        f"For Temperature Observed Info: /api/v1.0/tobs<br/>"
        f"For Specific Date Temperature Info: /api/v1.0/start (enter as YYYY-MM-DD)<br/>"
        f"For a Range of Date Temperature Info: /api/v1.0/start/end (enter as YYYY-MM-DD)"

    )

#show percip data in all stations in descending order
@app.route("/api/v1.0/precipitation") 
def precipitation():
    session = Session(engine)

    # Query Measurement
    results = (session.query(Measurement.date, Measurement.tobs)
                      .order_by(Measurement.date))
    
    # Create a list to store tobs data
    precip_date_tobs = []
    for row in results:
        dt_dict = {}
        dt_dict["date"] = row.date
        dt_dict["tobs"] = row.tobs
        precip_date_tobs.append(dt_dict)

    return jsonify(precip_date_tobs)


#return data for all the stations in the data base
@app.route("/api/v1.0/stations") 
def stations():

    session = Session(engine)
    results = session.query(Station.name).all()

    # Convert to normal list
    station_list = list(np.ravel(results))

    return jsonify(station_list)


#show all temperature observed data ordered by active station
@app.route("/api/v1.0/tobs") 
def tobs():

    session = Session(engine)

    latest_date = (session.query(Measurement.date)
                          .order_by(Measurement.date
                          .desc())
                          .first())
    
    latest_date_str = str(latest_date)
    latest_date_str = re.sub("'|,", "",latest_date_str)
    latest_date_obj = dt.datetime.strptime(latest_date_str, '(%Y-%m-%d)')
    start_date = dt.date(latest_date_obj.year, latest_date_obj.month, latest_date_obj.day) - dt.timedelta(days=365)
     
    # Order by Most active station
    q_station_list = (session.query(Measurement.station, func.count(Measurement.station))
                             .group_by(Measurement.station)
                             .order_by(func.count(Measurement.station).desc())
                             .all())
    
    station_list = q_station_list[0][0]
    print(station_list)


    # get info for dates and order by date
    results = (session.query(Measurement.station, Measurement.date, Measurement.tobs)
                      .filter(Measurement.date >= start_date)
                      .filter(Measurement.station == station_list)
                      .all())

    # JSONify results
    tobs_list = []
    for row in results:
        record = {}
        record["Date"] = row[1]
        record["Station"] = row[0]
        record["Temperature"] = int(row[2])
        tobs_list.append(record)

    return jsonify(tobs_list)

#create a route for users to input a start date for temperature data
@app.route("/api/v1.0/<start>") 
def start_route(start):

    session = Session(engine)

#define max and min for dates entered
    date_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_max_str = str(date_max)
    date_max_str = re.sub("'|,", "",date_max_str)
    print (date_max_str)

    date_min = session.query(Measurement.date).first()
    date_min_str = str(date_min)
    date_min_str = re.sub("'|,", "",date_min_str)
    print (date_min_str)


    # check date entered
    range_check = session.query(exists().where(Measurement.date == start)).scalar()
 
    if range_check:

    	results = (session.query(func.min(Measurement.tobs)
    				 ,func.avg(Measurement.tobs)
    				 ,func.max(Measurement.tobs))
    				 	  .filter(Measurement.date >= start).all())

    	temp_min =results[0][0]
    	temp_avg =results[0][1]
    	temp_max =results[0][2]
    
    	result_q =( ['Date: ' + start,
    						'The lowest Temperature was: '  + str(temp_min) + ' F',
    						'The average Temperature was: ' + str(temp_avg) + ' F',
    						'The highest Temperature was: ' + str(temp_max) + ' F'])
    	return jsonify(result_q)

    return jsonify({"error": f"Input Date {start} not valid. Date Range is between {date_min_str} and {date_max_str}"}), 404





#create a route for users to input start and end date for temperature data
@app.route("/api/v1.0/<start>/<end>") 
def start_end(start, end):


    session = Session(engine)

    # set date max and min
    date_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_max_str = str(date_max)
    date_max_str = re.sub("'|,", "",date_max_str)
    print (date_max_str)

    date_min = session.query(Measurement.date).first()
    date_min_str = str(date_min)
    date_min_str = re.sub("'|,", "",date_min_str)
    print (date_min_str)

    # check range for start date
    range_check_start = session.query(exists().where(Measurement.date == start)).scalar()
 	
 	# check range for end date
    range_check_end = session.query(exists().where(Measurement.date == end)).scalar()

    if range_check_start and range_check_end:

    	results = (session.query(func.min(Measurement.tobs)
    				 ,func.avg(Measurement.tobs)
    				 ,func.max(Measurement.tobs))
    					  .filter(Measurement.date >= start)
    				  	  .filter(Measurement.date <= end).all())

    	temp_min =results[0][0]
    	temp_avg =results[0][1]
    	temp_max =results[0][2]
    
    	result_q =( ['Start Date: ' + start,
    						'End Date: ' + end,
    						'The lowest Temperature was: '  + str(temp_min) + ' F',
    						'The average Temperature was: ' + str(temp_avg) + ' F',
    						'The highest Temperature was: ' + str(temp_max) + ' F'])
    	return jsonify(result_q)

    if not range_check_start and not range_check_end:
    	return jsonify({"error": f"Input Start {start} and End Date {end} not within Date Range. Date Range is between {date_min_str} and {date_max_str}"}), 404

    if not range_check_start:
    	return jsonify({"error": f"Input Start Date {start} not valid. Date Range is between {date_min_str} and {date_max_str}"}), 404

    if not range_check_end:
    	return jsonify({"error": f"Input End Date {end} not valid. Date Range is between {date_min_str} and {date_max_str}"}), 404






if __name__ == '__main__':
    app.run(debug=True)