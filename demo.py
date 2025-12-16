import requests
import json

# --- Configuration ---
# You need to obtain an API key from Tally's developer portal after signing in.
TALLY_API_KEY = "d560c938af2e7c9db2f9be39a7f64885fd86e459d1383f24a1e68d97a1905ebe"  # Replace with your actual key
TALLY_API_ENDPOINT = "https://api.tally.xyz/query" 
AAVE_ORG_SLUG = "aave"
LIMIT = 1000 # Number of results to fetch in this single API call (max is typically 1000)

# --- GraphQL Query String ---
# This query requests delegation events for the Aave organization.
# It selects the delegator, the old delegate, the new delegate, and the timestamp.
QUERY = """
query AaveDelegationHistory($orgSlug: String!, $pagination: PaginationInput!) {
  delegationEvents(
    input: {
      organization: $orgSlug
      pagination: $pagination
    }
  ) {
    nodes {
      blockTimestamp
      delegator {
        address
      }
      fromDelegate {
        address
      }
      toDelegate {
        address
      }
    }
    pageInfo {
      hasNextPage
      lastCursor
    }
  }
}
"""

# --- Variables for the Query ---
# Defines the organization and the pagination settings for the first page.
VARIABLES = {
    "orgSlug": AAVE_ORG_SLUG,
    "pagination": {
        "limit": LIMIT,
        "cursor": None  # Starting from the beginning
    }
}

# --- Request Headers ---
# The API key must be included in the header for authentication.
HEADERS = {
    "Content-Type": "application/json",
    "Api-Key": TALLY_API_KEY
}

# --- Execute the API Call ---
def fetch_aave_delegations():
    """
    Executes the single API call to Tally's GraphQL endpoint.
    """
    try:
        # Construct the payload
        payload = {
            'query': QUERY,
            'variables': VARIABLES
        }

        # Send the POST request
        response = requests.post(
            TALLY_API_ENDPOINT,
            headers=HEADERS,
            data=json.dumps(payload)
        )
        
        # Raise an exception for bad status codes
        response.raise_for_status()

        data = response.json()
        
        # Check for GraphQL errors
        if 'errors' in data:
            print("--- GraphQL Errors Found ---")
            for error in data['errors']:
                print(error)
            return None

        # Process the successful result
        events = data['data']['delegationEvents']['nodes']
        page_info = data['data']['delegationEvents']['pageInfo']
        
        print(f"--- Successfully Retrieved {len(events)} Delegation Events ---")
        
        # Display the first 5 events as an example
        for i, event in enumerate(events[:5]):
            print(f"\nEvent #{i+1}")
            print(f"  Timestamp: {event['blockTimestamp']}")
            print(f"  Delegator: {event['delegator']['address']}")
            print(f"  FROM: {event['fromDelegate']['address']} (Previous Delegate)")
            print(f"  TO:   {event['toDelegate']['address']} (New Delegate)")

        print("\n--- Pagination Info ---")
        print(f"Has Next Page: {page_info['hasNextPage']}")
        print(f"Last Cursor (for next page): {page_info['lastCursor']}")
        
        return events

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    fetch_aave_delegations()