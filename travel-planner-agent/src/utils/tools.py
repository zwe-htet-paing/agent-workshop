from functools import lru_cache
from typing import List, Optional, Any, Callable, Dict
from serpapi import GoogleSearch
from langchain_core.tools import tool

import os

@lru_cache(maxsize=None)
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str]) -> dict:
    """
    Search flights between two airports using SerpAPI Google Flights and return available options.
    """
    params = {
        "api_key": os.environ["SERPAPI_API_KEY"],
        "engine": "google_flights",
        "hl": "en",
        "gl": "th",
        "departure_id": origin.strip().upper(),
        "arrival_id": destination.strip().upper(),
        "outbound_date": departure_date,
        "return_date": return_date,
        "currency": "THB"
    }
    
    results = GoogleSearch(params).get_dict()
    return results


@lru_cache(maxsize=None)
def search_hotels(
    destination: str, 
    check_in_date: str, 
    check_out_date: str) -> dict:
    """
    Search hotels in a location using SerpAPI Google Hotels and return available options.
    """
    
    params = {
        "api_key": os.environ["SERPAPI_API_KEY"],
        "engine": "google_hotels",
        "hl": "en",
        "gl": "th",
        "q": destination,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "currency": "THB",
        "sort_by": 3,
        "rating": 8
    }
    
    results = GoogleSearch(params).get_dict()
    return results


@tool
def search_flights_tool(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str]) -> dict:
    """
    Search for flights using Google Flights API
    
    Args:
        origin: Origin airport code or city
        destination: Destination airport code or city
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD)
    
    Returns:
        Dict containing flight search results
    """
    try:
        results = search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date
        )
        
        flights = []
        if "best_flights" in results:
            for flight in results["best_flights"][:5]:  # Top 5 flights
                flights.append({
                    "airline": flight.get("flights", [{}])[0].get("airline", "Unknown"),
                    "price": flight.get("price", "N/A"),
                    "duration": flight.get("total_duration", "N/A"),
                    "departure_time": flight.get("flights", [{}])[0].get("departure_airport", {}).get("time", "N/A"),
                    "arrival_time": flight.get("flights", [{}])[-1].get("arrival_airport", {}).get("time", "N/A"),
                    "stops": len(flight.get("flights", [])) - 1,
                    "travel_class": flight.get("flights", [{}])[0].get("travel_class", "N/A"),
                    # "return_date":
                    # "airline_logo":
                })
        
        return {
            "flights": flights,
            "search_metadata": {
                "origin": origin,
                "destination": destination, 
                "departure_date": departure_date,
                "return_date": return_date
            }
        }
        
    except Exception as e:
        return {"error": f"Flight search failed: {str(e)}", "flights": []}


@tool
def search_hotels_tool(
    destination: str,
    check_in_date: str,
    check_out_date: str) -> dict:
    """
    Search for hotels using Google Hotels API
    
    Args:
        location: Hotel destination
        check_in_date: Check-in date (YYYY-MM-DD)
        check_out_date: Check-out date (YYYY-MM-DD)
        budget: Optional budget per night
        
    Returns:
        Dict containing hotel search results
    """
    try:
        results = search_hotels(
            destination=destination,
            check_in_date=check_in_date,
            check_out_date=check_out_date
        )
        
        hotels = []
        if "properties" in results:
            for hotel in results["properties"][:5]:  # Top 5 hotels
                hotels.append({
                    "name": hotel.get("name", "Unknown"),
                    "price": hotel.get("rate_per_night", {}).get("lowest", "N/A"),
                    "rating": hotel.get("overall_rating", "N/A"),
                    "location": hotel.get("nearby_places", "N/A"),
                    "amenities": hotel.get("amenities", []),
                    "link": hotel.get("link", "N/A")
                })
        
        return {
            "hotels": hotels,
            "search_metadata": {
                "destination": destination,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                # "budget": budget
            }
        }
        
    except Exception as e:
        return {"error": f"Hotel search failed: {str(e)}", "hotels": []}



@tool
def extract_travel_details(user_request: str) -> Dict[str, str]:
    """
    Extract travel details from user request using LLM
    
    Args:
        user_request: Raw user travel request
        
    Returns:
        Dict with extracted travel details
    """
    # This would typically use an LLM to extract structured data
    # For demo purposes, returning a simple extraction
    return {
        "origin": "Bangkok",
        "destination": "Chiang Mai", 
        "departure_date": "2024-04-20",
        "return_date": "2024-04-22",
        "budget": "10000",
        "travelers": "2"
    }

TOOLS: List[Callable[..., Any]] = [
    search_flights_tool,
    search_hotels_tool
    ]