"""
AWS Bedrock Client
Handles AI model inference using AWS Bedrock
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BedrockClient:
    """AWS Bedrock client for AI model inference"""
    
    def __init__(self):
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        
        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.aws_region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        
        logger.info(f"Bedrock client initialized with model: {self.model_id}")
    
    async def analyze_issue(
        self, 
        issue_text: str, 
        context: str = "", 
        analysis_type: str = "issue_classification"
    ) -> Dict[str, Any]:
        """Analyze customer issue using Bedrock AI"""
        try:
            if analysis_type == "issue_classification":
                prompt = self._create_classification_prompt(issue_text, context)
            elif analysis_type == "sentiment_analysis":
                prompt = self._create_sentiment_prompt(issue_text)
            elif analysis_type == "urgency_detection":
                prompt = self._create_urgency_prompt(issue_text)
            else:
                prompt = self._create_general_analysis_prompt(issue_text, context)
            
            response = await self._invoke_model(prompt)
            
            # Parse response based on analysis type
            if analysis_type == "issue_classification":
                return self._parse_classification_response(response)
            elif analysis_type == "sentiment_analysis":
                return self._parse_sentiment_response(response)
            elif analysis_type == "urgency_detection":
                return self._parse_urgency_response(response)
            else:
                return self._parse_general_response(response)
                
        except Exception as e:
            logger.error(f"Issue analysis failed: {e}")
            raise
    
    async def extract_call_info(self, transcript: str, caller_phone: str = "") -> Dict[str, Any]:
        """Extract structured information from call transcript"""
        try:
            prompt = f"""
            Analyze this customer support call transcript and extract key information:

            Transcript: {transcript}
            Caller Phone: {caller_phone}

            Please extract and return the following information in JSON format:
            {{
                "customer_name": "extracted customer name or 'Unknown'",
                "customer_email": "extracted email or null",
                "issue_description": "clear summary of the main issue",
                "urgency_indicators": ["list", "of", "urgency", "keywords"],
                "resolution_attempted": "what solutions were tried during the call",
                "customer_satisfaction": "satisfied/neutral/frustrated based on tone",
                "follow_up_needed": true/false,
                "key_points": ["important", "points", "from", "call"]
            }}

            Focus on accuracy and only extract information that is clearly stated or strongly implied.
            """
            
            response = await self._invoke_model(prompt)
            return self._parse_json_response(response)
            
        except Exception as e:
            logger.error(f"Call info extraction failed: {e}")
            raise
    
    async def analyze_sentiment(
        self, 
        transcript: str, 
        conversation_segments: List[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment and urgency from call transcript"""
        try:
            prompt = f"""
            Analyze the sentiment and urgency of this customer support interaction:

            Transcript: {transcript}

            Please analyze and return the following in JSON format:
            {{
                "sentiment_score": 0.0,  // -1.0 (very negative) to 1.0 (very positive)
                "frustration_level": "low/medium/high",
                "urgency_level": "low/medium/high/critical",
                "escalation_needed": true/false,
                "key_emotions": ["frustrated", "confused", "angry", "satisfied"],
                "urgency_keywords": ["urgent", "critical", "asap"],
                "customer_tone_progression": "how tone changed during call",
                "resolution_satisfaction": "satisfied/neutral/unsatisfied"
            }}

            Consider:
            - Language intensity and emotional words
            - Repetition of issues or complaints
            - Mentions of deadlines or business impact
            - Customer's response to proposed solutions
            """
            
            response = await self._invoke_model(prompt)
            return self._parse_json_response(response)
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            raise
    
    def _create_classification_prompt(self, issue_text: str, context: str) -> str:
        """Create prompt for issue classification"""
        return f"""
        Analyze this customer support issue and classify it:

        Issue: {issue_text}
        Context: {context}

        Please provide analysis in JSON format:
        {{
            "issue_summary": "concise summary of the main issue",
            "urgency_level": "low/medium/high/critical",
            "suggested_category": "authentication/billing/technical_issues/account_management/integrations/performance/security",
            "key_points": ["main", "points", "from", "issue"],
            "complexity_level": "simple/moderate/complex",
            "estimated_resolution_time": "5 minutes/30 minutes/2 hours/1 day",
            "requires_escalation": true/false,
            "suggested_actions": ["immediate", "actions", "to", "take"]
        }}

        Consider:
        - Technical complexity of the issue
        - Business impact mentioned
        - Customer's technical level
        - Urgency indicators in language
        """
    
    def _create_sentiment_prompt(self, issue_text: str) -> str:
        """Create prompt for sentiment analysis"""
        return f"""
        Analyze the sentiment of this customer message:

        Message: {issue_text}

        Return sentiment analysis in JSON format:
        {{
            "sentiment_score": 0.0,  // -1.0 to 1.0
            "sentiment_label": "positive/neutral/negative",
            "confidence": 0.0,  // 0.0 to 1.0
            "emotional_indicators": ["frustrated", "polite", "urgent"],
            "tone": "professional/casual/frustrated/angry/polite"
        }}
        """
    
    def _create_urgency_prompt(self, issue_text: str) -> str:
        """Create prompt for urgency detection"""
        return f"""
        Determine the urgency level of this support issue:

        Issue: {issue_text}

        Return urgency analysis in JSON format:
        {{
            "urgency_level": "low/medium/high/critical",
            "urgency_score": 0.0,  // 0.0 to 1.0
            "urgency_indicators": ["deadline mentioned", "business impact", "system down"],
            "business_impact": "none/low/medium/high",
            "time_sensitivity": "not urgent/within week/within day/immediate"
        }}
        """
    
    def _create_general_analysis_prompt(self, issue_text: str, context: str) -> str:
        """Create general analysis prompt"""
        return f"""
        Provide a comprehensive analysis of this customer support issue:

        Issue: {issue_text}
        Context: {context}

        Please analyze and return in JSON format:
        {{
            "summary": "brief summary",
            "category": "likely category",
            "urgency": "urgency level",
            "sentiment": "customer sentiment",
            "next_steps": ["recommended", "actions"],
            "keywords": ["key", "terms"]
        }}
        """
    
    async def _invoke_model(self, prompt: str) -> str:
        """Invoke Bedrock model with prompt"""
        try:
            # Prepare request body based on model
            if "claude" in self.model_id.lower():
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            else:
                # Generic format for other models
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 4000,
                        "temperature": 0.1,
                        "topP": 0.9
                    }
                }
            
            # Invoke model
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if "claude" in self.model_id.lower():
                return response_body['content'][0]['text']
            else:
                return response_body.get('results', [{}])[0].get('outputText', '')
                
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Model invocation failed: {e}")
            raise
    
    def _parse_classification_response(self, response: str) -> Dict[str, Any]:
        """Parse classification response"""
        try:
            return self._parse_json_response(response)
        except:
            # Fallback parsing if JSON fails
            return {
                "issue_summary": "Unable to parse AI response",
                "urgency_level": "medium",
                "suggested_category": "technical_issues",
                "key_points": [],
                "complexity_level": "moderate",
                "estimated_resolution_time": "30 minutes",
                "requires_escalation": False,
                "suggested_actions": ["manual_review_required"]
            }
    
    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        """Parse sentiment response"""
        try:
            return self._parse_json_response(response)
        except:
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.5,
                "emotional_indicators": [],
                "tone": "neutral"
            }
    
    def _parse_urgency_response(self, response: str) -> Dict[str, Any]:
        """Parse urgency response"""
        try:
            return self._parse_json_response(response)
        except:
            return {
                "urgency_level": "medium",
                "urgency_score": 0.5,
                "urgency_indicators": [],
                "business_impact": "medium",
                "time_sensitivity": "within day"
            }
    
    def _parse_general_response(self, response: str) -> Dict[str, Any]:
        """Parse general analysis response"""
        try:
            return self._parse_json_response(response)
        except:
            return {
                "summary": "AI analysis unavailable",
                "category": "technical_issues",
                "urgency": "medium",
                "sentiment": "neutral",
                "next_steps": ["manual_review"],
                "keywords": []
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from AI model"""
        try:
            # Try to find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, try parsing entire response
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {response}")
            raise