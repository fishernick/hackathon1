"""
PurdueAI - A simple ChatGPT wrapper chatbot
"""

import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
import googlemaps

# Load environment variables
load_dotenv()

class IntentClassifier:
    def __init__(self):
        """Initialize the intent classifier with pattern-based rules"""
        # Define patterns for different intents using regex
        self.patterns = {
            'location': [
                r'\bwhere\s+is\b',
                r'\baddress\s+of\b',
                r'\blocation\s+of\b',
                r'\bwhere\s+can\s+i\s+find\b',
                r'\bwhat\s+is\s+the\s+address\b',
                r'\bwhere\s+is\s+this\s+place\b',
                r'\bhow\s+do\s+i\s+find\b',
                r'\bcan\s+you\s+tell\s+me\s+where\b',
                r'\bwhat\s+is\s+the\s+location\b',
                r'\bwhere\s+is\s+the\b',
                r'\baddress\s+of\s+the\b',
                r'\blocation\s+of\s+the\b'
            ],
            'directions': [
                r'\bhow\s+do\s+i\s+get\s+to\b',
                r'\bdirections\s+to\b',
                r'\bhow\s+to\s+get\s+to\b',
                r'\bdirections\s+from\b',
                r'\bhow\s+do\s+i\s+walk\s+to\b',
                r'\bdriving\s+directions\b',
                r'\bwalking\s+directions\b',
                r'\bbiking\s+directions\b',
                r'\btransit\s+directions\b',
                r'\bhow\s+to\s+get\s+there\b',
                r'\bwhat\s+is\s+the\s+way\s+to\b',
                r'\bcan\s+you\s+show\s+me\s+how\s+to\s+get\b',
                r'\bwhat\s+is\s+the\s+route\s+to\b',
                r'\bhow\s+do\s+i\s+travel\s+to\b',
                r'\bwhat\s+is\s+the\s+path\s+to\b',
                r'\bcan\s+you\s+guide\s+me\s+to\b',
                r'\bhow\s+do\s+i\s+navigate\s+to\b',
                r'\bshow\s+me\s+the\s+way\b',
                r'\bgive\s+me\s+directions\b',
                r'\bhow\s+do\s+i\s+go\s+to\b'
            ],
            'distance_time': [
                r'\bhow\s+far\s+is\b',
                r'\bdistance\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\b',
                r'\btravel\s+time\s+from\b',
                r'\bhow\s+long\s+to\s+get\s+to\b',
                r'\btime\s+from\b',
                r'\bhow\s+far\s+from\b',
                r'\bhow\s+much\s+time\b',
                r'\bhow\s+long\s+is\s+the\s+drive\b',
                r'\bhow\s+long\s+is\s+the\s+walk\b',
                r'\bhow\s+long\s+is\s+the\s+ride\b',
                r'\bhow\s+many\s+miles\b',
                r'\bhow\s+many\s+minutes\b',
                r'\bhow\s+many\s+hours\b',
                r'\bwhat\s+is\s+the\s+distance\b',
                r'\bwhat\s+is\s+the\s+travel\s+time\b',
                r'\bhow\s+long\s+will\s+it\s+take\b',
                r'\bhow\s+far\s+away\s+is\b',
                r'\bhow\s+far\s+apart\s+are\b',
                r'\bwhat\s+is\s+the\s+walking\s+distance\b',
                r'\bwhat\s+is\s+the\s+driving\s+distance\b',
                r'\bhow\s+long\s+to\s+walk\b',
                r'\bhow\s+long\s+to\s+drive\b',
                r'\bhow\s+long\s+to\s+bike\b',
                r'\bhow\s+long\s+to\s+ride\b',
                r'\bwalking\s+time\s+from\b',
                r'\bdriving\s+time\s+from\b',
                r'\bbiking\s+time\s+from\b',
                r'\btransit\s+time\s+from\b',
                r'\bhow\s+far\s+is\s+it\s+to\b',
                r'\bhow\s+far\s+is\s+it\s+from\b',
                r'\bhow\s+far\s+away\s+from\b',
                r'\bhow\s+close\s+is\s+it\s+to\b',
                r'\bhow\s+close\s+are\s+they\b',
                r'\bwhat\s+is\s+the\s+walk\s+time\b',
                r'\bwhat\s+is\s+the\s+drive\s+time\b',
                r'\bwhat\s+is\s+the\s+ride\s+time\b',
                r'\bhow\s+much\s+time\s+to\s+walk\b',
                r'\bhow\s+much\s+time\s+to\s+drive\b',
                r'\bhow\s+much\s+time\s+to\s+bike\b',
                r'\bhow\s+much\s+time\s+to\s+ride\b',
                r'\bhow\s+long\s+is\s+the\s+journey\b',
                r'\bhow\s+long\s+is\s+the\s+trip\b',
                r'\bhow\s+long\s+is\s+the\s+commute\b',
                r'\bwhat\s+is\s+the\s+duration\b',
                r'\bwhat\s+is\s+the\s+travel\s+duration\b',
                r'\bhow\s+long\s+does\s+the\s+walk\s+take\b',
                r'\bhow\s+long\s+does\s+the\s+drive\s+take\b',
                r'\bhow\s+long\s+does\s+the\s+ride\s+take\b',
                r'\bhow\s+long\s+does\s+the\s+trip\s+take\b',
                r'\bhow\s+long\s+does\s+the\s+journey\s+take\b',
                r'\bhow\s+long\s+does\s+the\s+commute\s+take\b',
                r'\bhow\s+long\s+does\s+the\s+walk\s+from\b',
                r'\bhow\s+long\s+does\s+the\s+drive\s+from\b',
                r'\bhow\s+long\s+does\s+the\s+ride\s+from\b',
                r'\bhow\s+long\s+does\s+the\s+trip\s+from\b',
                r'\bhow\s+long\s+does\s+the\s+journey\s+from\b',
                r'\bhow\s+long\s+does\s+the\s+commute\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+walk\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+drive\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+bike\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+ride\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+get\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+reach\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+go\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+travel\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+commute\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+journey\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+trip\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+walk\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+drive\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+bike\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+ride\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+get\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+reach\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+go\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+travel\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+commute\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+journey\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+trip\s+to\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+walk\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+drive\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+bike\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+ride\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+get\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+reach\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+go\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+travel\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+commute\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+journey\s+from\b',
                r'\bhow\s+long\s+does\s+it\s+take\s+to\s+trip\s+from\b'
            ]
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for intent, pattern_list in self.patterns.items():
            self.compiled_patterns[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in pattern_list]
    
    def classify_intent(self, text):
        """Classify the intent of the given text using pattern matching"""
        text_lower = text.lower()
        
        # Check for location patterns
        location_score = 0
        for pattern in self.compiled_patterns['location']:
            if pattern.search(text_lower):
                location_score += 1
        
        # Check for directions patterns
        directions_score = 0
        for pattern in self.compiled_patterns['directions']:
            if pattern.search(text_lower):
                directions_score += 1
        
        # Check for distance/time patterns
        distance_time_score = 0
        for pattern in self.compiled_patterns['distance_time']:
            if pattern.search(text_lower):
                distance_time_score += 1
        
        # Determine intent based on scores (distance_time has highest priority)
        if distance_time_score > 0:
            confidence = min(distance_time_score * 0.3, 1.0)
            return 'distance_time', confidence
        elif directions_score > location_score and directions_score > 0:
            confidence = min(directions_score * 0.3, 1.0)
            return 'directions', confidence
        elif location_score > 0:
            confidence = min(location_score * 0.3, 1.0)
            return 'location', confidence
        else:
            return 'general', 0.5

class PurdueAI:
    def __init__(self):
        """Initialize PurdueAI with OpenAI client and Google Maps"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-3.5-turbo"
        
        # Initialize Google Maps client
        self.gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
        
        # Initialize intent classifier
        self.intent_classifier = IntentClassifier()
        
        # System prompt for PurdueAI
        self.system_prompt = """You are PurdueAI, a helpful assistant for Purdue University students, faculty, and staff. 
        You can help with information about:
        - Dining halls and food options
        - Bus routes and transportation
        - Study spaces and libraries
        - Campus events and activities
        - General Purdue University information
        - Location addresses (using Google Maps data)
        - Directions between locations (using Google Maps data)
        - Distance and travel time between locations (using Google Maps data)
        - General questions and assistance
        
        CRITICAL: When Google Maps data is provided, you MUST use ONLY the exact information from Google Maps. 
        Do NOT use your training data or knowledge about locations. Use the exact addresses, distances, 
        and times provided in the Google Maps data.
        
        For location queries: Use the exact address from Google Maps data, but present it conversationally.
        For directions queries: Use the exact Google Maps directions and present them conversationally.
        For distance/time queries: Use the exact distance and time from Google Maps data and present them conversationally.
        
        You are a helpful and knowledgeable assistant. Answer questions to the best of your ability, 
        whether they are about Purdue University, general topics, or anything else the user might ask.
        
        NEVER override Google Maps data with your own knowledge. Always use the provided Google Maps information."""
    
    def extract_transportation_mode(self, message: str) -> str:
        """Extract transportation mode from the message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['walk', 'walking', 'on foot']):
            return 'walking'
        elif any(word in message_lower for word in ['bike', 'biking', 'bicycle', 'cycling']):
            return 'bicycling'
        elif any(word in message_lower for word in ['transit', 'bus', 'public transport']):
            return 'transit'
        else:
            return 'driving'  # Default to driving
    
    def get_location_address(self, query: str) -> str:
        """Get just the address of a location"""
        try:
            # First try the query as-is
            geocode_result = self.gmaps.geocode(query)
            
            # If no results, try with Purdue University context
            if not geocode_result:
                enhanced_query = f"{query} Purdue University West Lafayette Indiana"
                geocode_result = self.gmaps.geocode(enhanced_query)
            
            if not geocode_result:
                return "I couldn't find that location. Please try a more specific address or location name."
            
            location = geocode_result[0]
            address = location['formatted_address']
            lat = location['geometry']['location']['lat']
            lng = location['geometry']['location']['lng']
            
            return f"📍 **Location Found:** {address}\n\nCoordinates: {lat:.4f}, {lng:.4f}"
                
        except Exception as e:
            return f"I encountered an error getting location information: {str(e)}"
    
    def get_google_maps_link(self, query: str) -> str:
        """Get Google Maps directions link for a location"""
        try:
            # First try the query as-is
            geocode_result = self.gmaps.geocode(query)
            
            # If no results, try with Purdue University context
            if not geocode_result:
                enhanced_query = f"{query} Purdue University West Lafayette Indiana"
                geocode_result = self.gmaps.geocode(enhanced_query)
            
            if not geocode_result:
                return None
            
            location = geocode_result[0]
            lat = location['geometry']['location']['lat']
            lng = location['geometry']['location']['lng']
            
            # Create Google Maps directions link
            maps_link = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
            return maps_link
                
        except Exception as e:
            return None
    
    def extract_address_from_info(self, location_info: str) -> str:
        """Extract the address from location info string"""
        try:
            # Look for the address after "Location Found:" or "Address:"
            if "Location Found:" in location_info:
                address_line = location_info.split("Location Found:")[1].split("\n")[0].strip()
                return address_line
            elif "Address:" in location_info:
                address_line = location_info.split("Address:")[1].split("\n")[0].strip()
                return address_line
            else:
                # Try to find the first line that looks like an address
                lines = location_info.split("\n")
                for line in lines:
                    if any(word in line.lower() for word in ["ave", "st", "dr", "blvd", "rd", "way"]):
                        return line.strip()
                return None
        except Exception as e:
            return None
    
    def get_directions(self, origin: str, destination: str, mode: str = "driving") -> str:
        """Get directions between two locations"""
        try:
            # Get directions between the two locations
            directions = self.gmaps.directions(origin, destination, mode=mode)
            
            if not directions:
                return f"I couldn't get directions from {origin} to {destination}. Please check the location names."
            
            route = directions[0]['legs'][0]
            distance = route['distance']['text']
            duration = route['duration']['text']
            
            info = f"🗺️ **Directions from {origin} to {destination}**\n"
            info += f"Mode: {mode.title()}\n"
            info += f"Distance: {distance}\n"
            info += f"Duration: {duration}\n\n"
            
            # Add step-by-step directions (first 5 steps)
            steps = route['steps'][:5]
            info += "**Step-by-step directions:**\n"
            for i, step in enumerate(steps, 1):
                instruction = step['html_instructions'].replace('<b>', '').replace('</b>', '')
                info += f"{i}. {instruction}\n"
            
            if len(route['steps']) > 5:
                info += f"... and {len(route['steps']) - 5} more steps\n"
            
            return info
                
        except Exception as e:
            return f"I encountered an error getting directions: {str(e)}"
    
    def get_distance_and_time(self, origin: str, destination: str, mode: str = "driving") -> str:
        """Get distance and travel time between two locations"""
        try:
            # Get directions to extract distance and time
            directions = self.gmaps.directions(origin, destination, mode=mode)
            
            if not directions:
                return f"I couldn't get distance information from {origin} to {destination}. Please check the location names."
            
            route = directions[0]['legs'][0]
            distance = route['distance']['text']
            duration = route['duration']['text']
            
            # Format the response
            info = f"📍 **Distance and Travel Time**\n"
            info += f"From: {origin}\n"
            info += f"To: {destination}\n"
            info += f"Mode: {mode.title()}\n"
            info += f"Distance: {distance}\n"
            info += f"Travel Time: {duration}\n"
            
            return info
                
        except Exception as e:
            return f"I encountered an error getting distance information: {str(e)}"
    
    def extract_locations_from_distance_query(self, query: str) -> tuple:
        """Extract origin and destination from distance/time queries"""
        query_lower = query.lower()
        
        # Common patterns for distance/time queries
        patterns = [
            r'from\s+(.+?)\s+to\s+(.+)',
            r'between\s+(.+?)\s+and\s+(.+)',
            r'(.+?)\s+to\s+(.+)',
            r'(.+?)\s+and\s+(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                origin = match.group(1).strip()
                destination = match.group(2).strip()
                return origin, destination
        
        # If no pattern matches, try to extract from common phrases
        if 'from' in query_lower and 'to' in query_lower:
            parts = query_lower.split('from')[1].split('to')
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        return None, None
    
    
    def chat(self, user_message: str) -> str:
        """Process user message and return AI response"""
        try:
            # Use intent classifier to determine the type of query
            intent, confidence = self.intent_classifier.classify_intent(user_message)
            
            # Initialize variables for location intent
            maps_link = None
            
            if intent == 'distance_time':
                # Extract transportation mode
                mode = self.extract_transportation_mode(user_message)
                
                # Extract origin and destination from the query
                origin, destination = self.extract_locations_from_distance_query(user_message)
                
                if origin and destination:
                    # Get addresses for both locations first using the same method as location queries
                    origin_info = self.get_location_address(origin)
                    destination_info = self.get_location_address(destination)
                    
                    # Extract addresses for distance calculation
                    origin_address = self.extract_address_from_info(origin_info)
                    destination_address = self.extract_address_from_info(destination_info)
                    
                    if origin_address and destination_address:
                        # Get distance and time information
                        distance_info = self.get_distance_and_time(origin_address, destination_address, mode)
                        maps_info = f"Origin: {origin_info}\n\nDestination: {destination_info}\n\n{distance_info}"
                    else:
                        maps_info = "I couldn't find one or both of the locations. Please try more specific location names."
                else:
                    maps_info = "I couldn't extract the locations from your query. Please specify both locations clearly, for example: 'how far is it from tarkington hall to hawkins hall'"
                
                # For distance/time queries, use OpenAI to format the Google Maps data conversationally
                # while ensuring we use the accurate data
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "system", "content": f"Here is the Google Maps distance and time information:\n\n{maps_info}"},
                    {"role": "user", "content": user_message}
                ]
                
                # Get response from OpenAI for conversational formatting
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            elif intent == 'directions':
                # Extract transportation mode
                mode = self.extract_transportation_mode(user_message)
                
                # For directions, we need to get addresses from Google Maps first
                if "from" in user_message.lower() and "to" in user_message.lower():
                    # Try to extract origin and destination from the message
                    parts = user_message.lower().split("from")[1].split("to")
                    if len(parts) == 2:
                        origin_query = parts[0].strip()
                        destination_query = parts[1].strip()
                        
                        # Get addresses for both locations
                        origin_info = self.get_location_address(origin_query)
                        destination_info = self.get_location_address(destination_query)
                        
                        # Get directions between the addresses
                        origin_address = self.extract_address_from_info(origin_info)
                        destination_address = self.extract_address_from_info(destination_info)
                        
                        if origin_address and destination_address:
                            directions_info = self.get_directions(origin_address, destination_address, mode)
                            maps_info = f"Origin: {origin_info}\n\nDestination: {destination_info}\n\nDirections:\n{directions_info}"
                        else:
                            maps_info = "I couldn't find one or both of the locations. Please try more specific location names."
                    else:
                        maps_info = "Please specify both origin and destination. For example: 'directions from Purdue University to Indianapolis Airport'"
                else:
                    # Assume they want directions from Purdue to the mentioned location
                    destination_query = user_message.replace("directions", "").replace("how to get to", "").replace("how do i get to", "").strip()
                    
                    # Get destination address
                    destination_info = self.get_location_address(destination_query)
                    destination_address = self.extract_address_from_info(destination_info)
                    
                    if destination_address:
                        directions_info = self.get_directions("Purdue University West Lafayette Indiana", destination_address, mode)
                        maps_info = f"Destination: {destination_info}\n\nDirections from Purdue University:\n{directions_info}"
                    else:
                        maps_info = f"I couldn't find the destination location. Here's what I found: {destination_info}"
                
                # Prepare messages for OpenAI with Google Maps context
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "system", "content": f"Here is the Google Maps directions information:\n\n{maps_info}"},
                    {"role": "user", "content": user_message}
                ]
            elif intent == 'location':
                # Get Google Maps data first
                maps_info = self.get_location_address(user_message)
                
                # Extract the address and coordinates for OpenAI processing
                address = self.extract_address_from_info(maps_info)
                if not address:
                    return maps_info  # Return raw Google Maps data if we can't extract address
                
                # Get Google Maps link
                maps_link = self.get_google_maps_link(user_message)
                
                # Prepare messages for OpenAI with Google Maps context
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "system", "content": f"Here is the Google Maps location information:\n\nAddress: {address}\n\nPresent this information conversationally and helpfully."},
                    {"role": "user", "content": user_message}
                ]
            else:
                # General chat without location context
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ]
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            openai_response = response.choices[0].message.content
            
            # For location intent, append Google Maps link
            if intent == 'location' and maps_link:
                return f"{openai_response}\n\n🗺️ [Open in Google Maps]({maps_link})"
            
            return openai_response
            
        except Exception as e:
            return f"I'm sorry, I encountered an error: {str(e)}. Please check your API keys and try again."

def main():
    """Main function for the chatbot"""
    print("🚂 Welcome to PurdueAI! Your campus assistant.")
    print("Ask me anything about Purdue University!")
    print("Type 'quit' to exit.\n")
    
    # Check if API keys are set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: Please set your OPENAI_API_KEY in the .env file")
        print("Create a .env file with: OPENAI_API_KEY=your_api_key_here")
        return
    
    if not os.getenv('GOOGLE_MAPS_API_KEY'):
        print("❌ Error: Please set your GOOGLE_MAPS_API_KEY in the .env file")
        print("Add to .env file: GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here")
        return
    
    ai = PurdueAI()
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye! Boiler Up! 🚂")
            break
        
        if not user_input:
            continue
            
        response = ai.chat(user_input)
        print(f"PurdueAI: {response}\n")

if __name__ == "__main__":
    main()
