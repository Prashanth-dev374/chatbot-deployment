import requests

# Your API key
API_KEY = "9ec9285debec43badb135f04d9b7ceaf48c9f9cd4be63a36fa5f6b9444119e0f"

# Search parameters
params = {
    "q": "latest electric cars in India",  # Your search query
    "api_key": API_KEY,
    "engine": "google"
}

try:
    # Make request to SerpApi
    response = requests.get("https://serpapi.com/search", params=params)
    response.raise_for_status()
    data = response.json()

    # Print top 5 results
    if "organic_results" in data:
        print("\nTop 5 Google Search Results:\n")
        for result in data["organic_results"][:5]:
            print("🔹 Title:", result.get("title"))
            print("🔗 URL:", result.get("link"))
            print()
    else:
        print("❌ No organic results found. Check your API usage or query.")
except requests.exceptions.RequestException as e:
    print("🚫 Request failed:", e)
