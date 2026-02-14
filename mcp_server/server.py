from pathlib import Path

from mcp.server.fastmcp import FastMCP

from models.user_info import UserSearchRequest, UserCreate, UserUpdate
from user_client import UserClient

# Create FastMCP instance
mcp = FastMCP(
    name="users-management-mcp-server",
    host="0.0.0.0",
    port=8005
)

# Create UserClient instance
user_client = UserClient()


# ==================== TOOLS ====================

@mcp.tool()
async def get_user_by_id(user_id: int) -> str:
    """
    Retrieves a user by their unique ID from the user database.
    Returns detailed user information including profile, contact details, and preferences.
    """
    return await user_client.get_user(user_id)


@mcp.tool()
async def delete_user(user_id: int) -> str:
    """
    Deletes a user from the database by their unique ID.
    This action is permanent and cannot be undone.
    """
    return await user_client.delete_user(user_id)


@mcp.tool()
async def search_user(search_request: UserSearchRequest) -> str:
    """
    Searches for users in the database using flexible filters.
    Supports partial matching on name, surname, and email.
    Can combine multiple criteria for more precise results.
    """
    return await user_client.search_users(
        name=search_request.name,
        surname=search_request.surname,
        email=search_request.email,
        gender=search_request.gender
    )


@mcp.tool()
async def add_user(user_data: UserCreate) -> str:
    """
    Creates a new user in the database with complete profile information.
    Requires name, surname, email, and about_me. Other fields are optional.
    Email must be unique across all users.
    """
    return await user_client.add_user(user_data)


@mcp.tool()
async def update_user(user_id: int, user_data: UserUpdate) -> str:
    """
    Updates an existing user's information in the database.
    Only provided fields will be updated; others remain unchanged.
    Useful for partial updates without needing to resend all user data.
    """
    return await user_client.update_user(user_id, user_data)

# ==================== MCP RESOURCES ====================

@mcp.resource(uri="users-management://flow-diagram", mime_type="image/png")
async def get_flow_diagram() -> bytes:
    """
    Provides a visual flow diagram showing the Swagger API endpoints
    of the User Management Service. This diagram illustrates all available
    REST endpoints, their HTTP methods, and the overall API structure.
    """
    flow_diagram_path = Path(__file__).parent / "flow.png"
    return flow_diagram_path.read_bytes()


# ==================== MCP PROMPTS ====================

@mcp.prompt()
async def search_guidance() -> str:
    """
    Helps users formulate effective search queries for the user database.
    Provides guidance on available search parameters, strategies, and best practices.
    """
    return """
You are helping users search through a dynamic user database. The database contains 
realistic synthetic user profiles with the following searchable fields:

## Available Search Parameters
- **name**: First name (partial matching, case-insensitive)
- **surname**: Last name (partial matching, case-insensitive)  
- **email**: Email address (partial matching, case-insensitive)
- **gender**: Exact match (male, female, other, prefer_not_to_say)

## Search Strategy Guidance

### For Name Searches
- Use partial names: "john" finds John, Johnny, Johnson, etc.
- Try common variations: "mike" vs "michael", "liz" vs "elizabeth"
- Consider cultural name variations

### For Email Searches  
- Search by domain: "gmail" for all Gmail users
- Search by name patterns: "john" for emails containing john
- Use company names to find business emails

### For Demographic Analysis
- Combine gender with other criteria for targeted searches
- Use broad searches first, then narrow down

### Effective Search Combinations
- Name + Gender: Find specific demographic segments
- Email domain + Surname: Find business contacts
- Partial names: Cast wider nets for common names

## Example Search Patterns
```
"Find all Johns" → name="john"
"Gmail users named Smith" → email="gmail" + surname="smith"  
"Female users with company emails" → gender="female" + email="company"
"Users with Johnson surname" → surname="johnson"
```

## Tips for Better Results
1. Start broad, then narrow down
2. Try variations of names (John vs Johnny)
3. Use partial matches creatively
4. Combine multiple criteria for precision
5. Remember searches are case-insensitive

When helping users search, suggest multiple search strategies and explain 
why certain approaches might be more effective for their goals.
"""


@mcp.prompt()
async def user_creation_guidance() -> str:
    """
    Guides users in creating realistic and complete user profiles.
    Provides best practices for all fields, validation requirements, and tips for
    generating authentic biographies and demographic information.
    """
    return """
You are helping create realistic user profiles for the system. Follow these guidelines 
to ensure data consistency and realism.

## Required Fields
- **name**: 2-50 characters, letters only, culturally appropriate
- **surname**: 2-50 characters, letters only  
- **email**: Valid format, must be unique in system
- **about_me**: Rich, realistic biography (see guidelines below)

## Optional Fields Best Practices
- **phone**: Use E.164 format (+1234567890) when possible
- **date_of_birth**: YYYY-MM-DD format, realistic ages (18-80)
- **gender**: Use standard values (male, female, other, prefer_not_to_say)
- **company**: Real-sounding company names
- **salary**: $30,000-$200,000 range for employed individuals

## Address Guidelines
Provide complete, realistic addresses:
- **country**: Full country names
- **city**: Actual city names  
- **street**: Realistic street addresses
- **flat_house**: Apartment/unit format (Apt 123, Unit 5B, Suite 200)

## Credit Card Guidelines  
Generate realistic but non-functional card data:
- **num**: 16 digits formatted as XXXX-XXXX-XXXX-XXXX
- **cvv**: 3 digits (000-999)
- **exp_date**: MM/YYYY format, future dates only

## Biography Creation ("about_me")
Create engaging, realistic biographies that include:

### Personality Elements
- 1-3 personality traits (curious, adventurous, analytical, etc.)
- Authentic voice and writing style
- Cultural and demographic appropriateness

### Interests & Hobbies  
- 2-4 specific hobbies or activities
- 1-3 broader interests or passion areas
- 1-2 life goals or aspirations

### Biography Templates
Use varied narrative structures:
- "I'm a [trait] person who loves [hobbies]..."
- "When I'm not working, you can find me [activity]..."  
- "Life is all about balance for me. I enjoy [interests]..."
- "As someone who's [trait], I find great joy in [hobby]..."

## Data Validation Reminders
- Email uniqueness is enforced (check existing users)
- Phone numbers should follow consistent formatting
- Date formats must be exact (YYYY-MM-DD)
- Credit card expiration dates must be in the future
- Salary values should be realistic for the demographic

## Cultural Sensitivity
- Match names to appropriate cultural backgrounds
- Consider regional variations in address formats
- Use realistic company names for the user's location
- Ensure hobbies and interests are culturally appropriate

When creating profiles, aim for diversity in:
- Geographic representation
- Age distribution  
- Interest variety
- Socioeconomic backgrounds
- Cultural backgrounds
"""


if __name__ == "__main__":
    # Run server with streamable HTTP transport
    mcp.run(transport="streamable-http")
