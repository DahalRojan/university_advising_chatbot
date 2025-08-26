"""
Enhanced Academic Advisor System
Professional, personalized AI advisor with real-time student context integration
"""

from typing import Dict, List, Optional, Any
import json
import time
from datetime import datetime, timedelta
from functools import lru_cache
from features.onboarding.onboarding_api import OnboardingAPI


class PersonalizedAdvisorEngine:
    """
    Core engine for context-aware, personalized academic advising
    """
    
    def __init__(self, onboarding_api: OnboardingAPI):
        self.onboarding_api = onboarding_api
        self.response_cache = {}
        self.personality_templates = self._load_advisor_personalities()
        
    def _load_advisor_personalities(self) -> Dict[str, str]:
        """Load different advisor personality templates"""
        return {
            "supportive": """You are Dr. Knight, a warm and encouraging academic advisor at Gannon University with 15 years of experience. You genuinely care about each student's success and always provide practical, actionable advice. Your responses are professional yet approachable, and you remember important details about your students.""",
            
            "analytical": """You are Dr. Knight, a detail-oriented academic advisor who excels at breaking down complex academic pathways. You provide structured, logical guidance while maintaining a supportive tone. You're known for helping students create clear, achievable academic plans.""",
            
            "motivational": """You are Dr. Knight, an inspiring academic advisor who helps students see their potential. You balance realistic guidance with encouragement, helping students overcome challenges and achieve their academic goals. You're particularly skilled at helping students navigate difficult decisions."""
        }
    
    def get_student_context(self, user_email: str, user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Retrieve comprehensive student context with caching
        Fast context retrieval for real-time personalization
        """
        try:
            # Get student profile with Microsoft name integration
            profile_data = self.onboarding_api.get_student_dashboard(user_email, 
                                                                   user_data=user_data or {"email": user_email})
            
            if not profile_data:
                return {"status": "new_student", "context": "limited"}
            
            # Build comprehensive context
            context = {
                "personal_info": {
                    "first_name": profile_data.first_name,
                    "last_name": profile_data.last_name,
                    "preferred_name": profile_data.preferred_name or profile_data.first_name,
                    "email": user_email
                },
                "academic_profile": {
                    "student_type": profile_data.student_type,
                    "academic_level": profile_data.academic_level,
                    "enrollment_status": profile_data.enrollment_status,
                    "primary_major": profile_data.primary_major,
                    "degree_program": getattr(profile_data, 'degree_program', None),
                    "cumulative_gpa": profile_data.cumulative_gpa,
                    "expected_graduation": profile_data.expected_graduation
                },
                "completion_status": {
                    "onboarding_complete": profile_data.is_onboarding_complete,
                    "profile_completion": profile_data.profile_completion_percentage,
                    "progress_percentage": profile_data.onboarding_progress_percentage
                },
                "engagement_metrics": {
                    "active_recommendations": profile_data.active_recommendations_count,
                    "course_interests": profile_data.course_interests_count,
                    "last_updated": profile_data.updated_at
                }
            }
            
            # Get academic goals for personalized recommendations
            goals = self.onboarding_api.get_student_academic_goals(user_email)
            context["academic_goals"] = []
            
            if goals:
                for goal in goals:
                    try:
                        # Handle both dict and object types
                        if isinstance(goal, dict):
                            context["academic_goals"].append({
                                "type": goal.get("goal_type", ""),
                                "category": goal.get("goal_category", ""),
                                "description": goal.get("goal_description", ""),
                                "priority": goal.get("priority_level", 5),
                                "target_date": goal.get("target_completion_date", "")
                            })
                        else:
                            # Handle object attributes
                            context["academic_goals"].append({
                                "type": getattr(goal, 'goal_type', ''),
                                "category": getattr(goal, 'goal_category', ''),
                                "description": getattr(goal, 'goal_description', ''),
                                "priority": getattr(goal, 'priority_level', 5),
                                "target_date": getattr(goal, 'target_completion_date', '')
                            })
                    except Exception as goal_error:
                        print(f"Error processing goal: {goal_error}")
                        continue
            
            # Get course interests for contextual course recommendations
            interests = self.onboarding_api.get_student_course_interests(user_email)
            context["course_interests"] = []
            
            if interests:
                for interest in interests:
                    try:
                        # Handle both dict and object types
                        if isinstance(interest, dict):
                            context["course_interests"].append({
                                "course_code": interest.get("course_code", ""),
                                "interest_level": interest.get("interest_level", ""),
                                "planned_semester": interest.get("planned_semester", ""),
                                "reason": interest.get("reason", "")
                            })
                        else:
                            # Handle object attributes
                            context["course_interests"].append({
                                "course_code": getattr(interest, 'course_code', ''),
                                "interest_level": getattr(interest, 'interest_level', ''),
                                "planned_semester": getattr(interest, 'planned_semester', ''),
                                "reason": getattr(interest, 'reason', '')
                            })
                    except Exception as interest_error:
                        print(f"Error processing interest: {interest_error}")
                        continue
            
            # Get actual completed courses from academic history
            try:
                academic_history = self.onboarding_api.get_student_academic_history(user_email)
                context["completed_courses"] = []
                context["current_courses"] = []
                
                if academic_history:
                    for course in academic_history:
                        try:
                            # Handle both dict and object types for course history
                            if isinstance(course, dict):
                                course_info = {
                                    "course_code": course.get("course_code", ""),
                                    "course_title": course.get("course_title", ""),
                                    "semester": course.get("semester", ""),
                                    "year": course.get("year", ""),
                                    "grade": course.get("grade", ""),
                                    "credits": course.get("credits_earned", ""),
                                    "status": course.get("status", ""),
                                    "institution": course.get("institution", "")
                                }
                            else:
                                # Handle object attributes
                                course_info = {
                                    "course_code": getattr(course, 'course_code', ''),
                                    "course_title": getattr(course, 'course_title', ''),
                                    "semester": getattr(course, 'semester', ''),
                                    "year": getattr(course, 'year', ''),
                                    "grade": getattr(course, 'grade', ''),
                                    "credits": getattr(course, 'credits_earned', ''),
                                    "status": getattr(course, 'status', ''),
                                    "institution": getattr(course, 'institution', '')
                                }
                            
                            # Categorize courses by status
                            status = course_info.get("status", "").lower()
                            if status in ["completed", "passed"]:
                                context["completed_courses"].append(course_info)
                            elif status in ["enrolled", "in_progress", "current"]:
                                context["current_courses"].append(course_info)
                                
                        except Exception as course_error:
                            print(f"Error processing course history: {course_error}")
                            continue
                            
            except Exception as history_error:
                print(f"Error retrieving academic history: {history_error}")
                context["completed_courses"] = []
                context["current_courses"] = []
            
            return context
            
        except Exception as e:
            print(f"Error retrieving student context for {user_email}: {e}")
            return {"status": "error", "context": "limited"}
    
    def build_personalized_prompt(self, user_email: str, query: str, 
                                 context_docs: str, history: List[Dict], 
                                 user_data: Optional[Dict] = None) -> str:
        """
        Build a highly personalized system prompt using student data
        """
        student_context = self.get_student_context(user_email, user_data)
        
        # Select advisor personality based on student profile
        personality_key = self._select_advisor_personality(student_context)
        base_personality = self.personality_templates[personality_key]
        
        # Build personalized context
        personal_context = self._build_personal_context(student_context)
        academic_context = self._build_academic_context(student_context)
        goal_context = self._build_goal_context(student_context)
        course_history_context = self._build_course_history_context(student_context)
        
        # Build comprehensive prompt
        prompt = f"""{base_personality}

STUDENT PROFILE:
{personal_context}

ACADEMIC CONTEXT:
{academic_context}

STUDENT GOALS & INTERESTS:
{goal_context}

COURSE HISTORY:
{course_history_context}

CONVERSATION CONTEXT:
Previous conversation length: {len(history)} messages
Current query focus: {self._analyze_query_intent(query)}

KNOWLEDGE BASE:
{context_docs}

ADVISOR GUIDELINES:
1. **Personalization**: Always use the student's preferred name and reference their specific major/goals
2. **Context Awareness**: Remember their academic level, enrollment status, and interests
3. **Goal Alignment**: Connect advice to their stated academic and career goals
4. **Professional Tone**: Maintain warmth while being authoritative and knowledgeable
5. **Actionable Advice**: Provide specific, implementable recommendations
6. **Encouragement**: Acknowledge their progress and encourage continued success
7. **Course History Accuracy**: ALWAYS use the student's actual completed and current courses from their COURSE HISTORY section

RESPONSE STRUCTURE:
- Address them by name when appropriate
- Reference their specific academic context
- Use their ACTUAL completed courses from the COURSE HISTORY section above
- Provide personalized recommendations based on courses they've actually taken
- Connect to their goals when relevant
- Offer next steps or follow-up questions

ACCURACY REQUIREMENTS:
- Only use information from the provided knowledge base
- For completed courses, ONLY use courses listed in the COURSE HISTORY section above
- Reference specific courses by exact code and title from their actual records
- If course information is unavailable in their records, acknowledge limitations professionally  
- NEVER fabricate course numbers, titles, grades, or completion status
- NEVER make up courses the student hasn't actually taken
"""
        
        return prompt
    
    def _select_advisor_personality(self, context: Dict) -> str:
        """Select appropriate advisor personality based on student profile"""
        if context.get("status") in ["new_student", "error"]:
            return "supportive"
        
        completion = context.get("completion_status", {}).get("profile_completion", 0)
        if completion < 50:
            return "supportive"  # More guidance needed
        elif context.get("academic_profile", {}).get("academic_level") == "graduate":
            return "analytical"  # More detailed planning
        else:
            return "motivational"  # Encourage exploration
    
    def _build_personal_context(self, context: Dict) -> str:
        """Build personalized context string"""
        if context.get("status") != "error":
            personal = context.get("personal_info", {})
            name = personal.get("preferred_name", "Student")
            return f"Student: {name} ({personal.get('email', 'Unknown')})"
        return "New student (limited profile information available)"
    
    def _build_academic_context(self, context: Dict) -> str:
        """Build academic context string"""
        if context.get("status") == "error":
            return "Academic profile: Not available (new or incomplete profile)"
        
        academic = context.get("academic_profile", {})
        completion = context.get("completion_status", {})
        
        details = []
        if academic.get("student_type"):
            details.append(f"Type: {academic['student_type']}")
        if academic.get("academic_level"):
            details.append(f"Level: {academic['academic_level']}")
        if academic.get("degree_program"):
            details.append(f"Degree: {academic['degree_program']}")
        elif academic.get("primary_major"):
            details.append(f"Major: {academic['primary_major']}")
        if academic.get("enrollment_status"):
            details.append(f"Status: {academic['enrollment_status']}")
        if academic.get("cumulative_gpa"):
            details.append(f"GPA: {academic['cumulative_gpa']}")
        if academic.get("expected_graduation"):
            details.append(f"Expected graduation: {academic['expected_graduation']}")
        
        profile_complete = completion.get("profile_completion", 0)
        details.append(f"Profile completion: {profile_complete}%")
        
        return " | ".join(details) if details else "Academic profile: Incomplete"
    
    def _build_goal_context(self, context: Dict) -> str:
        """Build goals and interests context"""
        if context.get("status") == "error":
            return "Goals: Not available"
        
        goals = context.get("academic_goals", [])
        interests = context.get("course_interests", [])
        
        goal_summary = []
        if goals:
            high_priority_goals = [g for g in goals if g.get("priority", 5) >= 7]
            if high_priority_goals:
                goal_summary.append(f"High priority goals: {len(high_priority_goals)}")
        
        if interests:
            very_interested = [i for i in interests if i.get("interest_level") == "very_interested"]
            if very_interested:
                goal_summary.append(f"High interest courses: {len(very_interested)}")
        
        return " | ".join(goal_summary) if goal_summary else "Goals: Not yet defined"
    
    def _build_course_history_context(self, context: Dict) -> str:
        """Build course history context string"""
        if context.get("status") == "error":
            return "Course History: Not available"
        
        completed_courses = context.get("completed_courses", [])
        current_courses = context.get("current_courses", [])
        
        history_summary = []
        
        if completed_courses:
            completed_details = []
            for course in completed_courses[:10]:  # Limit to recent 10 courses
                code = course.get("course_code", "")
                title = course.get("course_title", "")
                grade = course.get("grade", "")
                semester = course.get("semester", "")
                year = course.get("year", "")
                
                if code:
                    course_str = f"{code}"
                    if title:
                        course_str += f" ({title})"
                    if grade:
                        course_str += f" - Grade: {grade}"
                    if semester and year:
                        course_str += f" [{semester} {year}]"
                    completed_details.append(course_str)
            
            if completed_details:
                history_summary.append(f"Completed: {'; '.join(completed_details)}")
        
        if current_courses:
            current_details = []
            for course in current_courses:
                code = course.get("course_code", "")
                title = course.get("course_title", "")
                semester = course.get("semester", "")
                year = course.get("year", "")
                
                if code:
                    course_str = f"{code}"
                    if title:
                        course_str += f" ({title})"
                    if semester and year:
                        course_str += f" [{semester} {year}]"
                    current_details.append(course_str)
            
            if current_details:
                history_summary.append(f"Currently Enrolled: {'; '.join(current_details)}")
        
        if not history_summary:
            return "Course History: No course history available"
        
        return " | ".join(history_summary)
    
    def _analyze_query_intent(self, query: str) -> str:
        """Analyze the intent of the current query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["course", "class", "prerequisite", "schedule"]):
            return "Course Planning"
        elif any(word in query_lower for word in ["major", "degree", "requirement", "graduation"]):
            return "Degree Planning"
        elif any(word in query_lower for word in ["career", "job", "internship", "future"]):
            return "Career Guidance"
        elif any(word in query_lower for word in ["gpa", "grade", "study", "academic"]):
            return "Academic Performance"
        else:
            return "General Inquiry"
    
    def generate_suggested_questions(self, context: Dict, query_intent: str) -> List[str]:
        """Generate personalized follow-up questions"""
        if context.get("status") == "error":
            return [
                "Would you like to complete your academic profile for personalized advice?",
                "What courses are you currently taking?",
                "What are your main academic goals this semester?"
            ]
        
        academic = context.get("academic_profile", {})
        major = academic.get("primary_major", "")
        level = academic.get("academic_level", "")
        
        suggestions = []
        
        if query_intent == "Course Planning":
            suggestions.extend([
                f"What {major} courses should I take next semester?",
                f"Are there any {level}-level electives you'd recommend?",
                "How should I balance my course load?"
            ])
        elif query_intent == "Degree Planning":
            suggestions.extend([
                f"What requirements do I still need for my {major} degree?",
                "How can I optimize my remaining semesters?",
                "Should I consider adding a minor or second major?"
            ])
        elif query_intent == "Career Guidance":
            suggestions.extend([
                f"What career paths are common for {major} graduates?",
                "How can I prepare for internships in my field?",
                "What skills should I develop for my career goals?"
            ])
        
        return suggestions[:3]  # Return top 3 suggestions


class FastResponseCache:
    """
    High-performance response caching for frequently asked questions
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.hit_count = {}
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
    
    def get_cache_key(self, user_email: str, query: str, context_hash: str) -> str:
        """Generate cache key for query"""
        return f"{user_email}:{hash(query.lower().strip())}:{context_hash}"
    
    def get(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if valid"""
        if cache_key in self.cache:
            if datetime.now() < self.cache_expiry[cache_key]:
                self.hit_count[cache_key] = self.hit_count.get(cache_key, 0) + 1
                return self.cache[cache_key]
            else:
                # Expired cache entry
                del self.cache[cache_key]
                del self.cache_expiry[cache_key]
        return None
    
    def set(self, cache_key: str, response: Dict) -> None:
        """Cache response"""
        self.cache[cache_key] = response
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
        self.hit_count[cache_key] = 0
    
    def get_stats(self) -> Dict:
        """Get cache performance stats"""
        total_hits = sum(self.hit_count.values())
        return {
            "total_cached_responses": len(self.cache),
            "total_cache_hits": total_hits,
            "most_popular": max(self.hit_count.items(), key=lambda x: x[1]) if self.hit_count else None
        }


# Global instances for performance
advisor_engine = None
response_cache = FastResponseCache()

def get_advisor_engine(onboarding_api: OnboardingAPI) -> PersonalizedAdvisorEngine:
    """Get singleton advisor engine instance"""
    global advisor_engine
    if advisor_engine is None:
        advisor_engine = PersonalizedAdvisorEngine(onboarding_api)
    return advisor_engine
