"""
SuperOps API Client
Handles GraphQL operations for ticket management
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SuperOpsClient:
    """SuperOps GraphQL API client for ticket management"""
    
    def __init__(self):
        self.api_url = os.getenv("SUPEROPS_API_URL")
        self.api_key = os.getenv("SUPEROPS_API_KEY")
        
        if not self.api_url or not self.api_key:
            raise ValueError("SUPEROPS_API_URL and SUPEROPS_API_KEY environment variables are required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info("SuperOps client initialized")
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new support ticket"""
        try:
            mutation = """
            mutation CreateTicket($input: CreateTicketInput!) {
                createTicket(input: $input) {
                    id
                    ticketNumber
                    title
                    description
                    priority
                    status
                    category
                    assignedAgent {
                        id
                        name
                        email
                    }
                    customer {
                        email
                        phone
                    }
                    createdAt
                    estimatedResolutionTime
                    ticketUrl
                }
            }
            """
            
            # Map our data to SuperOps format
            variables = {
                "input": {
                    "title": ticket_data["title"],
                    "description": ticket_data["description"],
                    "priority": ticket_data["priority"].upper(),
                    "category": ticket_data["category"],
                    "customerEmail": ticket_data["customer"]["email"],
                    "customerPhone": ticket_data["customer"].get("phone"),
                    "source": ticket_data["source"].upper(),
                    "tags": ticket_data.get("tags", []),
                    "escalateImmediately": ticket_data.get("escalate_immediately", False)
                }
            }
            
            response_data = await self._execute_graphql(mutation, variables)
            
            if "errors" in response_data:
                raise Exception(f"GraphQL errors: {response_data['errors']}")
            
            ticket = response_data["data"]["createTicket"]
            
            # Format response
            result = {
                "ticket_id": ticket["ticketNumber"],
                "internal_id": ticket["id"],
                "ticket_url": ticket["ticketUrl"],
                "status": ticket["status"].lower(),
                "priority": ticket["priority"].lower(),
                "assigned_agent": ticket["assignedAgent"]["name"] if ticket["assignedAgent"] else None,
                "created_at": ticket["createdAt"],
                "estimated_resolution_time": ticket["estimatedResolutionTime"]
            }
            
            logger.info(f"Ticket created in SuperOps: {result['ticket_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create ticket in SuperOps: {e}")
            raise
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing ticket"""
        try:
            mutation = """
            mutation UpdateTicket($ticketId: ID!, $input: UpdateTicketInput!) {
                updateTicket(ticketId: $ticketId, input: $input) {
                    id
                    ticketNumber
                    status
                    priority
                    assignedAgent {
                        name
                    }
                    updatedAt
                }
            }
            """
            
            variables = {
                "ticketId": ticket_id,
                "input": updates
            }
            
            response_data = await self._execute_graphql(mutation, variables)
            
            if "errors" in response_data:
                raise Exception(f"GraphQL errors: {response_data['errors']}")
            
            ticket = response_data["data"]["updateTicket"]
            
            logger.info(f"Ticket updated in SuperOps: {ticket['ticketNumber']}")
            return ticket
            
        except Exception as e:
            logger.error(f"Failed to update ticket in SuperOps: {e}")
            raise
    
    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Get ticket details"""
        try:
            query = """
            query GetTicket($ticketId: ID!) {
                ticket(id: $ticketId) {
                    id
                    ticketNumber
                    title
                    description
                    priority
                    status
                    category
                    assignedAgent {
                        id
                        name
                        email
                    }
                    customer {
                        email
                        phone
                    }
                    createdAt
                    updatedAt
                    estimatedResolutionTime
                    ticketUrl
                    comments {
                        id
                        content
                        author {
                            name
                        }
                        createdAt
                    }
                }
            }
            """
            
            variables = {"ticketId": ticket_id}
            
            response_data = await self._execute_graphql(query, variables)
            
            if "errors" in response_data:
                raise Exception(f"GraphQL errors: {response_data['errors']}")
            
            ticket = response_data["data"]["ticket"]
            
            logger.info(f"Retrieved ticket from SuperOps: {ticket['ticketNumber']}")
            return ticket
            
        except Exception as e:
            logger.error(f"Failed to get ticket from SuperOps: {e}")
            raise
    
    async def add_ticket_comment(self, ticket_id: str, comment: str, is_internal: bool = False) -> Dict[str, Any]:
        """Add comment to ticket"""
        try:
            mutation = """
            mutation AddTicketComment($ticketId: ID!, $input: AddCommentInput!) {
                addTicketComment(ticketId: $ticketId, input: $input) {
                    id
                    content
                    author {
                        name
                    }
                    createdAt
                    isInternal
                }
            }
            """
            
            variables = {
                "ticketId": ticket_id,
                "input": {
                    "content": comment,
                    "isInternal": is_internal
                }
            }
            
            response_data = await self._execute_graphql(mutation, variables)
            
            if "errors" in response_data:
                raise Exception(f"GraphQL errors: {response_data['errors']}")
            
            comment_data = response_data["data"]["addTicketComment"]
            
            logger.info(f"Comment added to ticket {ticket_id}")
            return comment_data
            
        except Exception as e:
            logger.error(f"Failed to add comment to ticket: {e}")
            raise
    
    async def create_callback_task(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a callback task for agent follow-up"""
        try:
            mutation = """
            mutation CreateTask($input: CreateTaskInput!) {
                createTask(input: $input) {
                    id
                    title
                    description
                    priority
                    scheduledTime
                    assignedAgent {
                        name
                    }
                    status
                    createdAt
                }
            }
            """
            
            variables = {
                "input": {
                    "title": f"Callback: {callback_data['callback_type']}",
                    "description": callback_data["instructions"],
                    "type": "CALLBACK",
                    "priority": callback_data["priority"].upper(),
                    "scheduledTime": callback_data["scheduled_time"],
                    "customerPhone": callback_data.get("customer_phone"),
                    "customerEmail": callback_data.get("customer_email"),
                    "relatedTicketId": callback_data.get("ticket_id"),
                    "metadata": {
                        "callback_reason": callback_data["reason"],
                        "callback_type": callback_data["callback_type"]
                    }
                }
            }
            
            response_data = await self._execute_graphql(mutation, variables)
            
            if "errors" in response_data:
                raise Exception(f"GraphQL errors: {response_data['errors']}")
            
            task = response_data["data"]["createTask"]
            
            result = {
                "callback_id": task["id"],
                "title": task["title"],
                "scheduled_time": task["scheduledTime"],
                "assigned_agent": task["assignedAgent"]["name"] if task["assignedAgent"] else None,
                "status": task["status"]
            }
            
            logger.info(f"Callback task created in SuperOps: {result['callback_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create callback task: {e}")
            raise
    
    async def get_agent_availability(self) -> Dict[str, Any]:
        """Get available agents for assignment"""
        try:
            query = """
            query GetAvailableAgents {
                agents(status: AVAILABLE) {
                    id
                    name
                    email
                    skills
                    currentWorkload
                    maxCapacity
                }
            }
            """
            
            response_data = await self._execute_graphql(query)
            
            if "errors" in response_data:
                raise Exception(f"GraphQL errors: {response_data['errors']}")
            
            agents = response_data["data"]["agents"]
            
            logger.info(f"Retrieved {len(agents)} available agents")
            return {"available_agents": agents}
            
        except Exception as e:
            logger.error(f"Failed to get agent availability: {e}")
            raise
    
    async def _execute_graphql(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute GraphQL query/mutation"""
        try:
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in GraphQL request: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"GraphQL request failed: {e}")
            raise