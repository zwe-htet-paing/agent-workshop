from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Annotated

class ItineraryAgentState(BaseModel):
    
    origin: str
    destination: str
    departure_date: str      # format: YYYY-MM-DD
    return_date: str         # format: YYYY-MM-DD
    
    is_valid_date: Optional[bool] = None
    validation_message: Optional[str] = None
    
    flight_options: List[Dict[str, Any]] = Field(default_factory=list)
    hotel_options: List[Dict[str, Any]] = Field(default_factory=list)
    
    flight_data: Optional[str] = None
    hotel_data: Optional[str] = None
    
    itinerary: Optional[str] = None
    
    is_valid_date: Optional[bool] = None