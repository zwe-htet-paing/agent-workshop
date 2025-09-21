from datetime import datetime
from typing import TypedDict
from src.utils.state import ItineraryAgentState
from src.utils.tools import search_flights_tool, search_hotels_tool


def get_flight_options(state: ItineraryAgentState):
    input_dict = {
        "origin": state.origin,
        "destination": state.destination,
        "departure_date": state.departure_date,
        "return_date": state.return_date
    }
    
    result = search_flights_tool.invoke(input_dict)
    return {"flight_options": result.get("flights", [])}


def get_hotel_options(state: ItineraryAgentState):
    input_dict = {
        "destination": state.destination,
        "check_in_date": state.departure_date,
        "check_out_date": state.return_date
    }
    
    result = search_hotels_tool.invoke(input_dict)
    return {"hotel_options": result.get("hotels", [])}


def validate_dates(state: ItineraryAgentState):
    
    departure_date = state.departure_date
    return_date = state.return_date
    
    try:
        dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
        ret_date = datetime.strptime(return_date, "%Y-%m-%d")
        today = datetime.today()

        # Check if dates are in the future
        if dep_date < today or ret_date < today:
            return {"is_valid_date": False, "validation_message": "Departure and return dates must be in the future."}
        
        # Check if return date is after departure date
        if ret_date <= dep_date:
            return {"is_valid_date": False, "validation_message": "Return date must be after departure date."}
        
        return {"is_valid_date": True, "validation_message": "Dates are valid."}
    
    except ValueError as e:
        return {"is_valid_date": False, "validation_message": f"Invalid date format: {str(e)}"}
    
    

    