from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# It's better practice to load sensitive keys from environment variables
# For now, you can keep them directly here, but consider using os.environ.get()
# when deploying for security.
API_KEY = "Your_Api"
# IMPORTANT: Replace "e4b2d939f26554ccf" with your actual CSE ID.
CSE_ID = "ID" 

# Number of results per page for Google Custom Search API
RESULTS_PER_PAGE = 10 

@app.route("/", methods=["GET", "POST"])
def search():
    query = request.form.get("query", "") # From POST for initial search
    if not query:
        query = request.args.get("query", "") # From GET for pagination links
    
    start_index_str = request.args.get("start", "1") # Get start index for pagination
    try:
        start_index = int(start_index_str)
        if start_index < 1: # Ensure start index is at least 1
            start_index = 1
    except ValueError:
        start_index = 1 # Default to first page if invalid

    results = []
    api_error = None
    user_message = None
    response = {} # Initialize response to an empty dictionary to prevent UnboundLocalError

    if query:
        # Construct the API URL using the defined API_KEY and CSE_ID variables
        # Add 'start' parameter for pagination
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CSE_ID}&start={start_index}"
        
        try:
            response = requests.get(url).json()
            
            if "items" in response:
                results = [
                    {"title": item["title"], "snippet": item["snippet"], "url": item["link"]}
                    for item in response["items"]
                ]
            elif "error" in response:
                # Capture specific API errors from Google
                api_error = response["error"].get("message", "An unknown API error occurred.")
                print(f"API Error: {api_error}")
            else:
                user_message = "No search results found. Please try a different query."
                print(f"No search results found for query: '{query}'")

        except requests.exceptions.RequestException as e:
            api_error = f"Failed to connect to the search service. Please check your internet connection. ({e})"
            print(f"Error making API request: {e}")
            response = {} # Ensure response is reset to empty if request fails
        except ValueError:
            api_error = "Received an invalid response from the search service."
            print(f"Error parsing JSON response for query '{query}': {response.text}")
            response = {} # Ensure response is reset to empty if parsing fails

    # Calculate pagination links
    prev_start = None
    if start_index > 1:
        prev_start = start_index - RESULTS_PER_PAGE
        if prev_start < 1: # Ensure it doesn't go below 1
            prev_start = 1

    next_start = None
    # Google API's 'queries' object contains 'nextPage' if there are more results
    # Added check for 'response' to ensure it's not empty before accessing 'queries'
    if response and "queries" in response and "nextPage" in response["queries"]:
        for page_info in response["queries"]["nextPage"]:
            if "startIndex" in page_info:
                next_start = page_info["startIndex"]
                break
    
    # If no next page info from API, but we have results, assume next page is possible
    # This is a fallback if 'nextPage' isn't always reliable (though it usually is)
    # if not next_start and len(results) == RESULTS_PER_PAGE:
    #     next_start = start_index + RESULTS_PER_PAGE

    return render_template(
        "index.html", 
        query=query, 
        results=results, 
        start=start_index, # Pass current start index for page number calculation
        prev_start=prev_start, 
        next_start=next_start,
        api_error=api_error,
        user_message=user_message # For general messages like "No results found"
    )

@app.route("/suggest", methods=["GET"])
def suggest():
    query = request.args.get("q", "").lower()
    
    # --- Basic Hardcoded Suggestions (MVP) ---
    # In a real system, this would query a dedicated suggestion index
    # or analyze popular search terms.
    all_suggestions = [
        "what is chatgpt", "chatgpt login", "chatgpt plus", "ai tools",
        "india news", "indian economy", "latest technology in india",
        "bharat history", "indian culture", "cricket live score",
        "new delhi weather", "mumbai stock market", "bangalore startups"
    ]
    
    # Filter suggestions based on the user's query
    filtered_suggestions = [s for s in all_suggestions if query in s.lower()]
    
    # Return suggestions as JSON
    return jsonify(filtered_suggestions[:5]) # Limit to top 5 suggestions

if __name__ == "__main__":

    app.run(debug=True)
