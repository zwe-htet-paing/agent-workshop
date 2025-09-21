import streamlit as st
import asyncio
import datetime
from datetime import date, timedelta
import pandas as pd
import json

# Import LangGraph API client (adjust import based on your setup)
try:
    from langgraph_sdk import get_client
    URL = "http://127.0.0.1:2024"
    client = get_client(url=URL)
    assistant_id = "agent"
except ImportError:
    st.error("Please install langgraph-sdk: pip install langgraph-sdk")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="🌍 AI Travel Itinerary Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    
    .trip-summary {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .progress-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .step-completed {
        color: #51cf66;
    }
    
    .step-current {
        color: #667eea;
    }
    
    .step-pending {
        color: #868e96;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🌍 AI Travel Itinerary Planner</h1>
    <p>Plan your perfect trip with AI-powered flight and hotel recommendations</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'itinerary_generated' not in st.session_state:
    st.session_state.itinerary_generated = False
if 'current_result' not in st.session_state:
    st.session_state.current_result = None
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'generation_steps' not in st.session_state:
    st.session_state.generation_steps = {}
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

# Async function to handle the streaming API
async def generate_itinerary_stream(input_state):
    """Stream itinerary generation with real-time updates"""
    
    # Create thread if it doesn't exist
    if not st.session_state.thread_id:
        thread = await client.threads.create()
        st.session_state.thread_id = thread["thread_id"]
    
    # Track progress
    progress_steps = {
        "update_airport_codes": "🗺️ Converting airport codes...",
        "validate_dates": "📅 Validating travel dates...",
        "get_flight_options": "✈️ Searching flight options...",
        "get_hotel_options": "🏨 Finding hotel options...",
        "get_flight_recommendation": "🎯 Analyzing best flights...",
        "get_hotel_recommendation": "🏆 Selecting optimal hotel...",
        "generate_itinerary": "📋 Creating your itinerary..."
    }
    
    final_result = {}
    
    try:
        async for event in client.runs.stream(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            input=input_state,
            stream_mode="values"
        ):
            # Update session state with current event
            if hasattr(event, 'data') and event.data:
                # Extract current step information
                current_step = None
                if hasattr(event.data, '__dict__'):
                    for step_name in progress_steps.keys():
                        if step_name in str(event.data):
                            current_step = step_name
                            break
                
                # Update progress
                if current_step:
                    st.session_state.generation_steps[current_step] = "completed"
                
                # Store the latest complete state
                final_result = event.data
                
            # Yield for real-time updates
            yield final_result, st.session_state.generation_steps
            
    except Exception as e:
        st.error(f"Error during generation: {str(e)}")
        yield None, st.session_state.generation_steps

def display_progress(steps):
    """Display current generation progress"""
    progress_steps = {
        "update_airport_codes": "🗺️ Converting airport codes...",
        "validate_dates": "📅 Validating travel dates...",
        "get_flight_options": "✈️ Searching flight options...",
        "get_hotel_options": "🏨 Finding hotel options...",
        "get_flight_recommendation": "🎯 Analyzing best flights...",
        "get_hotel_recommendation": "🏆 Selecting optimal hotel...",
        "generate_itinerary": "📋 Creating your itinerary..."
    }
    
    st.markdown('<div class="progress-container">', unsafe_allow_html=True)
    st.markdown("### 🔄 Generation Progress")
    
    for step_name, step_desc in progress_steps.items():
        status = steps.get(step_name, "pending")
        if status == "completed":
            st.markdown(f'<div class="step-completed">✅ {step_desc}</div>', unsafe_allow_html=True)
        elif step_name in steps and status != "completed":
            st.markdown(f'<div class="step-current">🔄 {step_desc}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="step-pending">⏳ {step_desc}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Sidebar for input form
with st.sidebar:
    st.header("✈️ Trip Details")
    
    with st.form("trip_form"):
        st.subheader("📍 Locations")
        
        # Origin and Destination
        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input(
                "From", 
                placeholder="e.g., Bangkok or BKK",
                help="Enter city name or 3-letter airport code"
            )
        with col2:
            destination = st.text_input(
                "To", 
                placeholder="e.g., Chiang Mai or CNX",
                help="Enter city name or 3-letter airport code"
            )
        
        st.subheader("📅 Travel Dates")
        
        # Date inputs
        today = date.today()
        departure_date = st.date_input(
            "Departure Date",
            value=today + timedelta(days=7),
            min_value=today,
            max_value=today + timedelta(days=365)
        )
        
        return_date = st.date_input(
            "Return Date",
            value=today + timedelta(days=10),
            min_value=departure_date + timedelta(days=1) if departure_date else today + timedelta(days=1),
            max_value=today + timedelta(days=365)
        )
        
        # Submit button
        submit_button = st.form_submit_button(
            "🚀 Plan My Trip", 
            use_container_width=True,
            disabled=st.session_state.is_generating
        )

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    if submit_button and not st.session_state.is_generating:
        # Validation
        errors = []
        
        if not origin.strip():
            errors.append("Please enter departure location")
        if not destination.strip():
            errors.append("Please enter destination location")
        if departure_date >= return_date:
            errors.append("Return date must be after departure date")
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Show trip summary
            days = (return_date - departure_date).days
            
            st.markdown(f"""
            <div class="trip-summary">
                <h3>🎯 Trip Summary</h3>
                <ul>
                    <li><strong>From:</strong> {origin}</li>
                    <li><strong>To:</strong> {destination}</li>
                    <li><strong>Departure:</strong> {departure_date.strftime('%B %d, %Y')}</li>
                    <li><strong>Return:</strong> {return_date.strftime('%B %d, %Y')}</li>
                    <li><strong>Duration:</strong> {days} days</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Prepare input state
            input_state = {
                "origin": origin.strip(),
                "destination": destination.strip(),
                "departure_date": departure_date.strftime("%Y-%m-%d"),
                "return_date": return_date.strftime("%Y-%m-%d")
            }
            
            # Set generating state
            st.session_state.is_generating = True
            st.session_state.generation_steps = {}
            
            # Create placeholders for single-location updates
            progress_placeholder = st.empty()
            result_placeholder = st.empty()
            
            # Run async generation with streaming
            async def run_generation():
                final_result = None
                async for result, steps in generate_itinerary_stream(input_state):
                    # Update progress in the same location
                    with progress_placeholder.container():
                        display_progress(steps)
                    
                    # Update result if available
                    if result:
                        final_result = result
                        # Handle dict result
                        itinerary_data = result.get('itinerary', '') if isinstance(result, dict) else getattr(result, 'itinerary', '')
                        if itinerary_data:
                            with result_placeholder.container():
                                st.markdown("### 🎉 Itinerary Preview")
                                with st.expander("Click to view your itinerary", expanded=True):
                                    preview = itinerary_data[:500] + "..." if len(itinerary_data) > 500 else itinerary_data
                                    st.markdown(preview)
                
                # Final cleanup - clear progress and show success
                progress_placeholder.empty()
                st.session_state.current_result = final_result
                st.session_state.itinerary_generated = True
                st.session_state.is_generating = False
                
                if final_result:
                    st.success("🎉 Your itinerary has been generated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to generate itinerary. Please try again.")
            
            # Run the async function
            asyncio.run(run_generation())
    
    # Show generation in progress
    if st.session_state.is_generating:
        st.info("🔄 Generation in progress... Please wait.")

# Display results if available
if st.session_state.itinerary_generated and st.session_state.current_result and not st.session_state.is_generating:
    result = st.session_state.current_result
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["🗓️ Full Itinerary", "✈️ Flight Details", "🏨 Hotel Details", "📊 Trip Overview"])
    
    with tab1:
        st.header("📋 Your Complete Itinerary")
        itinerary_data = result.get('itinerary', '') if isinstance(result, dict) else getattr(result, 'itinerary', '')
        if itinerary_data:
            st.markdown(itinerary_data)
        else:
            st.warning("No itinerary data available.")
    
    with tab2:
        st.header("✈️ Recommended Flight")
        flight_data = result.get('flight_data', '') if isinstance(result, dict) else getattr(result, 'flight_data', '')
        if flight_data:
            st.markdown(flight_data)
        else:
            st.warning("No flight data available.")
    
    with tab3:
        st.header("🏨 Recommended Hotel")
        hotel_data = result.get('hotel_data', '') if isinstance(result, dict) else getattr(result, 'hotel_data', '')
        if hotel_data:
            st.markdown(hotel_data)
        else:
            st.warning("No hotel data available.")
    
    with tab4:
        st.header("📊 Trip Overview")
        
        # Display key information in metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            origin_val = result.get('origin', 'N/A') if isinstance(result, dict) else getattr(result, 'origin', 'N/A')
            st.metric("Origin", origin_val)
        with col2:
            dest_val = result.get('destination', 'N/A') if isinstance(result, dict) else getattr(result, 'destination', 'N/A')
            st.metric("Destination", dest_val)
        with col3:
            dep_val = result.get('departure_date', 'N/A') if isinstance(result, dict) else getattr(result, 'departure_date', 'N/A')
            st.metric("Departure", dep_val)
        with col4:
            ret_val = result.get('return_date', 'N/A') if isinstance(result, dict) else getattr(result, 'return_date', 'N/A')
            st.metric("Return", ret_val)
        
        # Show validation status
        is_valid = result.get('is_valid_date') if isinstance(result, dict) else getattr(result, 'is_valid_date', None)
        if is_valid is not None:
            if is_valid:
                st.success("✅ All dates are valid")
            else:
                st.error("❌ Date validation failed")
        
        # Show thread ID for debugging
        if st.session_state.thread_id:
            st.info(f"🔗 Thread ID: `{st.session_state.thread_id}`")

# Sidebar info
with col2:
    if not st.session_state.itinerary_generated:
        st.markdown("""
        ### 🎯 How it works:
        
        1. **Enter your travel details** in the form
        2. **Click "Plan My Trip"** to start the AI planning process
        3. **Watch real-time progress** as AI analyzes options
        4. **Get personalized recommendations** for flights and hotels
        5. **Receive a detailed itinerary** with activities, restaurants, and costs
        
        ### ✨ Features:
        - 🤖 AI-powered flight recommendations
        - 🏨 Smart hotel selection
        - 📅 Day-by-day itinerary planning
        - 💰 Cost estimation
        - 🗺️ Local attractions and restaurants
        - 🔄 Real-time generation progress
        
        ### 💡 Tips:
        - Use city names or airport codes
        - Plan at least a week in advance
        - Consider your budget and preferences
        """)
    else:
        st.markdown("""
        ### 🎉 Itinerary Generated!
        
        Your AI-powered travel plan is ready! 
        
        **What's included:**
        - ✈️ Best flight recommendations
        - 🏨 Optimal hotel selection
        - 🗓️ Day-by-day activities
        - 🍽️ Restaurant suggestions
        - 💰 Cost estimates
        
        ### 📤 Export Options:
        """)
        
        # Add download button for the itinerary
        if st.session_state.current_result:
            itinerary_text = None
            if isinstance(st.session_state.current_result, dict):
                itinerary_text = st.session_state.current_result.get('itinerary', '')
            else:
                itinerary_text = getattr(st.session_state.current_result, 'itinerary', '')
            
            if itinerary_text:
                st.download_button(
                    label="📄 Download Itinerary",
                    data=itinerary_text,
                    file_name=f"itinerary_{datetime.datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
        
        if st.button("🔄 Plan Another Trip", use_container_width=True):
            st.session_state.itinerary_generated = False
            st.session_state.current_result = None
            st.session_state.thread_id = None
            st.session_state.generation_steps = {}
            st.session_state.is_generating = False
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    Made with ❤️ using Streamlit and LangGraph API | 
    <a href="#" style="color: #667eea;">About</a> | 
    <a href="#" style="color: #667eea;">Contact</a>
</div>
""", unsafe_allow_html=True)