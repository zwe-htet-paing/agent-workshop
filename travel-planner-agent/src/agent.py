
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from langgraph.graph import START, StateGraph, END

from src.utils.state import ItineraryAgentState
from src.utils.nodes import validate_dates, get_flight_options, get_hotel_options

from datetime import datetime

llm = ChatOpenAI(model="gpt-4", temperature=0)


def should_continue(state: ItineraryAgentState):
    if not state.is_valid_date:
        return END
    
    return ["get_flight_options", "get_hotel_options"]

def is_iata(code: str) -> bool:
    return isinstance(code, str) and len(code) == 3 and code.isalpha()


def get_iata_from_name(name: str) -> str:
    system_prompt = """
    Given a city name, return ONLY the main airport's IATA code (3 letters).
    If it's already an IATA code, just return it.
    If multiple airports exist, choose the largest/primary one.
    Output only the IATA code, nothing else.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=name)
    ]
    
    response = llm(messages)
    return response.content
    
    
    
def update_airport_codes(state: ItineraryAgentState):
    
    if is_iata(state.origin) and is_iata(state.destination):
        return {"origin": state.origin, "destination": state.destination}
    
    if not is_iata(state.origin):
        origin = get_iata_from_name(state.origin)
        
    if not is_iata(state.destination):
        destination = get_iata_from_name(state.destination)
        
    return {"origin": origin, "destination": destination}
    

flight_agent_instructions = """

Your are AI expert that provides in-depth analysis comparing flight options based on multiple factors. Analyze flight options and recommend the best one considering price, duration, stops, and overall convenience.

Recommend the best flight from the available options, based on the details provided below:

**Reasoning for Recommendation:**
- **Price:** Provide a detailed explanation about why this flight offers the best value compared to others.
- **Duration:** Explain why this flight has the best duration in comparison to others.
- **Stops:** Discuss why this flight has minimal or optimal stops.
- **Travel Class:** Describe why this flight provides the best comfort and amenities.

Use the provided flight data as the basis for your recommendation. Be sure to justify your choice using clear reasoning for each attribute. Do not repeat the flight details in your response.
"""


hotel_agent_instructions = """

Your are AI expert that provides in-depth analysis comparing hotel options based on multiple factors. Analyze hotel options and recommend the best one considering price, rating, location, and amenities.

Based on the following analysis, generate a detailed recommendation for the best hotel. Your response should include clear reasoning based on price, rating, location, and amenities.

**AI Hotel Recommendation**
We recommend the best hotel based on the following analysis:

**Reasoning for Recommendation**:
- **Price:** The recommended hotel is the best option for the price compared to others, offering the best value for the amenities and services provided.
- **Rating:** With a higher rating compared to the alternatives, it ensures a better overall guest experience. Explain why this makes it the best choice.
- **Location:** The hotel is in a prime location, close to important attractions, making it convenient for travelers.
- **Amenities:** The hotel offers amenities like Wi-Fi, pool, fitness center, free breakfast, etc. Discuss how these amenities enhance the experience, making it suitable for different types of travelers.

**Reasoning Requirements**:
- Ensure that each section clearly explains why this hotel is the best option based on the factors of price, rating, location, and amenities.
- Compare it against the other options and explain why this one stands out.
- Provide concise, well-structured reasoning to make the recommendation clear to the traveler.
- Your recommendation should help a traveler make an informed decision based on multiple factors, not just one.
"""


def get_flight_recommendation(state: ItineraryAgentState):
    flight_options = state.flight_options
    
    if not flight_options:
        return {"flight_data": "No flight options available."}
    
    messages = [SystemMessage(content=flight_agent_instructions),
                HumanMessage(content=f"Flight options: {flight_options}")]
    
    
    recommended_flight = llm.invoke(messages)
    
    return {"flight_data": recommended_flight.content}


def get_hotel_recommendation(state: ItineraryAgentState):
    hotel_options = state.hotel_options
    
    if not hotel_options:
        return {"hotel_data": "No hotel options available."}
    
    messages = [SystemMessage(content=hotel_agent_instructions),
                HumanMessage(content=f"Hotel options: {hotel_options}")]
    
    recommended_hotel = llm.invoke(messages)
    
    return {"hotel_data": recommended_hotel.content}
    

def generate_itinerary(state: ItineraryAgentState):
    
    flight_data = state.flight_data
    hotel_data = state.hotel_data
    
    destination = state.destination
    departure_date = state.departure_date
    return_date = state.return_date
    
    days = (datetime.strptime(departure_date, "%Y-%m-%d") - datetime.strptime(return_date, "%Y-%m-%d")).days
    
    
    planner_agent_instructions = f"""
Your are an AI Travel Planner Expert that create a detailed itinerary for the user based on flight and hotel information.

Based on the following details, create a {days}-day itinerary for the user:

The itinerary should include:
- Flight arrival and departure information
- Hotel check-in and check-out details
- Day-by-day breakdown of activities
- Must-visit attractions and estimated visit times
- Restaurant recommendations for meals
- Tips for local transportation
- Estimated daily expenses 💰 and total trip cost

**Format Requirements**:
- Use markdown formatting with clear headings (# for main headings, ## for days, ### for sections)
- Include emojis for different types of activities ( for landmarks, 🍽️ for restaurants, etc.)
- Use bullet points for listing activities
- Include estimated timings for each activity
- Include estimated cost for each activity, meal, and transportation
- Include total estimated cost at the end of the itinerary
- Format the itinerary to be visually appealing and easy to read
"""
    
    user_message = f"""

**Flight Details**:
{flight_data}

**Hotel Details**:
{hotel_data}

**Destination**: {destination}

**Travel Dates**: {departure_date} to {return_date} ({days} days)
"""

    
    messages = [
        SystemMessage(content=planner_agent_instructions),
        HumanMessage(content=user_message)
    ]
    
    result = llm.invoke(messages)
        
    return {"itinerary": result.content}



builder = StateGraph(ItineraryAgentState)

builder.add_node("update_airport_codes", update_airport_codes)
builder.add_node("validate_dates", validate_dates)
builder.add_node("get_flight_options", get_flight_options)
builder.add_node("get_hotel_options", get_hotel_options)

builder.add_node("get_flight_recommendation", get_flight_recommendation)
builder.add_node("get_hotel_recommendation", get_hotel_recommendation)

builder.add_node("generate_itinerary", generate_itinerary)

builder.set_entry_point("update_airport_codes")
builder.add_edge("update_airport_codes", "validate_dates")

builder.add_conditional_edges(
    "validate_dates", 
    should_continue,
    {
        "get_flight_options": "get_flight_options",
        "get_hotel_options": "get_hotel_options",
        END: END
    }
)


builder.add_edge("get_flight_options", "get_flight_recommendation")
builder.add_edge("get_hotel_options", "get_hotel_recommendation")

builder.add_edge("get_flight_recommendation", "generate_itinerary")
builder.add_edge("get_hotel_recommendation", "generate_itinerary")

builder.add_edge("generate_itinerary", END)

graph = builder.compile()

# Example usage (uncommented for testing)
def run_itinerary_agent():
    initial_state = ItineraryAgentState(
        origin="BKK",
        destination="CNX",
        departure_date="2025-09-20",
        return_date="2025-09-22"
    )
    
    result = graph.invoke(initial_state)
    return result