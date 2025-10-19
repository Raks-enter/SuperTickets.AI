"""
AWS Bedrock AI Email Processor
Real AI-powered email analysis using Claude 3
"""

import json
import logging
import boto3
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EmailAnalysis:
    """AI email analysis result"""
    category: str
    priority: str
    sentiment: str
    intent: str
    confidence: float
    keywords: List[str]
    requires_human: bool
    suggested_response: Optional[str] = None
    ticket_needed: bool = False
    reasoning: str = ""

class BedrockAIProcessor:
    """AWS Bedrock AI-powered email processor"""
    
    def __init__(self):
        try:
            # Initialize Bedrock client
            self.bedrock = boto3.client(
                'bedrock-runtime',
                region_name='us-east-1'  # Claude 3 available regions
            )
            self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
            logger.info("AWS Bedrock AI processor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self.bedrock = None

    async def analyze_email(self, email_content: str, subject: str, sender: str) -> EmailAnalysis:
        """Analyze email using Claude 3 AI"""
        try:
            if not self.bedrock:
                return self._fallback_analysis(email_content, subject)
            
            # Prepare AI prompt for email analysis
            analysis_prompt = self._create_analysis_prompt(email_content, subject, sender)
            
            # Call Claude 3 for analysis
            analysis_result = await self._call_bedrock_ai(analysis_prompt)
            
            # Parse AI response
            return self._parse_ai_analysis(analysis_result)
            
        except Exception as e:
            logger.error(f"AI email analysis failed: {e}")
            return self._fallback_analysis(email_content, subject)

    def _create_analysis_prompt(self, email_content: str, subject: str, sender: str) -> str:
        """Create structured prompt for Claude 3"""
        return f"""
You are an expert customer support AI analyzing incoming emails. Analyze this email and provide a structured response.

EMAIL DETAILS:
Subject: {subject}
From: {sender}
Content: {email_content}

ANALYSIS REQUIRED:
1. Category (technical, billing, account, general, complaint, feature_request)
2. Priority (high, medium, low)
3. Sentiment (positive, negative, neutral)
4. Intent (question, support_request, complaint, refund_request, information)
5. Confidence (0.0-1.0)
6. Keywords (5-10 important words)
7. Requires Human (true/false)
8. Ticket Needed (true/false)
9. Reasoning (brief explanation)

RESPONSE FORMAT (JSON):
{{
    "category": "technical|billing|account|general|complaint|feature_request",
    "priority": "high|medium|low",
    "sentiment": "positive|negative|neutral", 
    "intent": "question|support_request|complaint|refund_request|information",
    "confidence": 0.85,
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "requires_human": false,
    "ticket_needed": true,
    "reasoning": "Brief explanation of analysis"
}}

GUIDELINES:
- High priority: urgent, critical, system down, security issues
- Requires human: complex technical issues, billing disputes, complaints, legal matters
- Ticket needed: technical problems, account issues, anything requiring follow-up
- Be accurate and concise in your analysis
"""

    async def _call_bedrock_ai(self, prompt: str) -> str:
        """Call AWS Bedrock Claude 3 API"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,  # Low temperature for consistent analysis
                "top_p": 0.9
            }
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Bedrock API call failed: {e}")
            raise

    def _parse_ai_analysis(self, ai_response: str) -> EmailAnalysis:
        """Parse Claude 3 response into EmailAnalysis object"""
        try:
            # Extract JSON from AI response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = ai_response[json_start:json_end]
            analysis_data = json.loads(json_str)
            
            return EmailAnalysis(
                category=analysis_data.get('category', 'general'),
                priority=analysis_data.get('priority', 'medium'),
                sentiment=analysis_data.get('sentiment', 'neutral'),
                intent=analysis_data.get('intent', 'support_request'),
                confidence=float(analysis_data.get('confidence', 0.7)),
                keywords=analysis_data.get('keywords', []),
                requires_human=analysis_data.get('requires_human', False),
                ticket_needed=analysis_data.get('ticket_needed', True),
                reasoning=analysis_data.get('reasoning', 'AI analysis completed')
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI analysis: {e}")
            return self._fallback_analysis("", "")

    def _fallback_analysis(self, email_content: str, subject: str) -> EmailAnalysis:
        """Fallback analysis when AI fails"""
        return EmailAnalysis(
            category='general',
            priority='medium',
            sentiment='neutral',
            intent='support_request',
            confidence=0.5,
            keywords=[],
            requires_human=True,
            ticket_needed=True,
            reasoning='Fallback analysis - AI unavailable'
        )

    async def generate_response(self, analysis: EmailAnalysis, email_content: str, 
                              subject: str, kb_results: List[Dict] = None) -> str:
        """Generate AI response using Claude 3"""
        try:
            if not self.bedrock:
                return self._fallback_response(analysis)
            
            # Create response generation prompt
            response_prompt = self._create_response_prompt(
                analysis, email_content, subject, kb_results
            )
            
            # Generate response with Claude 3
            ai_response = await self._call_bedrock_ai(response_prompt)
            
            # Clean and format response
            return self._format_response(ai_response, analysis)
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._fallback_response(analysis)

    def _create_response_prompt(self, analysis: EmailAnalysis, email_content: str, 
                              subject: str, kb_results: List[Dict] = None) -> str:
        """Create prompt for response generation"""
        kb_context = ""
        if kb_results:
            kb_context = "\nKNOWLEDGE BASE RESULTS:\n"
            for result in kb_results[:3]:
                kb_context += f"- {result.get('title', 'Solution')}: {result.get('content', '')}\n"
        
        return f"""
You are a professional customer support agent for SuperTickets.AI. Generate a helpful, empathetic response to this customer email.

CUSTOMER EMAIL:
Subject: {subject}
Content: {email_content}

AI ANALYSIS:
Category: {analysis.category}
Priority: {analysis.priority}
Sentiment: {analysis.sentiment}
Intent: {analysis.intent}
Reasoning: {analysis.reasoning}

{kb_context}

RESPONSE GUIDELINES:
1. Be professional, helpful, and empathetic
2. Address the customer's specific concern
3. Use knowledge base information if available
4. If creating a ticket, mention ticket reference
5. Provide clear next steps
6. Match the tone to customer sentiment
7. Keep response concise but complete

RESPONSE TEMPLATE:
- Greeting with acknowledgment
- Address specific issue
- Provide solution or next steps
- Professional closing

Generate a complete email response:
"""

    def _format_response(self, ai_response: str, analysis: EmailAnalysis) -> str:
        """Format and enhance AI response"""
        try:
            # Clean up AI response
            response = ai_response.strip()
            
            # Add ticket reference if needed
            if analysis.ticket_needed:
                response += f"\n\nA support ticket has been created for your request. You'll receive updates as we work on your issue."
            
            # Add signature
            response += "\n\nBest regards,\nSuperTickets.AI Support Team"
            
            return response
            
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            return ai_response

    def _fallback_response(self, analysis: EmailAnalysis) -> str:
        """Fallback response when AI fails"""
        return f"""Hello,

Thank you for contacting SuperTickets.AI support. We've received your {analysis.category} inquiry and our team will review it shortly.

{"A support ticket has been created and " if analysis.ticket_needed else ""}You can expect a response within 24 hours.

If you have any urgent concerns, please don't hesitate to contact us directly.

Best regards,
SuperTickets.AI Support Team"""

    async def search_knowledge_base_ai(self, query: str) -> List[Dict]:
        """AI-powered knowledge base search"""
        try:
            if not self.bedrock:
                return []
            
            # Use AI to enhance search query
            search_prompt = f"""
Analyze this customer query and generate 3-5 relevant search terms for a knowledge base:

Customer Query: {query}

Generate search terms that would find relevant solutions:
- Focus on key technical terms
- Include synonyms and variations
- Consider common support categories

Return only the search terms, one per line:
"""
            
            ai_search_terms = await self._call_bedrock_ai(search_prompt)
            
            # Mock KB results (replace with actual KB search)
            mock_results = [
                {
                    "title": "Common Solutions",
                    "content": f"Based on your query about '{query}', here are some common solutions...",
                    "similarity": 0.8
                }
            ]
            
            return mock_results
            
        except Exception as e:
            logger.error(f"AI KB search failed: {e}")
            return []

    def get_model_info(self) -> Dict:
        """Get AI model information"""
        return {
            "provider": "AWS Bedrock",
            "model": "Claude 3 Sonnet",
            "model_id": self.model_id,
            "capabilities": [
                "Email Analysis",
                "Response Generation", 
                "Sentiment Analysis",
                "Intent Recognition",
                "Knowledge Base Search"
            ],
            "status": "connected" if self.bedrock else "disconnected"
        }