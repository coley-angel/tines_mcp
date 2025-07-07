#!/usr/bin/env python3
"""
Tines API MCP Server Main Entry Point

This MCP server provides tools for reading and editing stories in Tines
using the official Tines REST API.
"""
import sys
import logging
from dotenv import load_dotenv
import os
from mcp.server.fastmcp import FastMCP
import requests
from typing import Optional, List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except Exception as e:
    logger.warning(f"Failed to load .env file: {e}. Using existing environment variables.")

# Initialize FastMCP
mcp = FastMCP("TinesMCP")

# Setup base configuration
TOKEN = os.getenv("TINES_API_TOKEN")
if not TOKEN:
    logger.error("TINES_API_TOKEN environment variable is not set")
    logger.error("Please set your Tines API token in the environment or .env file")
    logger.error("Example: TINES_API_TOKEN=your_api_token_here")
    raise ValueError("TINES_API_TOKEN environment variable is not set")

# Get the base URL from env, default to tines.com but user should provide their tenant domain
BASE_URL = os.getenv("TINES_API_URL")
if not BASE_URL:
    logger.error("TINES_API_URL environment variable is not set")
    logger.error("Please set your Tines API URL in the environment or .env file")
    logger.error("Example: TINES_API_URL=https://your-tenant.tines.com/api/v1")
    raise ValueError("TINES_API_URL environment variable is not set. Use format: https://your-tenant.tines.com/api/v1")

logger.info(f"Tines MCP Server initialized with API URL: {BASE_URL}")
logger.info("API Token loaded successfully")


def make_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Make an authenticated request to the Tines API"""
    url = f"{BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Debug logging
    logger.info(f"Making {method} request to: {url}")
    if data:
        logger.info(f"Request data: {data}")
    if params:
        logger.info(f"Request params: {params}")
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        )
        
        # Log response details before checking status
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Try to get response text for debugging
        try:
            response_text = response.text
            logger.info(f"Response body: {response_text}")
        except Exception:
            logger.info("Could not read response body")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error {response.status_code}: {e}")
        logger.error(f"Response body: {response.text}")
        # Try to parse error response as JSON
        try:
            error_data = response.json()
            logger.error(f"Error details: {error_data}")
        except Exception:
            logger.error("Could not parse error response as JSON")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise


def list_stories(
    team_id: Optional[int] = None,
    folder_id: Optional[int] = None,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    filter: Optional[str] = None,
    order: Optional[str] = None
) -> Dict[str, Any]:
    """List all stories from Tines.
    
    Args:
        team_id: Return stories belonging to this team
        folder_id: Return stories in this folder
        per_page: Number of results per page (max 500)
        page: Page number to return
        tags: Comma separated list of tag names to filter by
        search: Search string against story name
        filter: Filter by: SEND_TO_STORY_ENABLED, HIGH_PRIORITY, API_ENABLED, 
                PUBLISHED, FAVORITE, CHANGE_CONTROL_ENABLED, DISABLED, LOCKED
        order: Order by: NAME, NAME_DESC, RECENTLY_EDITED, LEAST_RECENTLY_EDITED,
               ACTION_COUNT_ASC, ACTION_COUNT_DESC
    
    Returns:
        Dict containing stories array and pagination metadata
    """
    params = {}
    if team_id is not None:
        params['team_id'] = team_id
    if folder_id is not None:
        params['folder_id'] = folder_id
    if per_page is not None:
        params['per_page'] = min(per_page, 500)  # API max is 500
    if page is not None:
        params['page'] = page
    if tags:
        params['tags'] = tags
    if search:
        params['search'] = search
    if filter:
        params['filter'] = filter
    if order:
        params['order'] = order
    
    return make_request("GET", "stories", params=params)


def get_story(
    story_id: int,
    story_mode: Optional[str] = None,
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """Get a specific story from Tines.
    
    Args:
        story_id: ID of the story to retrieve
        story_mode: Mode (TEST or LIVE) of story to retrieve
        draft_id: ID of the draft to retrieve
    
    Returns:
        Dict containing the complete story details
    """
    params = {}
    if story_mode:
        params['story_mode'] = story_mode
    if draft_id is not None:
        params['draft_id'] = draft_id
    
    return make_request("GET", f"stories/{story_id}", params=params)


def create_story(
    team_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    keep_events_for: Optional[int] = None,
    folder_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    disabled: Optional[bool] = None,
    priority: Optional[bool] = None
) -> Dict[str, Any]:
    """Create a new story in Tines.
    
    Args:
        team_id: ID of team to which the story should be added
        name: The story name
        description: A user-defined description of the story
        keep_events_for: Event retention period in seconds
                        (3600=1h, 21600=6h, 86400=1d, 259200=3d, 604800=7d,
                         1209600=14d, 2592000=30d, 5184000=60d, 7776000=90d,
                         15552000=180d, 31536000=365d)
        folder_id: ID of folder to add the story to
        tags: Array of strings to classify the story
        disabled: Whether the story is disabled (default: false)
        priority: Whether this is a high priority story (default: false)
    
    Returns:
        Dict containing the created story details
    """
    story_data = {"team_id": team_id}
    
    if name is not None:
        story_data['name'] = name
    if description is not None:
        story_data['description'] = description
    if keep_events_for is not None:
        story_data['keep_events_for'] = keep_events_for
    if folder_id is not None:
        story_data['folder_id'] = folder_id
    if tags is not None:
        story_data['tags'] = tags
    if disabled is not None:
        story_data['disabled'] = disabled
    if priority is not None:
        story_data['priority'] = priority
    
    return make_request("POST", "stories", data=story_data)


def update_story(
    story_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    add_tag_names: Optional[List[str]] = None,
    remove_tag_names: Optional[List[str]] = None,
    keep_events_for: Optional[int] = None,
    disabled: Optional[bool] = None,
    locked: Optional[bool] = None,
    priority: Optional[bool] = None,
    send_to_story_access_source: Optional[str] = None,
    send_to_story_access: Optional[str] = None,
    shared_team_slugs: Optional[List[str]] = None,
    send_to_story_skill_use_requires_confirmation: Optional[bool] = None,
    webhook_api_enabled: Optional[bool] = None,
    team_id: Optional[int] = None,
    folder_id: Optional[int] = None,
    change_control_enabled: Optional[bool] = None,
    draft_id: Optional[int] = None,
    monitor_failures: Optional[bool] = None,
    entry_action_id: Optional[int] = None,
    exit_action_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Update a story in Tines.
    
    Args:
        story_id: The ID of the story to update
        name: The story name
        description: A user-defined description of the story
        add_tag_names: Array of tag names to add to the story
        remove_tag_names: Array of tag names to remove from the story
        keep_events_for: Event retention period in seconds
        disabled: Whether the story is disabled from running
        locked: Whether the story is locked, preventing edits
        priority: Whether story runs with high priority
        send_to_story_access_source: STS, STS_AND_WORKBENCH, WORKBENCH or OFF
        send_to_story_access: TEAM, GLOBAL, SPECIFIC_TEAMS
        shared_team_slugs: List of teams' slugs that can send to this story
        send_to_story_skill_use_requires_confirmation: Whether workbench should ask for confirmation
        webhook_api_enabled: Whether Webhook API is enabled
        team_id: The ID of the team to move the story to
        folder_id: The ID of the folder to move the story to
        change_control_enabled: Whether Change Control is enabled
        draft_id: The ID of the draft to update
        monitor_failures: Whether monitor failures is enabled on the story
        entry_action_id: The ID of the entry action for send to story (webhook)
        exit_action_ids: Array of IDs for exit actions (event transforms)
    
    Returns:
        Dict containing the updated story details
    """
    update_data = {}
    
    if name is not None:
        update_data['name'] = name
    if description is not None:
        update_data['description'] = description
    if add_tag_names is not None:
        update_data['add_tag_names'] = add_tag_names
    if remove_tag_names is not None:
        update_data['remove_tag_names'] = remove_tag_names
    if keep_events_for is not None:
        update_data['keep_events_for'] = keep_events_for
    if disabled is not None:
        update_data['disabled'] = disabled
    if locked is not None:
        update_data['locked'] = locked
    if priority is not None:
        update_data['priority'] = priority
    if send_to_story_access_source is not None:
        update_data['send_to_story_access_source'] = send_to_story_access_source
    if send_to_story_access is not None:
        update_data['send_to_story_access'] = send_to_story_access
    if shared_team_slugs is not None:
        update_data['shared_team_slugs'] = shared_team_slugs
    if send_to_story_skill_use_requires_confirmation is not None:
        update_data['send_to_story_skill_use_requires_confirmation'] = send_to_story_skill_use_requires_confirmation
    if webhook_api_enabled is not None:
        update_data['webhook_api_enabled'] = webhook_api_enabled
    if team_id is not None:
        update_data['team_id'] = team_id
    if folder_id is not None:
        update_data['folder_id'] = folder_id
    if change_control_enabled is not None:
        update_data['change_control_enabled'] = change_control_enabled
    if draft_id is not None:
        update_data['draft_id'] = draft_id
    if monitor_failures is not None:
        update_data['monitor_failures'] = monitor_failures
    if entry_action_id is not None:
        update_data['entry_action_id'] = entry_action_id
    if exit_action_ids is not None:
        update_data['exit_action_ids'] = exit_action_ids
    
    return make_request("PUT", f"stories/{story_id}", data=update_data)


def search_stories(
    query: str,
    team_id: Optional[int] = None,
    per_page: Optional[int] = 20
) -> Dict[str, Any]:
    """Search for stories by name.
    
    Args:
        query: Search string against story name
        team_id: Limit search to specific team
        per_page: Number of results per page
    
    Returns:
        Dict containing matching stories and pagination metadata
    """
    return list_stories(
        team_id=team_id,
        search=query,
        per_page=per_page
    )


def get_high_priority_stories(
    team_id: Optional[int] = None,
    per_page: Optional[int] = 20
) -> Dict[str, Any]:
    """Get all high priority stories.
    
    Args:
        team_id: Limit to specific team
        per_page: Number of results per page
    
    Returns:
        Dict containing high priority stories and pagination metadata
    """
    return list_stories(
        team_id=team_id,
        filter="HIGH_PRIORITY",
        per_page=per_page
    )


def get_disabled_stories(
    team_id: Optional[int] = None,
    per_page: Optional[int] = 20
) -> Dict[str, Any]:
    """Get all disabled stories.
    
    Args:
        team_id: Limit to specific team
        per_page: Number of results per page
    
    Returns:
        Dict containing disabled stories and pagination metadata
    """
    return list_stories(
        team_id=team_id,
        filter="DISABLED",
        per_page=per_page
    )


# Action Management Functions

def get_story_actions(
    story_id: int, draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """Get all actions from a specific story.
    
    Args:
        story_id: ID of the story to get actions from
        draft_id: ID of the draft to get actions from (optional)
    
    Returns:
        Dict containing the story with all its actions
    """
    params = {"story_id": story_id}
    if draft_id:
        params["draft_id"] = draft_id
    
    # Convert params to query string
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return make_request("GET", f"agents?{query_string}")


def create_action(
    story_id: int,
    action_type: str,
    name: str,
    options: Optional[Dict[str, Any]] = None,
    position: Optional[Dict[str, Any]] = None,
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new action in a story.
    
    Args:
        story_id: ID of the story to add the action to
        action_type: Type of action (supported types):
                    'Agents::EmailAgent'
                    'Agents::EventTransformationAgent'
                    'Agents::HTTPRequestAgent'
                    'Agents::IMAPAgent'
                    'Agents::TriggerAgent'
                    'Agents::WebhookAgent'
                    'Agents::SendToStoryAgent'
                    'Agents::GroupAgent'
                    'Agents::LLMAgent' (AI/LLM actions)
        name: Name for the action
        options: Configuration options for the action
        position: Position coordinates for the action in the story canvas
        draft_id: ID of the draft to add the action to (optional, but required
                 when change control is enabled)
    
    Returns:
        Dict containing the created action details
    """
    data = {
        "type": action_type,
        "name": name,
        "story_id": str(story_id),  # Convert to string per API example
    }
    
    # Add draft_id if provided (required for change control enabled stories)
    if draft_id is not None:
        data["draft_id"] = draft_id
    
    if options:
        data["options"] = options
    
    if position:
        data["position"] = position
    else:
        # Default position
        data["position"] = {"x": 100, "y": 100}
    
    # Use the correct actions endpoint from the curl example
    return make_request("POST", "actions", data=data)


def create_event_transform_action(
    story_id: int,
    name: str,
    draft_id: int,
    mode: str = "message",
    message: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create an Event Transform action in a story.
    
    Args:
        story_id: ID of the story to add the action to
        name: Name for the action
        draft_id: ID of the draft to add the action to (required)
        mode: Transform mode ('message', 'merge', 'implode', 'explode')
        message: Message template for the transformation
        payload: Payload template for the transformation
        position: Position coordinates for the action in the story canvas
    
    Returns:
        Dict containing the created action details
    """
    options = {
        "mode": mode
    }
    
    if message:
        options["message"] = message
    if payload:
        options["payload"] = payload
    
    return create_action(
        story_id=story_id,
        action_type="Agents::EventTransformationAgent",
        name=name,
        options=options,
        position=position,
        draft_id=draft_id
    )


def create_webhook_action(
    story_id: int,
    name: str,
    draft_id: int,
    secret: Optional[str] = None,
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a Webhook action in a story.
    
    Args:
        story_id: ID of the story to add the webhook to
        name: Name for the webhook action
        draft_id: ID of the draft to add the action to (required)
        secret: Optional secret for webhook verification
        position: Position coordinates for the action in the story canvas
    
    Returns:
        Dict containing the created webhook action details
    """
    options = {}
    if secret:
        options["secret"] = secret
    
    return create_action(
        story_id=story_id,
        action_type="Agents::WebhookAgent",
        name=name,
        options=options,
        position=position,
        draft_id=draft_id
    )


def create_email_action(
    story_id: int,
    name: str,
    draft_id: int,
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    content_type: str = "text/html",
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create an Email action in a story.
    
    Args:
        story_id: ID of the story to add the action to
        name: Name for the action
        draft_id: ID of the draft to add the action to (required)
        to: Email recipient(s)
        subject: Email subject
        body: Email body content
        from_email: From email address (optional)
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        content_type: Content type (text/html or text/plain)
        position: Position coordinates for the action in the story canvas
    
    Returns:
        Dict containing the created action details
    """
    options = {
        "to": to,
        "subject": subject,
        "body": body,
        "content_type": content_type
    }
    
    if from_email:
        options["from"] = from_email
    if cc:
        options["cc"] = cc
    if bcc:
        options["bcc"] = bcc
    
    return create_action(
        story_id=story_id,
        action_type="Agents::EmailAgent",
        name=name,
        options=options,
        position=position,
        draft_id=draft_id
    )


def create_imap_action(
    story_id: int,
    name: str,
    draft_id: int,
    host: str,
    username: str,
    password: str,
    port: int = 993,
    ssl: bool = True,
    folder: str = "INBOX",
    conditions: Optional[Dict[str, Any]] = None,
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create an IMAP action in a story for receiving emails.
    
    Args:
        story_id: ID of the story to add the action to
        name: Name for the action
        draft_id: ID of the draft to add the action to (required)
        host: IMAP server hostname
        username: IMAP username
        password: IMAP password
        port: IMAP port (default 993 for SSL)
        ssl: Use SSL connection (default True)
        folder: Email folder to monitor (default INBOX)
        conditions: Email filtering conditions
        position: Position coordinates for the action in the story canvas
    
    Returns:
        Dict containing the created action details
    """
    options = {
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "ssl": ssl,
        "folder": folder
    }
    
    if conditions:
        options["conditions"] = conditions
    
    return create_action(
        story_id=story_id,
        action_type="Agents::IMAPAgent",
        name=name,
        options=options,
        position=position,
        draft_id=draft_id
    )


def create_send_to_story_action(
    story_id: int,
    name: str,
    draft_id: int,
    target_story_id: int,
    payload: Optional[Dict[str, Any]] = None,
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a Send to Story action in a story.
    
    Args:
        story_id: ID of the story to add the action to
        name: Name for the action
        draft_id: ID of the draft to add the action to (required)
        target_story_id: ID of the target story to send events to
        payload: Data payload to send to the target story
        position: Position coordinates for the action in the story canvas
    
    Returns:
        Dict containing the created action details
    """
    options = {
        "story_id": target_story_id
    }
    
    if payload:
        options["payload"] = payload
    
    return create_action(
        story_id=story_id,
        action_type="Agents::SendToStoryAgent",
        name=name,
        options=options,
        position=position,
        draft_id=draft_id
    )


def create_trigger_action(
    story_id: int,
    name: str,
    draft_id: int,
    rules: List[Dict[str, Any]],
    message: Optional[str] = None,
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a Trigger action in a story.
    
    Args:
        story_id: ID of the story to add the action to
        name: Name for the action
        draft_id: ID of the draft to add the action to (required)
        rules: List of trigger rules/conditions
        message: Optional message to include with triggered events
        position: Position coordinates for the action in the story canvas
    
    Returns:
        Dict containing the created action details
    """
    options = {
        "rules": rules
    }
    
    if message:
        options["message"] = message
    
    return create_action(
        story_id=story_id,
        action_type="Agents::TriggerAgent",
        name=name,
        options=options,
        position=position,
        draft_id=draft_id
    )


def create_group_action(
    story_id: int,
    name: str,
    draft_id: int,
    group_story_id: int,
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a Group action in a story.
    
    Args:
        story_id: ID of the story to add the action to
        name: Name for the action
        draft_id: ID of the draft to add the action to (required)
        group_story_id: ID of the story to use as a group
        position: Position coordinates for the action in the story canvas
    
    Returns:
        Dict containing the created action details
    """
    options = {
        "group_story_id": group_story_id
    }
    
    return create_action(
        story_id=story_id,
        action_type="Agents::GroupAgent",
        name=name,
        options=options,
        position=position,
        draft_id=draft_id
    )


def create_llm_action(
    story_id: int,
    name: str,
    prompt: str,
    draft_id: int,
    json_mode: bool = False,
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create an LLM (AI) action in a story.
    
    Args:
        story_id: ID of the story to add the LLM action to
        name: Name for the LLM action
        prompt: The AI prompt to use
        draft_id: ID of the draft to add the action to (required)
        json_mode: Whether to force JSON output (default: False)
        position: Position coordinates for the action in the story canvas
    
    Returns:
        Dict containing the created LLM action details
    """
    options = {
        "prompt": prompt,
        "json_mode": json_mode
    }
    
    return create_action(
        story_id=story_id,
        action_type="Agents::LLMAgent",
        name=name,
        options=options,
        position=position,
        draft_id=draft_id
    )


def update_action(
    story_id: int,
    action_id: int,
    name: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    position: Optional[Dict[str, Any]] = None,
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """Update an existing action in a story.
    
    Args:
        story_id: ID of the story containing the action
        action_id: ID of the action to update
        name: New name for the action
        options: New configuration options for the action
        position: New position coordinates for the action
        draft_id: ID of the draft to update the action in (optional)
    
    Returns:
        Dict containing the updated action details
    """
    data = {}
    
    if name:
        data["name"] = name
    if options:
        data["options"] = options
    if position:
        data["position"] = position
    if draft_id:
        data["draft_id"] = draft_id
    
    return make_request(
        "PUT", f"actions/{action_id}", data=data
    )


def delete_action(story_id: int, action_id: int) -> Dict[str, Any]:
    """Delete an action from a story.
    
    Args:
        story_id: ID of the story containing the action
        action_id: ID of the action to delete
    
    Returns:
        Dict containing the deletion confirmation
    """
    return make_request("DELETE", f"actions/{action_id}")


def connect_actions(
    story_id: int,
    source_action_id: int,
    target_action_id: int,
    source_output: Optional[str] = None,
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """Connect two actions in a story with a link.
    
    Args:
        story_id: ID of the story containing the actions
        source_action_id: ID of the source action
        target_action_id: ID of the target action
        source_output: Specific output from source action (optional)
        draft_id: ID of the draft to perform the connection in (optional)
    
    Returns:
        Dict containing the created link details
    """
    # Get the current target action to preserve existing configuration
    target_action = make_request("GET", f"actions/{target_action_id}")
    
    # Add the source action to the target's source_ids
    current_sources = target_action.get("sources", [])
    if source_action_id not in current_sources:
        current_sources.append(source_action_id)
    
    # Update the target action with new source connection
    data = {
        "source_ids": current_sources
    }
    
    # Add draft_id if provided for draft operations
    if draft_id:
        data["draft_id"] = draft_id
    
    return make_request("PUT", f"actions/{target_action_id}", data=data)


def list_story_drafts(story_id: int) -> Dict[str, Any]:
    """List all drafts for a specific story.
    
    Args:
        story_id: ID of the story to get drafts for
    
    Returns:
        Dict containing the story drafts
    """
    return make_request("GET", f"stories/{story_id}/drafts")


def get_story_draft(story_id: int, draft_id: int) -> Dict[str, Any]:
    """Get a specific draft of a story.
    
    Args:
        story_id: ID of the story
        draft_id: ID of the draft to retrieve
    
    Returns:
        Dict containing the draft details
    """
    return make_request("GET", f"stories/{story_id}/drafts/{draft_id}")


def create_story_draft(story_id: int) -> Dict[str, Any]:
    """Create a new draft for a story by making a minimal change.
    
    Args:
        story_id: ID of the story to create a draft for
    
    Returns:
        Dict containing the created draft details
    """
    # Create a draft by making a minimal change to the story
    # We'll add a tag temporarily to force draft creation
    try:
        make_request("PUT", f"stories/{story_id}", data={
            "add_tag_names": ["draft-creation"]
        })
        # If successful, get the draft that was created
        drafts = list_story_drafts(story_id)
        if drafts.get("drafts"):
            latest_draft = drafts["drafts"][0]  # Get the most recent draft
            # Remove the temporary tag
            make_request("PUT", f"stories/{story_id}", data={
                "remove_tag_names": ["draft-creation"],
                "draft_id": latest_draft["id"]
            })
            return latest_draft
        else:
            raise ValueError("No draft was created")
    except Exception as e:
        logger.error(f"Failed to create draft: {e}")
        raise


# Notes/Comments Functions
def create_note(
    content: str,
    story_id: Optional[int] = None,
    group_id: Optional[int] = None,
    position: Optional[Dict[str, Any]] = None,
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a note/comment on the storyboard.
    
    Args:
        content: The note content in Markdown format
        story_id: ID of story to add the note to (optional,
                 either story_id or group_id required)
        group_id: ID of group to add the note to (optional,
                 either story_id or group_id required)
        position: XY coordinates for the note position (optional)
        draft_id: ID of the draft to add the note to (optional)
    
    Returns:
        Dict containing the created note details
    """
    if not story_id and not group_id:
        raise ValueError("Either story_id or group_id must be provided")
    
    data = {
        "content": content
    }
    
    if story_id:
        data["story_id"] = story_id
    if group_id:
        data["group_id"] = group_id
    if position:
        data["position"] = position
    else:
        # Default position
        data["position"] = {"x": 0, "y": 0}
    if draft_id:
        data["draft_id"] = draft_id
    
    return make_request("POST", "notes", data=data)


def get_note(note_id: int) -> Dict[str, Any]:
    """Get a specific note by ID.
    
    Args:
        note_id: ID of the note to retrieve
    
    Returns:
        Dict containing the note details
    """
    return make_request("GET", f"notes/{note_id}")


def update_note(
    note_id: int,
    content: Optional[str] = None,
    position: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update an existing note.
    
    Args:
        note_id: ID of the note to update
        content: New content for the note in Markdown format (optional)
        position: New XY coordinates for the note position (optional)
    
    Returns:
        Dict containing the updated note details
    """
    data = {}
    
    if content is not None:
        data["content"] = content
    if position is not None:
        data["position"] = position
    
    if not data:
        raise ValueError(
            "At least one of content or position must be provided"
        )
    
    return make_request("PUT", f"notes/{note_id}", data=data)


def list_notes(
    story_id: Optional[int] = None,
    group_id: Optional[int] = None,
    team_id: Optional[int] = None,
    mode: Optional[str] = None,
    draft_id: Optional[int] = None,
    per_page: Optional[int] = None,
    page: Optional[int] = None
) -> Dict[str, Any]:
    """List notes/comments.
    
    Args:
        story_id: List notes for a specific story (optional)
        group_id: List notes for a specific group (optional)
        team_id: List notes for a specific team (optional)
        mode: Story mode ('LIVE' or 'TEST',
              must be used with story_id) (optional)
        draft_id: List notes for a specific draft (optional)
        per_page: Number of results per page (optional)
        page: Page number to return (optional)
    
    Returns:
        Dict containing notes list and pagination metadata
    """
    params = {}
    
    if story_id is not None:
        params["story_id"] = story_id
    if group_id is not None:
        params["group_id"] = group_id
    if team_id is not None:
        params["team_id"] = team_id
    if mode is not None:
        params["mode"] = mode
    if draft_id is not None:
        params["draft_id"] = draft_id
    if per_page is not None:
        params["per_page"] = per_page
    if page is not None:
        params["page"] = page
    
    # Build query string
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    endpoint = "notes"
    if query_string:
        endpoint += f"?{query_string}"
    
    return make_request("GET", endpoint)


def delete_note(note_id: int) -> Dict[str, Any]:
    """Delete a note/comment.
    
    Args:
        note_id: ID of the note to delete
    
    Returns:
        Empty dict (204 status code response)
    """
    make_request("DELETE", f"notes/{note_id}")
    # DELETE returns 204 with empty response, so return success indicator
    return {"deleted": True, "note_id": note_id}


def register_tools():
    """Register all Tines API tools with the MCP server"""
    # Story management tools
    mcp.add_tool(list_stories)
    mcp.add_tool(get_story)
    mcp.add_tool(create_story)
    mcp.add_tool(update_story)
    mcp.add_tool(search_stories)
    mcp.add_tool(get_high_priority_stories)
    mcp.add_tool(get_disabled_stories)
    
    # Story draft tools
    mcp.add_tool(list_story_drafts)
    mcp.add_tool(get_story_draft)
    mcp.add_tool(create_story_draft)
    mcp.add_tool(create_story_draft)
    
    # Action management tools
    mcp.add_tool(get_story_actions)
    mcp.add_tool(create_action)
    mcp.add_tool(create_llm_action)
    mcp.add_tool(create_event_transform_action)
    mcp.add_tool(create_webhook_action)
    mcp.add_tool(create_email_action)
    mcp.add_tool(create_imap_action)
    mcp.add_tool(create_send_to_story_action)
    mcp.add_tool(create_trigger_action)
    mcp.add_tool(create_group_action)
    mcp.add_tool(update_action)
    mcp.add_tool(delete_action)
    mcp.add_tool(connect_actions)

    # Notes/Comments tools
    mcp.add_tool(create_note)
    mcp.add_tool(get_note)
    mcp.add_tool(update_note)
    mcp.add_tool(list_notes)
    mcp.add_tool(delete_note)


def debug_endpoint(endpoint: str, method: str = "GET",
                   data: Optional[Dict] = None) -> Dict[str, Any]:
    """Debug function to test API endpoints and capture detailed responses"""
    logger.info("=== DEBUG ENDPOINT TEST ===")
    logger.info(f"Testing: {method} {endpoint}")
    
    try:
        result = make_request(method, endpoint, data=data)
        logger.info(f"SUCCESS: Endpoint {endpoint} is working")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"FAILED: Endpoint {endpoint} failed with error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main function to run the Tines MCP server"""
    logger.info("Starting Tines MCP server...")
    logger.info(f"Using Tines API at: {BASE_URL}")
    register_tools()
    mcp.run()
    logger.info("Tines MCP server completed")


if __name__ == "__main__":
    main()