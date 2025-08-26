"""
Advanced Conversation Context Manager
Handles conversation state tracking, entity extraction, and context building for enhanced chatbot intelligence
"""

import json
import re
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from sentence_transformers import SentenceTransformer
from collections import defaultdict, Counter

class ConversationContextManager:
    """Advanced conversation context management with state tracking and entity persistence"""
    
    def __init__(self):
        # Lazy loading - only load model when actually needed
        self.model = None
        
        # Academic domain knowledge patterns
        self.academic_patterns = {
            "courses": r'\b([A-Z]{2,5})\s*(\d{3,4})\b',  # e.g., CS 101, MATH 1001
            "gpas": r'\b(\d\.\d{1,2}|\d)\s*(gpa|GPA)\b',
            "semesters": r'\b(fall|spring|summer|winter)\s*(\d{4}|\d{2})\b',
            "degrees": r'\b(bachelor|master|doctorate|phd|bs|ba|ms|ma)\b',
            "years": r'\b(freshman|sophomore|junior|senior|first|second|third|fourth)\s*(year)?\b'
        }
        
        # Academic topic categories for intelligent context building
        self.topic_categories = {
            "course_planning": ["course", "class", "prerequisite", "corequisite", "sequence"],
            "degree_requirements": ["requirement", "major", "minor", "degree", "graduation"],
            "scheduling": ["schedule", "time", "semester", "registration", "when"],
            "academic_policies": ["policy", "rule", "regulation", "procedure", "deadline"],
            "financial_aid": ["financial", "aid", "scholarship", "tuition", "cost", "fee"],
            "transfer_credits": ["transfer", "credit", "articulation", "previous"],
            "career_planning": ["career", "job", "internship", "employment", "future"]
        }
        
        # Conversation states for adaptive responses
        self.conversation_states = {
            "initial": "First interaction, establish rapport and understand needs",
            "exploratory": "User exploring options, provide broad guidance", 
            "focused": "User has specific questions, provide detailed information",
            "planning": "User making decisions, provide structured guidance",
            "troubleshooting": "User has problems, provide solutions and alternatives"
        }
        
    def _get_model(self):
        """Lazy load the embedding model only when needed"""
        if self.model is None:
            try:
                print("Loading BAAI/bge-large-en-v1.5 for context analysis...")
                self.model = SentenceTransformer("BAAI/bge-large-en-v1.5")
                print("Successfully loaded BAAI/bge-large-en-v1.5")
            except Exception as e:
                print(f"Warning: Failed to load BAAI/bge-large-en-v1.5: {e}")
                print("Falling back to BAAI/bge-small-en")
                try:
                    self.model = SentenceTransformer("BAAI/bge-small-en")
                except Exception as e2:
                    print(f"Warning: Failed to load BAAI/bge-small-en: {e2}")
                    print("Falling back to all-MiniLM-L6-v2")
                    self.model = SentenceTransformer("all-MiniLM-L6-v2")
        return self.model
    
    def build_enhanced_context(self, history: List[Dict], user_email: str, current_query: str) -> Dict:
        """Build comprehensive conversation context for enhanced LLM responses"""
        
        context = {
            "conversation_summary": self._generate_conversation_summary(history),
            "recent_topics": self._extract_recent_topics(history[-6:]),  # Last 3 exchanges
            "mentioned_entities": self._extract_entities(history),
            "user_profile": self._get_user_context_profile(user_email, history),
            "conversation_state": self._determine_conversation_state(history, current_query),
            "recent_queries": self._get_recent_queries(history[-4:]),  # Last 2 exchanges
            "topic_progression": self._analyze_topic_progression(history),
            "context_continuity": self._build_context_continuity(history, current_query),
            "conversation_metadata": {
                "turn_count": len(history),
                "user_message_count": len([msg for msg in history if msg["sender"] == "user"]),
                "last_interaction": datetime.now().isoformat(),
                "conversation_length": self._calculate_conversation_length(history)
            }
        }
        
        return context
    
    def _generate_conversation_summary(self, history: List[Dict]) -> str:
        """Create intelligent conversation summary focusing on academic context"""
        if len(history) < 2:
            return "New conversation beginning"
        
        # Extract main topics discussed
        topics = []
        entities = {"courses": set(), "majors": set(), "requirements": set()}
        
        for msg in history:
            if msg["sender"] == "user":
                # Extract topics
                topic = self._classify_message_topic(msg["text"])
                if topic != "general":
                    topics.append(topic)
                
                # Extract entities for context
                msg_entities = self._extract_entities_from_text(msg["text"])
                for key in entities:
                    entities[key].update(msg_entities.get(key, []))
        
        # Build intelligent summary
        topic_counts = Counter(topics)
        main_topics = [topic for topic, count in topic_counts.most_common(3)]
        
        summary_parts = []
        
        if main_topics:
            summary_parts.append(f"Discussion about {', '.join(main_topics)}")
        
        if entities["courses"]:
            courses_list = list(entities["courses"])[:3]  # Limit to prevent long summaries
            summary_parts.append(f"Courses mentioned: {', '.join(courses_list)}")
        
        if entities["majors"]:
            majors_list = list(entities["majors"])[:2]
            summary_parts.append(f"Academic programs: {', '.join(majors_list)}")
        
        return "; ".join(summary_parts) if summary_parts else "General academic advising discussion"
    
    def _extract_recent_topics(self, recent_history: List[Dict]) -> List[str]:
        """Extract and categorize recent conversation topics"""
        topics = []
        
        for msg in recent_history:
            if msg["sender"] == "user":
                topic = self._classify_message_topic(msg["text"])
                if topic != "general":
                    topics.append(topic)
        
        # Return unique topics in order of appearance
        return list(dict.fromkeys(topics))  # Preserves order while removing duplicates
    
    def _classify_message_topic(self, text: str) -> str:
        """Classify message into academic topic categories"""
        text_lower = text.lower()
        
        for category, keywords in self.topic_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _extract_entities(self, history: List[Dict]) -> Dict:
        """Extract and track academic entities mentioned throughout conversation"""
        entities = {
            "courses": set(),
            "majors": set(),
            "semesters": set(), 
            "requirements": set(),
            "gpas": set(),
            "years": set()
        }
        
        for msg in history:
            if msg["sender"] == "user":
                msg_entities = self._extract_entities_from_text(msg["text"])
                for key in entities:
                    entities[key].update(msg_entities.get(key, []))
        
        # Convert sets to lists for JSON serialization and limit size
        return {k: list(v)[:10] for k, v in entities.items()}  # Limit to 10 items per category
    
    def _extract_entities_from_text(self, text: str) -> Dict:
        """Extract academic entities from a single text message"""
        entities = defaultdict(list)
        
        # Extract course codes
        course_matches = re.findall(self.academic_patterns["courses"], text, re.IGNORECASE)
        for dept, num in course_matches:
            entities["courses"].append(f"{dept.upper()} {num}")
        
        # Extract GPAs
        gpa_matches = re.findall(self.academic_patterns["gpas"], text, re.IGNORECASE)
        for gpa, _ in gpa_matches:
            entities["gpas"].append(gpa)
        
        # Extract semesters
        semester_matches = re.findall(self.academic_patterns["semesters"], text, re.IGNORECASE)
        for season, year in semester_matches:
            entities["semesters"].append(f"{season.title()} {year}")
        
        # Extract degree types
        degree_matches = re.findall(self.academic_patterns["degrees"], text, re.IGNORECASE)
        entities["majors"].extend([degree.upper() for degree in degree_matches])
        
        # Extract academic years
        year_matches = re.findall(self.academic_patterns["years"], text, re.IGNORECASE)
        for year_level, _ in year_matches:
            entities["years"].append(year_level.title())
        
        # Extract common majors and requirements (basic keyword matching)
        text_lower = text.lower()
        common_majors = ["computer science", "engineering", "business", "psychology", "biology", 
                        "mathematics", "english", "history", "chemistry", "physics"]
        for major in common_majors:
            if major in text_lower:
                entities["majors"].append(major.title())
        
        common_requirements = ["prerequisite", "corequisite", "general education", "core requirement",
                              "elective", "practicum", "internship", "thesis", "capstone"]
        for req in common_requirements:
            if req in text_lower:
                entities["requirements"].append(req.title())
        
        return dict(entities)
    
    def _get_user_context_profile(self, user_email: str, history: List[Dict]) -> Dict:
        """Build user context profile from conversation history"""
        # Extract profile information from conversation
        profile = {
            "academic_level": "unknown",
            "major": "unknown",
            "interests": [],
            "conversation_count": len([msg for msg in history if msg["sender"] == "user"]),
            "frequent_topics": [],
            "academic_goals": []
        }
        
        # Analyze conversation patterns to infer user profile
        user_messages = [msg["text"] for msg in history if msg["sender"] == "user"]
        
        if user_messages:
            # Infer academic level
            text_combined = " ".join(user_messages).lower()
            
            if any(word in text_combined for word in ["freshman", "first year", "starting"]):
                profile["academic_level"] = "freshman"
            elif any(word in text_combined for word in ["sophomore", "second year"]):
                profile["academic_level"] = "sophomore"
            elif any(word in text_combined for word in ["junior", "third year"]):
                profile["academic_level"] = "junior"
            elif any(word in text_combined for word in ["senior", "fourth year", "graduating"]):
                profile["academic_level"] = "senior"
            elif any(word in text_combined for word in ["graduate", "masters", "phd", "doctoral"]):
                profile["academic_level"] = "graduate"
            
            # Extract frequent topics
            topics = [self._classify_message_topic(msg) for msg in user_messages]
            topic_counts = Counter(topics)
            profile["frequent_topics"] = [topic for topic, count in topic_counts.most_common(3)]
            
            # Extract mentioned majors - only if explicitly stated as their program
            entities = self._extract_entities(history)
            # Only infer major if user explicitly states it (e.g., "I am doing", "I'm in", "my major is")
            for msg in user_messages:
                if any(phrase in msg.lower() for phrase in ["i am doing", "i'm doing", "i am in", "i'm in", "my major is", "my program is"]):
                    if entities.get("majors"):
                        profile["major"] = entities["majors"][0]
                        break
        
        return profile
    
    def _determine_conversation_state(self, history: List[Dict], current_query: str) -> str:
        """Determine current conversation state for adaptive responses"""
        conversation_length = len(history)
        recent_user_messages = [msg["text"] for msg in history[-4:] if msg["sender"] == "user"]
        
        # State determination logic
        if conversation_length == 0:
            return "initial"
        elif conversation_length < 4:
            return "exploratory"
        else:
            # Analyze recent messages for state indicators
            current_text = current_query.lower()
            recent_text = " ".join(recent_user_messages).lower()
            
            # Planning indicators
            planning_keywords = ["should i", "what if", "which option", "help me choose", "plan", "schedule"]
            if any(keyword in current_text for keyword in planning_keywords):
                return "planning"
            
            # Troubleshooting indicators  
            trouble_keywords = ["problem", "issue", "error", "can't", "unable", "failed", "wrong"]
            if any(keyword in current_text for keyword in trouble_keywords):
                return "troubleshooting"
            
            # Focused discussion indicators
            specific_keywords = ["prerequisite", "requirement", "specific", "exactly", "precise"]
            if any(keyword in recent_text for keyword in specific_keywords):
                return "focused"
            
            return "exploratory"
    
    def _get_recent_queries(self, recent_history: List[Dict]) -> List[str]:
        """Extract recent user queries for similarity checking"""
        return [msg["text"] for msg in recent_history if msg["sender"] == "user"]
    
    def _analyze_topic_progression(self, history: List[Dict]) -> List[Dict]:
        """Analyze how conversation topics have evolved"""
        progression = []
        
        for i, msg in enumerate(history):
            if msg["sender"] == "user":
                topic = self._classify_message_topic(msg["text"])
                progression.append({
                    "turn": i // 2 + 1,  # Conversation turn number
                    "topic": topic,
                    "message": msg["text"][:50] + "..." if len(msg["text"]) > 50 else msg["text"]
                })
        
        return progression[-5:]  # Return last 5 topic progressions
    
    def _build_context_continuity(self, history: List[Dict], current_query: str) -> Dict:
        """Build context continuity information for seamless conversation flow"""
        if len(history) < 2:
            return {"has_continuity": False}
        
        # Extract entities from current query
        current_entities = self._extract_entities_from_text(current_query)
        
        # Check for entity references in previous conversation
        previous_entities = self._extract_entities(history)
        
        # Find overlapping entities (continuity indicators)
        continuity_entities = {}
        for entity_type in current_entities:
            overlap = set(current_entities[entity_type]) & set(previous_entities.get(entity_type, []))
            if overlap:
                continuity_entities[entity_type] = list(overlap)
        
        # Find the most recent relevant context
        relevant_context = self._find_most_relevant_previous_context(history, current_query)
        
        return {
            "has_continuity": bool(continuity_entities),
            "continuity_entities": continuity_entities,
            "relevant_previous_context": relevant_context,
            "can_reference_previous": len(history) >= 2
        }
    
    def _find_most_relevant_previous_context(self, history: List[Dict], current_query: str) -> Optional[Dict]:
        """Find the most relevant previous exchange for context reference (simplified for speed)"""
        if len(history) < 2:
            return None
        
        # Get recent user-assistant pairs (simplified - just get last exchange)
        for i in range(len(history) - 2, -1, -2):
            if i >= 0 and i + 1 < len(history):
                user_msg = history[i]
                assistant_msg = history[i + 1]
                if user_msg["sender"] == "user" and assistant_msg["sender"] == "assistant":
                    return {
                        "user_query": user_msg["text"],
                        "assistant_response": assistant_msg["text"],
                        "turn": i // 2 + 1,
                        "similarity_score": 0.8  # Assume recent context is relevant
                    }
        
        return None
    
    def _calculate_conversation_length(self, history: List[Dict]) -> str:
        """Calculate conversation length category"""
        length = len(history)
        if length < 4:
            return "short"
        elif length < 10:
            return "medium" 
        else:
            return "long"
    
    def format_context_for_llm(self, context: Dict) -> str:
        """Format context naturally for conversational responses"""
        context_parts = []
        
        # Only include truly relevant context - keep it minimal and natural
        entities = context["mentioned_entities"]
        profile = context["user_profile"]
        
        # Student info (only if explicitly confirmed by user)
        # DISABLED: Don't assume major unless explicitly confirmed
        # if profile["major"] != "unknown":
        #     context_parts.append(f"Student is in {profile['major']}")
        
        # Check for explicit interest statements in recent conversation
        recent_interest = self._extract_recent_interest(context["recent_queries"])
        if recent_interest:
            context_parts.append(f"User expressed interest in: {recent_interest}")
        
        # Add progress indicators for encouragement
        progress_indicators = self._detect_progress_indicators(context["recent_queries"], entities)
        if progress_indicators:
            context_parts.append(f"Student progress: {progress_indicators}")
        
        # Add program context consistency reminder
        if entities["courses"]:
            # Determine primary program from mentioned courses
            course_prefixes = [course.split()[0] for course in entities["courses"] if ' ' in course]
            if course_prefixes:
                primary_prefix = max(set(course_prefixes), key=course_prefixes.count)
                context_parts.append(f"Focus on {primary_prefix} program courses")
        
        # Important courses mentioned (most recent only)
        if entities["courses"]:
            recent_courses = entities["courses"][-2:]  # Last 2 courses only
            context_parts.append(f"Previously discussed: {', '.join(recent_courses)}")
        
        # Return minimal context or nothing if no relevant context
        return " | ".join(context_parts) if context_parts else ""
    
    def _extract_recent_interest(self, recent_queries: List[str]) -> str:
        """Extract explicit interest statements from recent queries"""
        for query in reversed(recent_queries):  # Check most recent first
            query_lower = query.lower()
            if any(phrase in query_lower for phrase in ["i am interested in", "i'm interested in", "interested in"]):
                # Extract what they're interested in
                for phrase in ["i am interested in", "i'm interested in", "interested in"]:
                    if phrase in query_lower:
                        interest_part = query_lower.split(phrase, 1)[1].strip()
                        # Clean up the interest statement
                        interest_part = interest_part.replace("cis with data science", "MS-CIS Data Science")
                        interest_part = interest_part.replace("computer science", "Computer Science")
                        interest_part = interest_part.replace("data science", "Data Science")
                        return interest_part[:50]  # Limit length
        return ""
    
    def _detect_progress_indicators(self, recent_queries: List[str], entities: Dict) -> str:
        """Detect indicators of student progress for encouragement"""
        progress_signals = []
        
        query_text = " ".join(recent_queries).lower()
        
        # Positive progress indicators
        if any(phrase in query_text for phrase in ["completed", "finished", "done with", "passed"]):
            progress_signals.append("completing coursework")
        
        if any(phrase in query_text for phrase in ["planning", "next semester", "schedule"]):
            progress_signals.append("actively planning ahead")
            
        if any(phrase in query_text for phrase in ["prerequisites", "requirements"]):
            progress_signals.append("researching requirements")
            
        if len(entities.get("courses", [])) > 2:
            progress_signals.append("exploring multiple courses")
            
        # Challenge indicators (for supportive responses)
        if any(phrase in query_text for phrase in ["difficult", "hard", "struggling", "confused", "overwhelmed"]):
            progress_signals.append("facing challenges (needs support)")
            
        return ", ".join(progress_signals[:2]) if progress_signals else ""
    
    def get_conversation_insights(self, context: Dict) -> Dict:
        """Generate insights about the conversation for debugging and improvement"""
        return {
            "conversation_maturity": context["conversation_metadata"]["conversation_length"],
            "user_engagement": len(context["recent_topics"]),
            "entity_richness": sum(len(entities) for entities in context["mentioned_entities"].values()),
            "context_continuity_strength": context["context_continuity"]["has_continuity"],
            "conversation_focus": context["conversation_state"],
            "topics_covered": len(set(context["recent_topics"])),
            "recommendation": self._generate_conversation_recommendation(context)
        }
    
    def _generate_conversation_recommendation(self, context: Dict) -> str:
        """Generate recommendation for conversation handling"""
        state = context["conversation_state"]
        topics = context["recent_topics"]
        entities = context["mentioned_entities"]
        
        if state == "initial":
            return "Establish rapport and understand user needs"
        elif state == "exploratory" and len(topics) > 2:
            return "Help user focus on specific area of interest"
        elif state == "focused" and any(len(e) > 0 for e in entities.values()):
            return "Provide detailed, specific information about mentioned entities"
        elif state == "planning":
            return "Offer structured guidance and next steps"
        elif state == "troubleshooting":
            return "Focus on problem-solving and alternative solutions"
        else:
            return "Continue supportive dialogue and gather more context"