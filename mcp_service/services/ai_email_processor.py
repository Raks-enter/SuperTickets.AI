"""
AI Email Processor
Handles automatic email analysis, categorization, and response generation
"""

import logging
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmailAnalysis:
    """Email analysis result"""
    category: str
    priority: str
    sentiment: str
    intent: str
    confidence: float
    keywords: List[str]
    requires_human: bool
    suggested_response: Optional[str] = None
    ticket_needed: bool = False

class AIEmailProcessor:
    """AI-powered email processor for automatic triage and response"""
    
    def __init__(self):
        self.categories = {
            'technical': ['error', 'bug', 'crash', 'not working', 'broken', 'issue', 'problem'],
            'billing': ['payment', 'invoice', 'charge', 'refund', 'subscription', 'billing'],
            'account': ['login', 'password', 'access', 'account', 'profile', 'settings'],
            'general': ['question', 'help', 'how to', 'information', 'support'],
            'complaint': ['angry', 'frustrated', 'terrible', 'awful', 'disappointed'],
            'feature_request': ['feature', 'enhancement', 'suggestion', 'improve', 'add']
        }
        
        self.priority_keywords = {
            'high': ['urgent', 'critical', 'emergency', 'asap', 'immediately', 'down', 'outage'],
            'medium': ['important', 'soon', 'needed', 'issue', 'problem'],
            'low': ['question', 'when possible', 'eventually', 'minor']
        }
        
        self.sentiment_keywords = {
            'positive': ['thank', 'great', 'excellent', 'love', 'amazing', 'perfect'],
            'negative': ['angry', 'frustrated', 'terrible', 'awful', 'hate', 'worst'],
            'neutral': ['question', 'help', 'information', 'please', 'need']
        }

    async def analyze_email(self, email_content: str, subject: str, sender: str) -> EmailAnalysis:
        """Analyze email and determine category, priority, and response strategy"""
        try:
            # Combine subject and content for analysis
            full_text = f"{subject} {email_content}".lower()
            
            # Categorize email
            category = self._categorize_email(full_text)
            
            # Determine priority
            priority = self._determine_priority(full_text)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(full_text)
            
            # Determine intent
            intent = self._determine_intent(full_text, category)
            
            # Extract keywords
            keywords = self._extract_keywords(full_text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(category, priority, sentiment)
            
            # Determine if human intervention needed
            requires_human = self._requires_human_review(category, priority, sentiment, keywords)
            
            # Determine if ticket needed
            ticket_needed = self._needs_ticket(category, priority, intent)
            
            analysis = EmailAnalysis(
                category=category,
                priority=priority,
                sentiment=sentiment,
                intent=intent,
                confidence=confidence,
                keywords=keywords,
                requires_human=requires_human,
                ticket_needed=ticket_needed
            )
            
            logger.info(f"Email analyzed: {category}/{priority}/{sentiment} (confidence: {confidence:.2f})")
            return analysis
            
        except Exception as e:
            logger.error(f"Email analysis failed: {e}")
            # Return safe defaults
            return EmailAnalysis(
                category='general',
                priority='medium',
                sentiment='neutral',
                intent='support_request',
                confidence=0.5,
                keywords=[],
                requires_human=True,
                ticket_needed=True
            )

    def _categorize_email(self, text: str) -> str:
        """Categorize email based on content"""
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return 'general'

    def _determine_priority(self, text: str) -> str:
        """Determine email priority"""
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in text for keyword in keywords):
                return priority
        return 'medium'

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze email sentiment"""
        sentiment_scores = {}
        
        for sentiment, keywords in self.sentiment_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                sentiment_scores[sentiment] = score
        
        if sentiment_scores:
            return max(sentiment_scores, key=sentiment_scores.get)
        return 'neutral'

    def _determine_intent(self, text: str, category: str) -> str:
        """Determine user intent"""
        if any(word in text for word in ['how', 'what', 'when', 'where', 'why', '?']):
            return 'question'
        elif any(word in text for word in ['fix', 'solve', 'help', 'support']):
            return 'support_request'
        elif any(word in text for word in ['refund', 'cancel', 'return']):
            return 'refund_request'
        elif category == 'complaint':
            return 'complaint'
        else:
            return 'support_request'

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from email"""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text)
        # Filter out common words and keep important ones
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cannot', 'cant', 'wont', 'dont', 'doesnt', 'didnt', 'havent', 'hasnt', 'hadnt', 'isnt', 'arent', 'wasnt', 'werent', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 'those', 'a', 'an'}
        
        keywords = [word for word in words if len(word) > 3 and word.lower() not in stop_words]
        return list(set(keywords))[:10]  # Return top 10 unique keywords

    def _calculate_confidence(self, category: str, priority: str, sentiment: str) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = 0.7
        
        # Adjust based on category certainty
        if category in ['technical', 'billing']:
            base_confidence += 0.1
        elif category == 'general':
            base_confidence -= 0.1
            
        # Adjust based on priority clarity
        if priority in ['high', 'low']:
            base_confidence += 0.1
            
        # Adjust based on sentiment clarity
        if sentiment in ['positive', 'negative']:
            base_confidence += 0.1
            
        return min(base_confidence, 1.0)

    def _requires_human_review(self, category: str, priority: str, sentiment: str, keywords: List[str]) -> bool:
        """Determine if email requires human review"""
        # Always require human review for high priority or negative sentiment
        if priority == 'high' or sentiment == 'negative':
            return True
            
        # Require human review for complaints
        if category == 'complaint':
            return True
            
        # Require human review for complex technical issues
        if category == 'technical' and any(word in keywords for word in ['crash', 'data', 'security', 'breach']):
            return True
            
        # Require human review for billing issues
        if category == 'billing':
            return True
            
        return False

    def _needs_ticket(self, category: str, priority: str, intent: str) -> bool:
        """Determine if a support ticket should be created"""
        # Always create ticket for high priority
        if priority == 'high':
            return True
            
        # Create ticket for technical issues
        if category == 'technical':
            return True
            
        # Create ticket for complaints
        if category == 'complaint':
            return True
            
        # Create ticket for complex support requests
        if intent == 'support_request' and category != 'general':
            return True
            
        return False

    async def generate_response(self, analysis: EmailAnalysis, email_content: str, 
                              kb_results: List[Dict] = None) -> str:
        """Generate appropriate response based on analysis"""
        try:
            # If we have knowledge base results, use them
            if kb_results and len(kb_results) > 0:
                best_result = kb_results[0]
                if best_result.get('similarity', 0) > 0.7:
                    return self._generate_solution_response(analysis, best_result)
            
            # Generate response based on category and intent
            if analysis.category == 'technical':
                return self._generate_technical_response(analysis)
            elif analysis.category == 'billing':
                return self._generate_billing_response(analysis)
            elif analysis.category == 'account':
                return self._generate_account_response(analysis)
            elif analysis.category == 'complaint':
                return self._generate_complaint_response(analysis)
            elif analysis.category == 'feature_request':
                return self._generate_feature_request_response(analysis)
            else:
                return self._generate_general_response(analysis)
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._generate_fallback_response()

    def _generate_solution_response(self, analysis: EmailAnalysis, kb_result: Dict) -> str:
        """Generate response with knowledge base solution"""
        return f"""Hello,

Thank you for contacting our support team. I found a solution that should help with your {analysis.category} issue.

**Solution:**
{kb_result.get('content', 'Please see our knowledge base for detailed instructions.')}

If this doesn't resolve your issue, I've created a support ticket for further assistance. Our team will follow up with you shortly.

Best regards,
SuperTickets.AI Support Team"""

    def _generate_technical_response(self, analysis: EmailAnalysis) -> str:
        """Generate technical issue response"""
        if analysis.priority == 'high':
            return """Hello,

Thank you for reporting this technical issue. I understand this is urgent and I've immediately escalated your case to our technical team.

A support ticket has been created and you should expect a response within 2 hours.

In the meantime, please try:
1. Clearing your browser cache
2. Trying a different browser
3. Checking our status page for any known issues

Best regards,
SuperTickets.AI Support Team"""
        else:
            return """Hello,

Thank you for contacting us about this technical issue. I've created a support ticket and our technical team will investigate this for you.

You can expect a response within 24 hours. We'll keep you updated on our progress.

Best regards,
SuperTickets.AI Support Team"""

    def _generate_billing_response(self, analysis: EmailAnalysis) -> str:
        """Generate billing issue response"""
        return """Hello,

Thank you for contacting us regarding your billing inquiry. I've created a support ticket and forwarded your case to our billing department.

Our billing team will review your account and respond within 24 hours with a detailed explanation.

If you need immediate assistance, please call our billing hotline at [PHONE_NUMBER].

Best regards,
SuperTickets.AI Support Team"""

    def _generate_account_response(self, analysis: EmailAnalysis) -> str:
        """Generate account issue response"""
        return """Hello,

Thank you for contacting us about your account. For security reasons, I've created a support ticket and our account specialists will assist you.

Please have your account information ready when they contact you. You should receive a response within 12 hours.

For immediate password resets, you can use the "Forgot Password" link on our login page.

Best regards,
SuperTickets.AI Support Team"""

    def _generate_complaint_response(self, analysis: EmailAnalysis) -> str:
        """Generate complaint response"""
        return """Hello,

Thank you for taking the time to share your feedback with us. I sincerely apologize for any inconvenience you've experienced.

I've immediately escalated your concerns to our management team and created a priority support ticket. A senior team member will personally review your case and contact you within 4 hours.

We value your business and are committed to resolving this matter to your satisfaction.

Best regards,
SuperTickets.AI Support Team"""

    def _generate_feature_request_response(self, analysis: EmailAnalysis) -> str:
        """Generate feature request response"""
        return """Hello,

Thank you for your feature suggestion! We appreciate customers who help us improve our product.

I've forwarded your request to our product development team for consideration. While I can't guarantee implementation, all suggestions are carefully reviewed.

You'll receive updates if your feature is added to our development roadmap.

Best regards,
SuperTickets.AI Support Team"""

    def _generate_general_response(self, analysis: EmailAnalysis) -> str:
        """Generate general response"""
        return """Hello,

Thank you for contacting SuperTickets.AI support. I've received your message and created a support ticket for you.

Our support team will review your request and respond within 24 hours with the information you need.

If you have any urgent concerns, please don't hesitate to contact us directly.

Best regards,
SuperTickets.AI Support Team"""

    def _generate_fallback_response(self) -> str:
        """Generate fallback response when other methods fail"""
        return """Hello,

Thank you for contacting SuperTickets.AI support. I've received your message and our team will review it shortly.

You can expect a response within 24 hours. If you need immediate assistance, please contact our support hotline.

Best regards,
SuperTickets.AI Support Team"""