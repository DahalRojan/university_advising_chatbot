"""
Smart Fallback Manager
Intelligent fallback system to reduce unnecessary fallback messages and provide targeted guidance
"""

import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime
import json

class SmartFallbackManager:
    """
    Intelligent fallback system that reduces unnecessary fallback messages by:
    1. Analyzing retrieval confidence and LLM confidence
    2. Categorizing queries for targeted fallback messages
    3. Providing contextual guidance instead of generic fallbacks
    4. Escalating appropriately when truly no information is available
    """
    
    def __init__(self):
        # Much less aggressive fallbacks - more ChatGPT-like confidence
        self.confidence_thresholds = {
            "high_confidence": 0.6,      # Proceed with response
            "medium_confidence": 0.3,    # Proceed with response (very lowered)
            "low_confidence": 0.15,      # Provide targeted guidance (very lowered)
            "very_low_confidence": 0.05  # Acknowledge limitation (very lowered)
        }
        
        # Query categorization patterns for targeted fallbacks
        self.query_categories = {
            "course_specific": {
                "patterns": [
                    r'\b[A-Z]{2,5}\s*\d{3,4}\b',  # Course codes
                    r'\bcourse\s+(code|number|title)\b',
                    r'\bclass\s+(description|info|details)\b'
                ],
                "keywords": ["course", "class", "section", "instructor", "syllabus"]
            },
            "prerequisites": {
                "patterns": [
                    r'\bprerequisite[s]?\b',
                    r'\bpre-req[s]?\b',
                    r'\brequirement[s]?\s+before\b',
                    r'\bwhat.*need.*before\b'
                ],
                "keywords": ["prerequisite", "prereq", "requirement", "before", "need"]
            },
            "degree_requirements": {
                "patterns": [
                    r'\b(degree|major|minor)\s+requirement[s]?\b',
                    r'\bgraduation\s+requirement[s]?\b',
                    r'\bcore\s+requirement[s]?\b'
                ],
                "keywords": ["degree", "major", "minor", "graduation", "requirement", "core"]
            },
            "academic_planning": {
                "patterns": [
                    r'\bschedule\s+planning\b',
                    r'\bcourse\s+sequence\b',
                    r'\bacademic\s+plan\b',
                    r'\bfour.year\s+plan\b'
                ],
                "keywords": ["schedule", "plan", "sequence", "timeline", "roadmap"]
            },
            "scheduling": {
                "patterns": [
                    r'\bwhen\s+is\s+.*offered\b',
                    r'\bsemester\s+schedule\b',
                    r'\bclass\s+times?\b',
                    r'\boffering\s+schedule\b'
                ],
                "keywords": ["schedule", "time", "semester", "offered", "when", "availability"]
            },
            "financial_aid": {
                "patterns": [
                    r'\bfinancial\s+aid\b',
                    r'\bscholarship[s]?\b',
                    r'\btuition\s+(cost|fee)\b',
                    r'\bpayment\s+plan[s]?\b'
                ],
                "keywords": ["financial", "aid", "scholarship", "tuition", "cost", "fee", "payment"]
            },
            "transfer_credits": {
                "patterns": [
                    r'\btransfer\s+credit[s]?\b',
                    r'\barticulation\s+agreement[s]?\b',
                    r'\bcredit\s+transfer\b',
                    r'\bprevious\s+college\b'
                ],
                "keywords": ["transfer", "credit", "articulation", "previous", "other", "college"]
            },
            "academic_policies": {
                "patterns": [
                    r'\bpolicy\s+on\b',
                    r'\brule[s]?\s+(about|regarding)\b',
                    r'\bregulation[s]?\b',
                    r'\bprocedure[s]?\s+for\b'
                ],
                "keywords": ["policy", "rule", "regulation", "procedure", "guideline"]
            },
            "career_guidance": {
                "patterns": [
                    r'\bcareer\s+(path|option)[s]?\b',
                    r'\bjob\s+(prospect|opportunity)[s]?\b',
                    r'\binternship[s]?\b',
                    r'\bemployment\s+rate[s]?\b'
                ],
                "keywords": ["career", "job", "employment", "internship", "professional"]
            },
            "academic_support": {
                "patterns": [
                    r'\btutoring\s+service[s]?\b',
                    r'\bacademic\s+support\b',
                    r'\bstudy\s+help\b',
                    r'\blearning\s+resource[s]?\b'
                ],
                "keywords": ["tutoring", "support", "help", "resource", "assistance", "study"]
            },
            "general_information": {
                "patterns": [
                    r'\btell\s+me\s+about\b',
                    r'\binformation\s+about\b',
                    r'\bwhat\s+is\b',
                    r'\bexplain\b'
                ],
                "keywords": ["information", "about", "explain", "describe", "tell"]
            },
            "greeting": {
                "patterns": [
                    r'^\s*(hi|hello|hey|greetings)\s*$',
                    r'^\s*(good\s+(morning|afternoon|evening))\s*$',
                    r'^\s*(how\s+are\s+you)\s*\??$'
                ],
                "keywords": ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
            }
        }
        
        # Confidence boosting factors
        self.confidence_boosters = {
            "specific_course_code": 0.15,     # Query mentions specific course
            "specific_program": 0.10,         # Query mentions specific program
            "clear_intent": 0.10,             # Query has clear intent
            "academic_terminology": 0.05,     # Uses proper academic terms
            "contextual_continuity": 0.10     # Builds on previous conversation
        }
        
        # Confidence reducing factors
        self.confidence_reducers = {
            "too_broad": -0.20,               # Query is too broad/generic
            "unclear_intent": -0.15,          # Intent is unclear
            "multiple_questions": -0.10,      # Multiple unrelated questions
            "vague_language": -0.10,          # Uses vague language
            "out_of_scope": -0.25             # Clearly outside academic domain
        }
    
    def should_provide_fallback(self, retrieval_result: Dict, llm_confidence: int, 
                              query: str, conversation_context: Dict = None) -> Dict:
        """
        Determine if fallback message should be provided and what type of fallback is appropriate
        """
        # Extract confidence scores
        retrieval_confidence = retrieval_result.get("confidence", {}).get("confidence_score", 0.0)
        
        # Convert LLM confidence (1-5) to 0-1 scale
        llm_confidence_normalized = llm_confidence / 5.0
        
        # Analyze query characteristics
        query_analysis = self._analyze_query_characteristics(query, conversation_context)
        
        # Calculate adjusted confidence scores
        adjusted_retrieval = self._adjust_confidence_score(
            retrieval_confidence, query_analysis, "retrieval"
        )
        adjusted_llm = self._adjust_confidence_score(
            llm_confidence_normalized, query_analysis, "llm"
        )
        
        # Combined confidence calculation with weighted average
        combined_confidence = (adjusted_retrieval * 0.6 + adjusted_llm * 0.4)
        
        # Categorize query for targeted fallback
        query_category = self._categorize_query(query)
        
        # Determine fallback strategy
        fallback_decision = self._determine_fallback_strategy(
            combined_confidence, query_category, query, query_analysis, retrieval_result
        )
        
        return {
            "should_fallback": fallback_decision["should_fallback"],
            "fallback_type": fallback_decision["fallback_type"],
            "fallback_message": fallback_decision.get("message", ""),
            "confidence_breakdown": {
                "retrieval_original": retrieval_confidence,
                "retrieval_adjusted": adjusted_retrieval,
                "llm_original": llm_confidence_normalized,
                "llm_adjusted": adjusted_llm,
                "combined": combined_confidence
            },
            "query_analysis": query_analysis,
            "query_category": query_category,
            "strategy_reasoning": fallback_decision.get("reasoning", ""),
            "alternative_actions": fallback_decision.get("alternative_actions", [])
        }
    
    def _analyze_query_characteristics(self, query: str, conversation_context: Dict = None) -> Dict:
        """Analyze query characteristics that affect confidence"""
        analysis = {
            "specificity_score": 0.0,
            "clarity_score": 0.0,
            "academic_relevance": 0.0,
            "intent_clarity": 0.0,
            "characteristics": []
        }
        
        query_lower = query.lower().strip()
        
        # Analyze specificity
        specificity_indicators = {
            "course_codes": len(re.findall(r'\b[A-Z]{2,5}\s*\d{3,4}\b', query)),
            "specific_programs": len(re.findall(r'\b(computer science|engineering|business|psychology|biology|mathematics|english|history|chemistry|physics)\b', query_lower)),
            "specific_terms": len(re.findall(r'\b(prerequisite|corequisite|credit|hour|gpa|semester|graduation)\b', query_lower)),
            "question_words": len(re.findall(r'\b(what|when|where|how|why|which|who)\b', query_lower))
        }
        
        # Calculate specificity score
        total_specific_elements = sum(specificity_indicators.values())
        analysis["specificity_score"] = min(total_specific_elements * 0.2, 1.0)
        
        if specificity_indicators["course_codes"] > 0:
            analysis["characteristics"].append("specific_course_mentioned")
        if specificity_indicators["specific_programs"] > 0:
            analysis["characteristics"].append("specific_program_mentioned")
        
        # Analyze clarity
        clarity_factors = {
            "has_question_word": bool(specificity_indicators["question_words"]),
            "reasonable_length": 5 <= len(query.split()) <= 30,
            "proper_grammar": "?" in query or query.endswith("."),
            "no_typos": self._check_for_obvious_typos(query)
        }
        
        analysis["clarity_score"] = sum(clarity_factors.values()) / len(clarity_factors)
        
        # Analyze academic relevance
        academic_keywords = [
            "course", "class", "degree", "major", "minor", "credit", "semester", 
            "graduation", "requirement", "prerequisite", "schedule", "academic",
            "university", "college", "student", "enrollment", "registration"
        ]
        
        academic_matches = sum(1 for keyword in academic_keywords if keyword in query_lower)
        analysis["academic_relevance"] = min(academic_matches * 0.15, 1.0)
        
        # Analyze intent clarity
        intent_patterns = [
            r'\bwhat\s+(are|is)\s+the\s+prerequisite',
            r'\bhow\s+(do|can)\s+i\b',
            r'\bwhen\s+(should|can|do)\s+i\b',
            r'\bwhere\s+(can|do)\s+i\b',
            r'\bwhich\s+course[s]?\b',
            r'\bshould\s+i\s+take\b',
            r'\bcan\s+i\s+(take|enroll)\b'
        ]
        
        intent_matches = sum(1 for pattern in intent_patterns if re.search(pattern, query_lower))
        analysis["intent_clarity"] = min(intent_matches * 0.3, 1.0)
        
        # Add contextual analysis if conversation context available
        if conversation_context:
            context_factors = self._analyze_contextual_factors(query, conversation_context)
            analysis.update(context_factors)
        
        return analysis
    
    def _check_for_obvious_typos(self, query: str) -> bool:
        """Basic typo detection (can be enhanced with spell checking libraries)"""
        # Simple heuristics for obvious typos
        words = query.lower().split()
        
        # Check for common academic word typos
        typo_patterns = [
            r'\bprereqisite\b',  # prerequisite
            r'\bgradutation\b',  # graduation
            r'\buniversty\b',    # university
            r'\bsemeseter\b',    # semester
            r'\brequirment\b'    # requirement
        ]
        
        for pattern in typo_patterns:
            if re.search(pattern, query.lower()):
                return False
        
        return True
    
    def _analyze_contextual_factors(self, query: str, conversation_context: Dict) -> Dict:
        """Analyze how query relates to conversation context"""
        contextual_analysis = {
            "builds_on_previous": False,
            "entity_continuity": False,
            "topic_continuity": False,
            "context_boost": 0.0
        }
        
        # Check if query builds on previous discussion
        if conversation_context.get("context_continuity", {}).get("has_continuity"):
            contextual_analysis["builds_on_previous"] = True
            contextual_analysis["context_boost"] += 0.1
        
        # Check entity continuity
        mentioned_entities = conversation_context.get("mentioned_entities", {})
        query_lower = query.lower()
        
        for entity_type, entities in mentioned_entities.items():
            if entities:
                for entity in entities:
                    if entity.lower() in query_lower:
                        contextual_analysis["entity_continuity"] = True
                        contextual_analysis["context_boost"] += 0.05
                        break
        
        # Check topic continuity
        recent_topics = conversation_context.get("recent_topics", [])
        current_topic = self._categorize_query(query)
        
        if current_topic in recent_topics:
            contextual_analysis["topic_continuity"] = True
            contextual_analysis["context_boost"] += 0.05
        
        return contextual_analysis
    
    def _adjust_confidence_score(self, original_score: float, query_analysis: Dict, 
                                score_type: str) -> float:
        """Adjust confidence score based on query characteristics"""
        adjusted_score = original_score
        
        # Apply boosters
        if "specific_course_mentioned" in query_analysis.get("characteristics", []):
            adjusted_score += self.confidence_boosters["specific_course_code"]
        
        if "specific_program_mentioned" in query_analysis.get("characteristics", []):
            adjusted_score += self.confidence_boosters["specific_program"]
        
        if query_analysis.get("intent_clarity", 0) > 0.7:
            adjusted_score += self.confidence_boosters["clear_intent"]
        
        if query_analysis.get("academic_relevance", 0) > 0.6:
            adjusted_score += self.confidence_boosters["academic_terminology"]
        
        if query_analysis.get("builds_on_previous", False):
            adjusted_score += self.confidence_boosters["contextual_continuity"]
        
        # Apply reducers
        if query_analysis.get("specificity_score", 0) < 0.3:
            adjusted_score += self.confidence_reducers["too_broad"]
        
        if query_analysis.get("intent_clarity", 0) < 0.4:
            adjusted_score += self.confidence_reducers["unclear_intent"]
        
        if query_analysis.get("academic_relevance", 0) < 0.3:
            adjusted_score += self.confidence_reducers["out_of_scope"]
        
        # Ensure score stays within bounds
        return max(0.0, min(1.0, adjusted_score))
    
    def _categorize_query(self, query: str) -> str:
        """Categorize query into academic topic areas"""
        query_lower = query.lower()
        category_scores = {}
        
        for category, config in self.query_categories.items():
            score = 0
            
            # Check patterns
            for pattern in config.get("patterns", []):
                if re.search(pattern, query_lower):
                    score += 2
            
            # Check keywords
            for keyword in config.get("keywords", []):
                if keyword in query_lower:
                    score += 1
            
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return "general_information"
    
    def _determine_fallback_strategy(self, combined_confidence: float, query_category: str,
                                   query: str, query_analysis: Dict, retrieval_result: Dict) -> Dict:
        """Determine appropriate fallback strategy based on analysis"""
        
        # Special handling for greetings - never fallback, let LLM handle naturally
        if query_category == "greeting":
            return {
                "should_fallback": False,
                "fallback_type": "none",
                "reasoning": "Greeting detected - allowing natural LLM response"
            }
        
        # High or medium confidence - proceed without fallback (ChatGPT style)
        if combined_confidence >= self.confidence_thresholds["medium_confidence"]:
            return {
                "should_fallback": False,
                "fallback_type": "none",
                "reasoning": f"Sufficient confidence ({combined_confidence:.2f}) - proceeding with response"
            }
        
        # Low confidence - provide targeted guidance
        elif combined_confidence >= self.confidence_thresholds["low_confidence"]:
            return {
                "should_fallback": True,
                "fallback_type": "targeted_guidance",
                "message": self._generate_targeted_guidance(query_category, query, query_analysis),
                "reasoning": f"Low confidence ({combined_confidence:.2f}) - providing targeted guidance",
                "alternative_actions": self._suggest_alternative_actions(query_category)
            }
        
        # Very low confidence - acknowledge limitation
        else:
            return {
                "should_fallback": True,
                "fallback_type": "acknowledge_limitation",
                "message": self._generate_limitation_acknowledgment(query_category, query, query_analysis),
                "reasoning": f"Very low confidence ({combined_confidence:.2f}) - acknowledging limitation",
                "alternative_actions": self._suggest_alternative_actions(query_category, include_external=True)
            }
    
    def _generate_confidence_qualifier(self, category: str) -> str:
        """Generate confidence qualifier messages for medium confidence responses"""
        qualifiers = {
            "course_specific": "Based on the information I have access to, ",
            "prerequisites": "According to the available academic requirements, ",
            "degree_requirements": "From the degree program information I can access, ",
            "academic_planning": "Based on typical academic planning guidelines, ",
            "scheduling": "According to general scheduling patterns, ",
            "financial_aid": "Based on general financial aid information, ",
            "transfer_credits": "According to standard transfer credit policies, ",
            "academic_policies": "Based on the policy information available to me, ",
            "career_guidance": "According to general career guidance principles, ",
            "academic_support": "Based on typical academic support resources, ",
            "general_information": "Based on the information I have available, "
        }
        
        return qualifiers.get(category, qualifiers["general_information"])
    
    def _generate_targeted_guidance(self, category: str, query: str, query_analysis: Dict) -> str:
        """Generate targeted guidance messages for low confidence situations"""
        
        guidance_templates = {
            "course_specific": {
                "high_specificity": "I have limited information about that specific course. For detailed course information including prerequisites, credit hours, and current offerings, I recommend checking the current course catalog or contacting the academic department directly.",
                "low_specificity": "To help you with course information, could you provide the specific course code (e.g., CS 101) or course title? This will help me give you more accurate details about prerequisites, credit hours, and availability."
            },
            "prerequisites": {
                "high_specificity": "I don't have complete prerequisite information for that specific course. For the most current and accurate prerequisite requirements, please consult the official course catalog or speak with an academic advisor in the relevant department.",
                "low_specificity": "To help you with prerequisite information, could you specify which course you're asking about? Please provide the course code (e.g., MATH 201) so I can give you accurate prerequisite details."
            },
            "degree_requirements": {
                "high_specificity": "I have limited information about those specific degree requirements. For comprehensive and up-to-date degree requirements, I recommend consulting with an academic advisor in your program or reviewing the current academic catalog for your specific major.",
                "low_specificity": "To provide accurate degree requirement information, could you specify your major or the specific degree program you're asking about? This will help me give you more relevant guidance."
            },
            "scheduling": {
                "high_specificity": "I don't have access to current scheduling information. For the most up-to-date course schedules, times, and availability, please check the online course schedule system or contact the registrar's office.",
                "low_specificity": "To help with scheduling questions, could you specify which courses or semester you're planning for? Also note that I don't have access to real-time scheduling data."
            },
            "financial_aid": {
                "high_specificity": "For specific financial aid information, eligibility requirements, and application procedures, I recommend contacting the Financial Aid office directly. They can provide personalized guidance based on your individual situation.",
                "low_specificity": "Financial aid options vary greatly based on individual circumstances. Could you specify what type of financial assistance you're looking for (scholarships, grants, loans, work-study)? For personalized advice, the Financial Aid office is your best resource."
            },
            "transfer_credits": {
                "high_specificity": "Transfer credit evaluation requires review of specific courses and institutions. For accurate transfer credit information, please contact the Registrar's office or Transfer Credit Evaluation office with your transcripts.",
                "low_specificity": "Transfer credit policies depend on many factors including your previous institution and specific courses. Could you provide more details about where you're transferring from and what credits you're hoping to transfer?"
            },
            "academic_policies": {
                "high_specificity": "For specific policy details and current regulations, I recommend consulting the official student handbook or contacting the appropriate administrative office for the most accurate and up-to-date information.",
                "low_specificity": "Academic policies can be complex and vary by situation. Could you specify which particular policy or procedure you're asking about? This will help me point you to the right resources."
            },
            "career_guidance": {
                "high_specificity": "For specific career guidance and industry insights, I recommend connecting with the Career Services office. They can provide personalized career counseling, industry connections, and current job market information.",
                "low_specificity": "Career planning is highly individual. Could you share more about your academic background, interests, or the specific career area you're exploring? The Career Services office would also be an excellent resource for personalized guidance."
            },
            "academic_support": {
                "high_specificity": "For specific academic support services and resources, I recommend contacting the Academic Success Center or Student Support Services. They can connect you with tutoring, study groups, and other learning resources.",
                "low_specificity": "Academic support needs vary by subject and learning style. Could you specify what type of academic help you're looking for? The Academic Success Center offers various support services that might be helpful."
            },
            "general_information": {
                "high_specificity": "I don't have specific information about that topic. For accurate and detailed information, I recommend contacting the appropriate university office or checking the official university website.",
                "low_specificity": "To provide you with the most helpful guidance, could you be more specific about what information you're looking for? This will help me direct you to the right resources or provide more targeted assistance."
            }
        }
        
        # Determine specificity level
        specificity = "high_specificity" if query_analysis.get("specificity_score", 0) > 0.5 else "low_specificity"
        
        # Get appropriate guidance template
        template = guidance_templates.get(category, guidance_templates["general_information"])
        return template.get(specificity, template["low_specificity"])
    
    def _generate_limitation_acknowledgment(self, category: str, query: str, query_analysis: Dict) -> str:
        """Generate limitation acknowledgment for very low confidence situations"""
        
        acknowledgments = {
            "course_specific": "I don't have detailed information about that specific course in my knowledge base. For comprehensive course details, please consult the official course catalog, contact the academic department, or speak with your academic advisor.",
            
            "prerequisites": "I don't have access to current prerequisite information for that course. Prerequisites can change, so I recommend checking the most recent course catalog or contacting the academic department for accurate requirements.",
            
            "degree_requirements": "I don't have complete degree requirement information for that program. Degree requirements are complex and can vary by admission year and program track. Please consult with an academic advisor in your specific program for accurate guidance.",
            
            "scheduling": "I don't have access to current course scheduling information. Course schedules, times, and availability change each semester. Please check the online course registration system or contact the registrar's office for up-to-date scheduling information.",
            
            "financial_aid": "Financial aid information is highly individual and changes frequently. I recommend contacting the Financial Aid office directly for personalized assistance with your specific financial aid questions and eligibility.",
            
            "transfer_credits": "Transfer credit evaluation requires detailed review of coursework and institutional accreditation. Please contact the Registrar's office or Transfer Credit office with your official transcripts for accurate evaluation.",
            
            "academic_policies": "Academic policies can be complex and may have recent updates. For the most current and accurate policy information, please consult the official student handbook or contact the appropriate administrative office.",
            
            "career_guidance": "Career planning is highly personalized and depends on many individual factors. I recommend scheduling an appointment with Career Services for personalized career counseling and industry-specific guidance.",
            
            "academic_support": "Academic support needs are individual and vary by subject area. Please contact the Academic Success Center or Student Support Services to discuss your specific needs and available resources.",
            
            "general_information": "You might want to check the university website or contact the relevant office directly for the most up-to-date information on that."
        }
        
        base_acknowledgment = acknowledgments.get(category, acknowledgments["general_information"])
        
        # Add natural, conversational preamble
        natural_preambles = [
            "I don't have the specific details on that topic right now. ",
            "That's not something I have detailed info about at the moment. ",
            "I wish I had more specific information about that for you. ",
            "I don't have those particular details in my knowledge base. "
        ]
        
        import random
        preamble = random.choice(natural_preambles)
        
        return preamble + base_acknowledgment
    
    def _suggest_alternative_actions(self, category: str, include_external: bool = False) -> List[str]:
        """Suggest alternative actions based on query category"""
        
        actions = {
            "course_specific": [
                "Check the current course catalog for detailed course descriptions",
                "Contact the academic department offering the course",
                "Speak with your academic advisor"
            ],
            "prerequisites": [
                "Review the course catalog for prerequisite information",
                "Contact the department offering the course",
                "Meet with an academic advisor to discuss course planning"
            ],
            "degree_requirements": [
                "Schedule a meeting with your academic advisor",
                "Review your degree audit in the student portal",
                "Consult the current academic catalog for your program"
            ],
            "scheduling": [
                "Check the online course registration system",
                "Contact the registrar's office",
                "Look for scheduling information on the department website"
            ],
            "financial_aid": [
                "Visit or call the Financial Aid office",
                "Complete the FAFSA if you haven't already",
                "Explore scholarship opportunities on the university website"
            ],
            "transfer_credits": [
                "Contact the Registrar's office for transfer evaluation",
                "Submit official transcripts for evaluation",
                "Review transfer credit policies in the academic catalog"
            ],
            "academic_policies": [
                "Consult the student handbook",
                "Contact the appropriate administrative office",
                "Check the university website for policy updates"
            ],
            "career_guidance": [
                "Schedule an appointment with Career Services",
                "Attend career fairs and networking events",
                "Connect with alumni in your field of interest"
            ],
            "academic_support": [
                "Contact the Academic Success Center",
                "Look into tutoring services",
                "Join study groups for your courses"
            ],
            "general_information": [
                "Check the university website",
                "Contact the appropriate office",
                "Speak with your academic advisor"
            ]
        }
        
        base_actions = actions.get(category, actions["general_information"])
        
        if include_external:
            # Add external resources for very low confidence situations
            external_actions = [
                "Search the university website for official information",
                "Call the main university information line",
                "Visit the campus information desk"
            ]
            return base_actions + external_actions
        
        return base_actions
    
    def generate_enhanced_response(self, original_response: Dict, fallback_decision: Dict) -> Dict:
        """Generate enhanced response with appropriate fallback integration"""
        
        if not fallback_decision["should_fallback"]:
            return original_response
        
        fallback_type = fallback_decision["fallback_type"]
        enhanced_response = original_response.copy()
        
        if fallback_type == "confidence_qualifier":
            # Prepend confidence qualifier to the response
            qualifier = fallback_decision["fallback_message"]
            enhanced_response["answer"] = qualifier + enhanced_response["answer"]
            
        elif fallback_type == "targeted_guidance":
            # Append targeted guidance to the response
            guidance = fallback_decision["fallback_message"]
            enhanced_response["answer"] += f"\n\n{guidance}"
            
            # Add alternative actions to suggested questions
            alt_actions = fallback_decision.get("alternative_actions", [])
            if alt_actions:
                enhanced_response["suggested_questions"] = enhanced_response.get("suggested_questions", []) + alt_actions[:2]
            
        elif fallback_type == "acknowledge_limitation":
            # Replace or append limitation acknowledgment
            limitation_msg = fallback_decision["fallback_message"]
            
            # If original response is generic, replace it
            if enhanced_response.get("confidence", 3) <= 2:
                enhanced_response["answer"] = limitation_msg
            else:
                enhanced_response["answer"] += f"\n\n{limitation_msg}"
            
            # Add alternative actions
            alt_actions = fallback_decision.get("alternative_actions", [])
            enhanced_response["suggested_questions"] = alt_actions[:3]
        
        # Add fallback metadata
        enhanced_response["fallback_applied"] = {
            "type": fallback_type,
            "reasoning": fallback_decision.get("strategy_reasoning", ""),
            "confidence_analysis": fallback_decision["confidence_breakdown"],
            "query_category": fallback_decision["query_category"]
        }
        
        return enhanced_response
    
    def get_fallback_analytics(self, fallback_decision: Dict) -> Dict:
        """Generate analytics about fallback decisions for monitoring and improvement"""
        
        return {
            "fallback_triggered": fallback_decision["should_fallback"],
            "fallback_type": fallback_decision.get("fallback_type", "none"),
            "query_category": fallback_decision["query_category"],
            "confidence_scores": fallback_decision["confidence_breakdown"],
            "query_characteristics": fallback_decision["query_analysis"],
            "strategy_reasoning": fallback_decision.get("strategy_reasoning", ""),
            "improvement_suggestions": self._generate_improvement_suggestions(fallback_decision)
        }
    
    def _generate_improvement_suggestions(self, fallback_decision: Dict) -> List[str]:
        """Generate suggestions for improving responses based on fallback analysis"""
        
        suggestions = []
        confidence_breakdown = fallback_decision["confidence_breakdown"]
        query_analysis = fallback_decision["query_analysis"]
        
        # Low retrieval confidence suggestions
        if confidence_breakdown["retrieval_original"] < 0.5:
            suggestions.append("Consider expanding knowledge base for this topic area")
            suggestions.append("Review document chunking strategy for better retrieval")
        
        # Low LLM confidence suggestions
        if confidence_breakdown["llm_original"] < 0.6:
            suggestions.append("Review prompt engineering for this query type")
            suggestions.append("Consider providing more context to LLM")
        
        # Query clarity suggestions
        if query_analysis.get("clarity_score", 1.0) < 0.6:
            suggestions.append("Implement clarifying question prompts for unclear queries")
        
        # Specificity suggestions
        if query_analysis.get("specificity_score", 1.0) < 0.4:
            suggestions.append("Guide users toward more specific questions")
            suggestions.append("Provide examples of well-formed questions")
        
        return suggestions