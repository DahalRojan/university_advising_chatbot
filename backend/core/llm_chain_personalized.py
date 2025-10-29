"""
Enhanced LLM Chain with Personalized Academic Advisor Integration
Fast, context-aware responses with student personalization
"""

import json
import time
import re
import random
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from features.intelligence.personalized_advisor import get_advisor_engine, response_cache
from features.onboarding.onboarding_api import OnboardingAPI
import requests

# Load environment variables
from dotenv import load_dotenv
config_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(config_path)

if TYPE_CHECKING:
    from features.intelligence.personalized_advisor import PersonalizedAdvisorEngine

# LLM Configuration with Local/Groq Fallback
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local").lower()

if LLM_PROVIDER == "local":
    MODEL_NAME = os.getenv("LOCAL_LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4")
    API_KEY = os.getenv("LOCAL_LLM_API_KEY")
    API_BASE_URL = os.getenv("LOCAL_LLM_API_URL", "https://llm.rojandahal.com/v1/chat/completions")
    print(f"LLM PROVIDER: LOCAL - {API_BASE_URL}")
else:
    MODEL_NAME = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    API_KEY = os.getenv("GROQ_API_KEY")
    API_BASE_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    print(f"LLM PROVIDER: GROQ - {API_BASE_URL}")

print(f"MODEL: {MODEL_NAME}")
print("=" * 80)

def ask_llm_personalized(user_input: str, context: str, history: List[Dict],
                        user_email: str, user_data: Dict,
                        onboarding_api: OnboardingAPI, query_mode: str = "catalog_info") -> Dict[str, Any]:
    """
    Enhanced LLM with full personalization and fast response optimization
    """
    start_time = time.time()

    # =============================================================================
    # [CHART] COMPREHENSIVE DATA FLOW LOGGING START
    # =============================================================================
    print("\n" + "=" * 80)
    print("[FIRE] PERSONALIZED LLM PIPELINE - FULL DATA FLOW")
    print("=" * 80)
    print(f"[INBOX] INPUT RECEIVED:")
    print(f"   User Email: {user_email}")
    print(f"   User Input: '{user_input}'")
    print(f"   Input Length: {len(user_input)} characters")
    print(f"   History Length: {len(history)} messages")
    print(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    # 1. ULTRA-FAST GREETING DETECTION
    is_greeting = _is_greeting(user_input)
    print(f"[TARGET] GREETING DETECTION: {'YES' if is_greeting else 'NO'}")
    if is_greeting:
        print("[LIGHTNING] FAST PATH: Handling personalized greeting")
        return _handle_personalized_greeting(user_email, user_data, history, onboarding_api)
    
    # 2. CACHE CHECK FOR FREQUENT QUERIES
    print("[BRAIN] STUDENT CONTEXT EXTRACTION:")
    advisor_engine = get_advisor_engine(onboarding_api)
    student_context = advisor_engine.get_student_context(user_email, user_data)

    print(f"   Status: {student_context.get('status', 'unknown')}")
    if student_context.get('status') != 'error':
        academic_profile = student_context.get('academic_profile', {})
        print(f"   Academic Level: {academic_profile.get('academic_level', 'N/A')}")
        print(f"   Major: {academic_profile.get('degree_program', 'N/A')}")
        print(f"   Enrolled Year: {academic_profile.get('enrolled_year', 'N/A')}")
        print(f"   Expected Graduation: {academic_profile.get('expected_graduation', 'N/A')}")

    # Create safe hash for caching (exclude non-hashable parts)
    cache_context = {k: v for k, v in student_context.items() if isinstance(v, (str, int, float, bool, type(None)))}
    context_hash = str(hash(str(cache_context)))

    cache_key = response_cache.get_cache_key(user_email, user_input, context_hash)
    print(f"[KEY2] CACHE KEY GENERATED: {cache_key[:50]}...")

    cached_response = response_cache.get(cache_key)
    if cached_response:
        print(f"[LIGHTNING] CACHE HIT! Returning cached response - Time: {time.time() - start_time:.3f}s")
        print("=" * 80)
        return cached_response

    print("[FLOPPY2] CACHE MISS - Proceeding with full pipeline")
    print("-" * 80)
    
    # 3. QUICK PATTERN RESPONSES (Common academic questions)
    quick_response = _check_quick_patterns(user_input, student_context, advisor_engine)
    if quick_response:
        response_cache.set(cache_key, quick_response)
        print(f"[LIGHTNING] Quick pattern - Response time: {time.time() - start_time:.3f}s")
        return quick_response
    
    # 4. FULL PERSONALIZED LLM RESPONSE
    try:
        # =============================================================================
        # [SEARCH] QUERY ENHANCEMENT & RETRIEVAL PIPELINE
        # =============================================================================
        print("[SEARCH] QUERY ENHANCEMENT:")
        enhanced_query = _enhance_query_with_student_context(user_input, student_context)
        print(f"   Original Query: '{user_input}'")
        print(f"   Enhanced Query: '{enhanced_query}'")
        print(f"   Enhancement Gain: {len(enhanced_query) - len(user_input)} characters")

        # Determine retrieval strategy
        is_course_related = _is_course_related_query(user_input)
        print(f"   Course-Related Query: {'YES' if is_course_related else 'NO'}")
        print("-" * 80)

        # Re-retrieve with enhanced query if it's course-related
        if is_course_related:
            print("[TARGET] RAG RETRIEVAL PIPELINE:")

            # Check if this is a course-related query that needs course-aware retrieval
            course_related_keywords = [
                # Scheduling queries
                'when can i take', 'what time', 'schedule', 'meeting time', 'offered when',
                'available', 'availability', 'current term', 'this term', 'can i register',
                'open sections', 'enrollment', 'when is', 'when does', 'what semester',
                'offered', 'when offered', 'can i take now', 'now', 'current', 'this semester',
                # Prerequisite queries
                'prerequisite', 'prereq', 'pre req', 'what is the pre req', 'requirements',
                'needed before', 'what do i need', 'required courses', 'pre-req', 'depends on'
            ]
            is_course_query = any(keyword in user_input.lower() for keyword in course_related_keywords)

            # If explicit query_mode is provided, always use course-aware retrieval for course-related queries
            if query_mode in ["current_sections", "catalog_info"]:
                is_course_query = True
                print(f"[MODE] EXPLICIT QUERY MODE: {query_mode} - Forcing course-aware retrieval")

            if is_course_query:
                print(f"[CALENDAR] COURSE QUERY DETECTED - Using course-aware retrieval")
                print(f"   Keywords detected: {[k for k in course_related_keywords if k in user_input.lower()]}")
                from core.course_aware_retriever import course_aware_retrieve_with_details
                print("   [BRAIN] USING COURSE-AWARE RETRIEVAL (Live Sections + Catalog)...")
                print(f"      Enhanced Query: '{enhanced_query[:80]}{'...' if len(enhanced_query) > 80 else ''}'")
                print(f"      Student Email: {user_email}")
                print("   [SEARCH] SEARCHING COURSE DATABASE + KNOWLEDGE BASE...")

                # Use original query for classification to avoid interference from enhanced keywords
                from core.course_aware_retriever import CourseAwareRetriever
                retriever = CourseAwareRetriever()
                query_analysis = retriever.is_course_query(user_input)
                print(f"   [CLASSIFY] Original query classification: {query_analysis.get('query_type')}")

                # Use enhanced query for retrieval but pass correct classification and query_mode
                course_result = course_aware_retrieve_with_details(enhanced_query, student_email=user_email, top_k=8, query_analysis=query_analysis, query_mode=query_mode)
                context = course_result.get("documents_text", "")
                print(f"   [PAGE] COURSE-AWARE RETRIEVAL: {len(context)} characters")
                print(f"   [INFO] Course Data Used: {course_result.get('course_data_used', False)}")
                print(f"   [INFO] Query Type: {course_result.get('query_analysis', {}).get('query_type', 'unknown')}")
                print(f"   [INFO] Data Sources: {course_result.get('sources', [])}")
                print(f"   [INFO] Confidence: {course_result.get('confidence', 0.0):.2f}")
            else:
                # Try year-aware retrieval first for non-scheduling course queries
                enrolled_year = student_context.get('academic_profile', {}).get('enrolled_year')
                academic_level = student_context.get('academic_profile', {}).get('academic_level', 'undergraduate')

                if enrolled_year:
                    print(f"[BOOKS] YEAR-AWARE RETRIEVAL:")
                    print(f"   Target Year: {enrolled_year}")
                    print(f"   Academic Level: {academic_level}")
                    print(f"   Catalog Year: {enrolled_year}-{enrolled_year + 1}")

                    try:
                        from core.retriever_year_aware import year_aware_retrieve_with_confidence, YearAwareRetriever

                        print("   [BRAIN] GENERATING QUERY EMBEDDING...")
                        print(f"      Embedding Model: BAAI/bge-large-en-v1.5")
                        print(f"      Query: '{enhanced_query[:80]}{'...' if len(enhanced_query) > 80 else ''}'")
                        print(f"      Database: Qdrant")
                        print(f"      Collection: university_docs_year_aware_v1")
                        print(f"      Vector Search Strategy: Cosine similarity")
                        print(f"   [SEARCH] SEARCHING YEAR-AWARE COLLECTION...")

                        year_aware_result = year_aware_retrieve_with_confidence(
                            enhanced_query,
                            enrolled_year=enrolled_year,
                            academic_level=academic_level,
                            top_k=8
                        )

                        if year_aware_result.get("documents"):
                            context = year_aware_result["documents_text"]
                            confidence = year_aware_result['confidence']
                            metadata = year_aware_result.get('metadata', {})

                            print(f"   [SUCCESS] YEAR-AWARE SUCCESS!")
                            print(f"      Overall Confidence: {confidence['overall_confidence']:.2f}")
                            print(f"      Year Relevance: {confidence['year_relevance']:.2f}")
                            print(f"      Level Match: {confidence['level_match']:.2f}")
                            print(f"      Documents Found: {len(year_aware_result['documents'])}")
                            print(f"      Year-Aware Results: {metadata.get('year_aware_results', 0)}")
                            print(f"      Fallback Results: {metadata.get('fallback_results', 0)}")
                            print(f"      Context Length: {len(context)} characters")
                        else:
                            print("   [WARNING] YEAR-AWARE RETURNED NO RESULTS - FALLBACK TO STANDARD")
                            from core.course_aware_retriever import course_aware_retrieve_with_details
                            print("   [BRAIN] USING COURSE-AWARE RETRIEVAL (Fallback)...")
                            print(f"      Enhanced Query: '{enhanced_query[:80]}{'...' if len(enhanced_query) > 80 else ''}'")
                            print(f"      Student Email: {user_email}")
                            print("   [SEARCH] SEARCHING COURSE DATABASE + KNOWLEDGE BASE...")
                            course_result = course_aware_retrieve_with_details(enhanced_query, student_email=user_email, top_k=8)
                            context = course_result.get("documents_text", "")
                            print(f"   [PAGE] COURSE-AWARE RETRIEVAL: {len(context)} characters")
                            print(f"   [INFO] Course Data Used: {course_result.get('course_data_used', False)}")
                            print(f"   [INFO] Confidence: {course_result.get('confidence', 0.0):.2f}")

                    except Exception as e:
                        print(f"   [ERROR] YEAR-AWARE FAILED: {e}")
                        print("   [REFRESH] FALLBACK TO STANDARD RETRIEVAL")
                        from core.course_aware_retriever import course_aware_retrieve_with_details
                        print("   [BRAIN] USING COURSE-AWARE RETRIEVAL (Error Fallback)...")
                        print(f"      Enhanced Query: '{enhanced_query[:80]}{'...' if len(enhanced_query) > 80 else ''}'")
                        print(f"      Student Email: {user_email}")
                        print("   [SEARCH] SEARCHING COURSE DATABASE + KNOWLEDGE BASE...")
                        course_result = course_aware_retrieve_with_details(enhanced_query, student_email=user_email, top_k=8)
                        context = course_result.get("documents_text", "")
                        print(f"   [PAGE] COURSE-AWARE RETRIEVAL: {len(context)} characters")
                        print(f"   [INFO] Course Data Used: {course_result.get('course_data_used', False)}")
                        print(f"   [INFO] Confidence: {course_result.get('confidence', 0.0):.2f}")
                else:
                    print("[BOOKS] UNIFIED RETRIEVAL (No enrollment year):")
                    try:
                        from core.unified_retriever import unified_retrieve
                        print("   [BRAIN] USING UNIFIED RETRIEVAL SYSTEM...")

                        retrieval_result = unified_retrieve(
                            enhanced_query,
                            enrolled_year=None,
                            academic_level='undergraduate',
                            top_k=8
                        )

                        if retrieval_result.get("documents_text"):
                            context = retrieval_result["documents_text"]
                            confidence = retrieval_result.get('confidence', {})
                            print(f"   [SUCCESS] UNIFIED RETRIEVAL SUCCESS!")
                            print(f"      Overall Confidence: {confidence.get('overall_confidence', 0.0):.2f}")
                            print(f"      Strategy: {confidence.get('strategy', 'unknown')}")
                            print(f"      Documents Found: {len(retrieval_result.get('documents', []))}")
                            print(f"   [PAGE] CONTEXT RETRIEVED: {len(context)} characters")
                        else:
                            print("   [WARNING] UNIFIED RETRIEVAL RETURNED NO RESULTS - FALLBACK")
                            from core.course_aware_retriever import course_aware_retrieve_with_details
                            print("   [BRAIN] USING COURSE-AWARE RETRIEVAL (Unified Fallback)...")
                            course_result = course_aware_retrieve_with_details(enhanced_query, student_email=user_email, top_k=8)
                            context = course_result.get("documents_text", "")
                            print(f"   [PAGE] COURSE-AWARE FALLBACK: {len(context)} characters")
                            print(f"   [INFO] Course Data Used: {course_result.get('course_data_used', False)}")
                    except Exception as e:
                        print(f"   [ERROR] UNIFIED RETRIEVAL FAILED: {e}")
                        from core.course_aware_retriever import course_aware_retrieve_with_details
                        print("   [BRAIN] USING COURSE-AWARE RETRIEVAL (Final Fallback)...")
                        course_result = course_aware_retrieve_with_details(enhanced_query, student_email=user_email, top_k=8)
                        context = course_result.get("documents_text", "")
                        print(f"   [PAGE] COURSE-AWARE FINAL FALLBACK: {len(context)} characters")
                        print(f"   [INFO] Course Data Used: {course_result.get('course_data_used', False)}")
        else:
            print("[MEMO] NON-COURSE QUERY - Using provided context")
            # For non-course queries, use the provided context or empty string
            context = context if context.strip() else ""
            print(f"   [PAGE] CONTEXT LENGTH: {len(context)} characters")

        print("-" * 80)

        # =============================================================================
        # [TOOLS2] PROMPT BUILDING PIPELINE
        # =============================================================================
        print("[TOOLS2] PROMPT CONSTRUCTION:")

        # Build personalized prompt with student context
        personalized_prompt = advisor_engine.build_personalized_prompt(
            user_email, user_input, context, history, user_data
        )
        print(f"   [MEMO] Personalized Prompt: {len(personalized_prompt)} characters")

        # Analyze query intent for better suggestions
        query_intent = advisor_engine._analyze_query_intent(user_input)
        print(f"   [TARGET] Query Intent: {query_intent}")

        # Get year context for enhanced prompting
        enrolled_year = student_context.get('academic_profile', {}).get('enrolled_year')
        academic_level = student_context.get('academic_profile', {}).get('academic_level', 'undergraduate')
        applicable_catalog = f"{enrolled_year}-{enrolled_year + 1}" if enrolled_year else "current"
        print(f"   [CALENDAR] Applicable Catalog: {applicable_catalog}")

        # Enhanced system prompt with year-aware context
        year_context_note = ""
        if enrolled_year:
            year_context_note = f"""
IMPORTANT YEAR-SPECIFIC CONTEXT:
- This student enrolled in {enrolled_year}, so they follow the {applicable_catalog} catalog requirements
- All degree requirements, course descriptions, and policies should be based on their enrollment year catalog
- If providing course recommendations, ensure they align with the {applicable_catalog} catalog year
- When discussing graduation requirements, reference their specific catalog year policies
- If information has changed since their enrollment, clarify what applies to them specifically
"""
            print(f"   [BOARD] Year-Specific Instructions: ENABLED")
        else:
            print(f"   [BOARD] Year-Specific Instructions: DISABLED")

        system_prompt = f"""{personalized_prompt}

Please provide a comprehensive response to the student's question using the knowledge base provided.
{year_context_note}
RESPONSE GUIDELINES:
- Be warm and personalized, addressing the student by name when appropriate
- Reference their specific academic context (major, level, enrollment year)
- Provide actionable, specific advice with concrete course recommendations
- Use only information from the provided knowledge base

SPECIAL HANDLING FOR COURSE SCHEDULING QUERIES:
When students ask "when can I take this?" or similar scheduling questions:
1. PRIORITIZE live course section data (enrollment, meeting times, faculty)
2. Give SPECIFIC scheduling information: "Section 0A meets M,W 2:25-4:25 PM with Ms Q Zhang"
3. Include IMMEDIATE availability: "1 spot open" or "currently full"
4. Provide ACTIONABLE next steps: specific sections to register for
5. Avoid generic advice like "typically offered in Fall" when live data exists

COURSE INFORMATION PRIORITIES:
- SCHEDULING questions → Live sections first, then catalog context
- AVAILABILITY questions → Current enrollment status and open sections
- GENERAL questions → Combine live sections with course descriptions
- PREREQUISITE questions → Academic catalog requirements

- When recommending courses, include course codes, titles, and brief descriptions
- Explain how recommended courses align with their major and career goals
- For current students: Base requirements on their {applicable_catalog} enrollment catalog
- For prospective students: Use current catalog information for planning
- If specific course information is not available, acknowledge limitations professionally
- Keep responses thorough but organized (3-5 paragraphs maximum)

Current query intent: {query_intent}
IMPORTANT: If this is a course recommendation query, provide specific course suggestions with codes and titles from the knowledge base, ensuring they match the student's catalog year context."""
        
        # Build conversation history
        messages = [{"role": "system", "content": system_prompt}]

        # Add relevant conversation history (last 6 messages for context)
        relevant_history = history[-6:] if len(history) > 6 else history
        for msg in relevant_history:
            role = "user" if msg["sender"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["text"]})

        # Add current query WITH SMART CONTEXT MANAGEMENT
        # Intelligently truncate context while preserving course information
        smart_context = _smart_truncate_context(context, user_input, max_length=4500)
        
        user_message_with_context = f"""AVAILABLE COURSES FROM DATABASE:
{smart_context}

STUDENT QUESTION: {user_input}

CRITICAL: Use ONLY the course information above. If you don't see relevant courses in the provided data, say so. Never invent course codes or descriptions. Respond conversationally as an AI advisor."""
        
        messages.append({"role": "user", "content": user_message_with_context})

        print(f"   [SPEECH] Message History: {len(relevant_history)} previous messages")
        print(f"   [MEMO] System Prompt: {len(system_prompt)} characters")
        print(f"   [CHART] Total Messages: {len(messages)}")

        # Calculate total token estimate
        total_content = system_prompt + user_input + "".join([msg.get("content", "") for msg in messages])
        estimated_tokens = len(total_content) // 4  # Rough estimate
        print(f"   [NUMBERS] Estimated Tokens: ~{estimated_tokens}")
        print("-" * 80)

        # =============================================================================
        # [ROBOT] LLM API CALL
        # =============================================================================
        print("[ROBOT] LOCAL LLM API CALL:")
        print(f"   [GLOBE] Endpoint: {API_BASE_URL}")
        print(f"   [TARGET] Model: {MODEL_NAME}")
        print(f"   [KEY2] API Key: {API_KEY[:20]}...")

        api_start_time = time.time()
        response = _call_llm_api(messages)
        api_duration = time.time() - api_start_time

        print(f"   [TIMER] API Response Time: {api_duration:.3f}s")
        
        if response:
            print(f"   [SUCCESS] RESPONSE RECEIVED: {len(response)} characters")
            print("-" * 80)

            # =============================================================================
            # [BOARD] RESPONSE PROCESSING PIPELINE
            # =============================================================================
            print("[BOARD] RESPONSE PROCESSING:")

            # Since local LLM returns plain text, handle as text response
            llm_output = None
            try:
                llm_output = json.loads(response)
                print("   [PAGE] RESPONSE FORMAT: JSON")
            except json.JSONDecodeError:
                # Treat as plain text response (expected for most LLMs)
                llm_output = {
                    "answer": response,
                    "confidence": 85,  # Default confidence for successful text response
                    "reasoning": "Generated personalized response based on student context",
                    "next_steps": []
                }
                print("   [PAGE] RESPONSE FORMAT: Plain Text")

            print(f"   [MEMO] Answer Length: {len(llm_output.get('answer', ''))} characters")
            print(f"   [TARGET] Confidence: {llm_output.get('confidence', 85)}")

            # Add personalized suggested questions
            print("   [CRYSTAL_BALL] GENERATING SUGGESTED QUESTIONS...")
            suggested_questions = advisor_engine.generate_suggested_questions(
                student_context, query_intent
            )
            print(f"   [LIGHT] Suggested Questions: {len(suggested_questions)}")
            
            # =============================================================================
            # [CHART] FINAL RESPONSE ASSEMBLY
            # =============================================================================
            total_time = round(time.time() - start_time, 3)
            personalization_level = "high" if student_context.get("status") != "error" else "basic"

            final_response = {
                "answer": llm_output.get("answer", response),  # Fallback to raw response
                "confidence": llm_output.get("confidence", 85),
                "reasoning": llm_output.get("reasoning", ""),
                "next_steps": llm_output.get("next_steps", []),
                "suggested_questions": suggested_questions,
                "context_references": llm_output.get("context_references", []),
                "response_time": total_time,
                "personalization_level": personalization_level
            }

            print("[CHART] FINAL RESPONSE ASSEMBLY:")
            print(f"   [MEMO] Final Answer: {len(final_response['answer'])} characters")
            print(f"   [TARGET] Confidence: {final_response['confidence']}")
            print(f"   [LIGHT] Suggested Questions: {len(final_response['suggested_questions'])}")
            print(f"   [PERSON] Personalization Level: {personalization_level}")
            print(f"   [TIMER] Total Response Time: {total_time}s")
            print(f"      - API Call: {api_duration:.3f}s ({(api_duration/total_time)*100:.1f}%)")
            print(f"      - Processing: {(total_time-api_duration):.3f}s ({((total_time-api_duration)/total_time)*100:.1f}%)")

            # Cache successful responses
            if llm_output.get("confidence", 0) > 70:
                response_cache.set(cache_key, final_response)
                print("   [FLOPPY2] RESPONSE CACHED for future use")
            else:
                print("   [NO_ENTRY] RESPONSE NOT CACHED (low confidence)")

            print("=" * 80)
            print("[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            return final_response
        
        else:
            raise Exception("No response from LLM API")
            
    except Exception as e:
        print(f"[ERROR] Error in personalized LLM: {e}")
        return _fallback_response(user_input, student_context, advisor_engine, start_time)


def _is_greeting(user_input: str) -> bool:
    """Fast greeting detection"""
    pattern = r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|how\s+are\s+you|what\'?s\s+up)\s*[.!?]*\s*$'
    return bool(re.match(pattern, user_input.lower().strip()))


def _handle_personalized_greeting(user_email: str, user_data: Dict, history: List[Dict], 
                                 onboarding_api: OnboardingAPI) -> Dict[str, Any]:
    """Generate personalized greeting based on student context"""
    advisor_engine = get_advisor_engine(onboarding_api)
    student_context = advisor_engine.get_student_context(user_email, user_data)
    
    # Get student name
    user_name = user_data.get("name", "").split()[0] if user_data.get("name") else ""
    preferred_name = ""
    
    if student_context.get("status") != "error":
        personal_info = student_context.get("personal_info", {})
        preferred_name = personal_info.get("preferred_name") or personal_info.get("first_name") or user_name
    else:
        preferred_name = user_name
    
    # Check if returning user
    is_returning = len(history) > 0
    
    # Build personalized greeting
    if is_returning:
        greetings = [
            f"Hi again, {preferred_name}! How can I help you continue your academic planning?",
            f"Welcome back, {preferred_name}! What academic questions can I assist with today?",
            f"Hello {preferred_name}! Ready to tackle more academic planning together?"
        ]
    else:
        if student_context.get("status") != "error":
            academic = student_context.get("academic_profile", {})
            major = academic.get("primary_major", "")
            level = academic.get("academic_level", "")
            
            greetings = [
                f"Hello {preferred_name}! I'm excited to help with your {major} {level} program planning. What's on your mind today?",
                f"Hi {preferred_name}! As your academic advisor, I'm here to support your {major} journey. How can I help?",
                f"Welcome {preferred_name}! I see you're working on your {major} degree - I'm here to help with any academic questions you have."
            ]
        else:
            greetings = [
                f"Hello {preferred_name}! I'm your academic advisor assistant. I'd love to help you with course planning, requirements, or any academic questions.",
                f"Hi {preferred_name}! I'm here to support your academic success at Gannon University. What can I help you with today?",
                f"Welcome {preferred_name}! I'm excited to help you navigate your academic journey. What questions do you have?"
            ]
    
    greeting = random.choice(greetings)
    
    # Generate contextual suggested questions
    suggested_questions = advisor_engine.generate_suggested_questions(student_context, "General Inquiry")
    
    return {
        "answer": greeting,
        "confidence": 100,
        "suggested_questions": suggested_questions,
        "response_time": 0.05,  # Ultra-fast greeting
        "personalization_level": "high" if preferred_name else "basic"
    }


def _check_quick_patterns(user_input: str, student_context: Dict, 
                         advisor_engine: "PersonalizedAdvisorEngine") -> Optional[Dict]:
    """Check for common patterns that can be answered quickly"""
    query_lower = user_input.lower().strip()
    
    # Get student info for personalization
    preferred_name = ""
    major = ""
    level = ""
    
    if student_context.get("status") != "error":
        personal_info = student_context.get("personal_info", {})
        academic_info = student_context.get("academic_profile", {})
        preferred_name = personal_info.get("preferred_name", "")
        major = academic_info.get("primary_major", "")
        level = academic_info.get("academic_level", "")
    
    name_part = f"{preferred_name}, " if preferred_name else ""
    
    # Academic status questions
    if "how am i doing" in query_lower or "my progress" in query_lower:
        if student_context.get("status") != "error":
            completion = student_context.get("completion_status", {})
            profile_completion = completion.get("profile_completion", 0)
            academic = student_context.get("academic_profile", {})
            
            response = f"You're making great progress{', ' + preferred_name if preferred_name else ''}! Your academic profile is {profile_completion}% complete. "
            
            if academic.get("cumulative_gpa"):
                response += f"Your current GPA is {academic['cumulative_gpa']}. "
            
            if completion.get("onboarding_complete"):
                response += "You've completed your onboarding, which puts you ahead of the game for academic planning!"
            else:
                response += "Once you complete your full profile, I'll be able to give you even more personalized advice."
            
            return {
                "answer": response,
                "confidence": 95,
                "suggested_questions": [
                    "What courses should I take next semester?",
                    "How can I improve my academic performance?",
                    "What graduation requirements do I still need?"
                ],
                "response_time": 0.1,
                "personalization_level": "high"
            }
    
    # Course planning questions - let full LLM handle with enhanced retrieval
    # Removed quick pattern to allow proper course retrieval and recommendations
    
    # Graduation requirements
    if any(phrase in query_lower for phrase in ["graduation requirements", "degree requirements", "what do i need to graduate"]):
        if major and level:
            response = f"Excellent question{', ' + preferred_name if preferred_name else ''}! For your {major} {level} degree, I'll need to check the specific requirements in our academic catalog. Let me pull up the current degree requirements for your program."
        else:
            response = f"I'd be happy to help with graduation requirements{', ' + preferred_name if preferred_name else ''}! Let me search for the degree requirements that apply to your program."
        
        return {
            "answer": response,
            "confidence": 90,
            "suggested_questions": [
                "How many credits do I need total?",
                "What are my remaining requirements?",
                "When can I graduate?"
            ],
            "response_time": 0.12,
            "personalization_level": "high" if major else "basic"
        }
    
    # Thank you responses
    if any(phrase in query_lower for phrase in ["thank you", "thanks", "thx", "appreciate"]):
        responses = [
            f"You're very welcome{', ' + preferred_name if preferred_name else ''}! I'm always here when you need academic guidance.",
            f"Happy to help{', ' + preferred_name if preferred_name else ''}! Feel free to come back anytime with more questions.",
            f"My pleasure{', ' + preferred_name if preferred_name else ''}! Supporting your academic success is what I'm here for."
        ]
        
        return {
            "answer": random.choice(responses),
            "confidence": 100,
            "suggested_questions": [
                "What else can I help you plan?",
                "Any other academic questions?",
                "Ready to tackle your next semester?"
            ],
            "response_time": 0.05,
            "personalization_level": "high" if preferred_name else "basic"
        }
    
    return None


def _optimize_messages_for_local_llm(messages: List[Dict]) -> List[Dict]:
    """Optimize messages for server limits - avoid 413 while preserving accurate course data"""
    MAX_TOTAL_LENGTH = 50000  # Updated to match server MAX_REQUEST_SIZE=50000 with safety margin

    # Calculate total content length
    total_length = sum(len(msg.get("content", "")) for msg in messages)

    # ALWAYS truncate for local server - don't just check length
    print(f"[OPTIMIZE] Total message length: {total_length} chars, limit: {MAX_TOTAL_LENGTH}")

    if total_length <= MAX_TOTAL_LENGTH:
        print(f"[OPTIMIZE] Messages fit within limit, but still applying optimization for safety")
        # Still apply truncation for safety with local server
    else:
        print(f"[OPTIMIZE] Messages exceed limit by {total_length - MAX_TOTAL_LENGTH} chars")

    # Keep system message (first) and user message (last), truncate middle
    if len(messages) <= 2:
        # Just system and user - always truncate system message for local model
        system_msg = messages[0]
        user_msg = messages[-1]

        # Always use truncated system message for local model
        truncated_system = _truncate_system_message(system_msg.get("content", ""))
        return [
            {"role": "system", "content": truncated_system},
            user_msg
        ]

    # Multiple messages - always use truncated system message and minimal history
    system_msg = messages[0]
    user_msg = messages[-1]
    history_msgs = messages[1:-1]

    # Always truncate system message for local model
    truncated_system = _truncate_system_message(system_msg.get("content", ""))

    # Calculate remaining space for history
    reserved_length = len(truncated_system) + len(user_msg.get("content", ""))
    available_for_history = MAX_TOTAL_LENGTH - reserved_length

    # Include minimal recent history
    optimized_history = []
    current_length = 0

    # Only include last 1-2 messages if they fit
    for msg in reversed(history_msgs[-2:]):  # Only last 2 history messages
        msg_length = len(msg.get("content", ""))
        if current_length + msg_length <= available_for_history:
            optimized_history.insert(0, msg)
            current_length += msg_length
        else:
            break

    return [{"role": "system", "content": truncated_system}] + optimized_history + [user_msg]

def _truncate_system_message(content: str) -> str:
    """Truncate system message while preserving BOTH student info AND course context"""

    # Split content into sections
    lines = content.split('\n')
    
    # Extract student information
    student_info = ""
    course_context = ""
    instructions = ""
    
    current_section = "unknown"
    for line in lines:
        line_lower = line.lower()
        
        # Identify sections
        if any(keyword in line_lower for keyword in ['student:', 'major:', 'degree:', 'level:', 'status:', 'email:']):
            current_section = "student"
        elif any(keyword in line_lower for keyword in ['course', 'gcis', 'cysec', 'credit', 'prerequisite']):
            current_section = "courses"
        elif any(keyword in line_lower for keyword in ['guideline', 'instruction', 'important:', 'response']):
            current_section = "instructions"
        
        # Collect sections with limits (VERY aggressive for 5000 char API limit)
        if current_section == "student" and len(student_info) < 150:  # Much smaller
            student_info += line + "\n"
        elif current_section == "courses" and len(course_context) < 3000:  # Increased to preserve enhanced formatting
            course_context += line + "\n"
        elif current_section == "instructions" and len(instructions) < 300:  # Much smaller
            instructions += line + "\n"

    # Create conversational advisor system prompt that preserves COURSE INFORMATION
    essential_prompt = f"""You are an AI academic advisor at Gannon University. Respond conversationally.

STUDENT: {student_info.strip()[:100]}

COURSE DATA:
{course_context.strip()}

GUIDELINES:
- Use **bold** for course names and codes
- Include prerequisites, credits, and semester info when available
- Use only provided course information - NEVER make up courses
- For scheduling questions, look for semester info (Fall/Spring/Summer), NOT program sequences
- CRITICAL: If you see "COURSE SCHEDULING FOR" format in the data, preserve it EXACTLY as shown
- CRITICAL: If you see "CURRENT TERM AVAILABILITY" sections, preserve them EXACTLY as formatted
- NEVER reformat structured course scheduling into conversational text
- NEVER add greetings, signatures, or email-style formatting to course scheduling responses
- Be specific and direct when answering course questions"""

    return essential_prompt

def _call_llm_api(messages: List[Dict]) -> Optional[str]:
    """Call Local/Groq LLM API with detailed logging"""
    try:
        print(f"   [SATELLITE] MAKING API CALL TO: {API_BASE_URL}")
        print(f"   [TARGET] MODEL: {MODEL_NAME}")

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        # Adjust parameters based on provider - optimize for local model limits
        if LLM_PROVIDER == "local":
            # ALWAYS truncate messages for local server's 10K limit
            optimized_messages = _optimize_messages_for_local_llm(messages)

            payload = {
                "model": MODEL_NAME,
                "messages": optimized_messages,
                "temperature": 0.3,  # Balanced temperature for formal, informative responses
                "max_tokens": 800,   # Adequate tokens for comprehensive yet organized responses
                "stream": False
            }
        else:
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }

        print(f"   [CHART] PAYLOAD:")
        print(f"      Temperature: {payload['temperature']}")
        print(f"      Max Tokens: {payload['max_tokens']}")
        print(f"      Messages: {len(messages)}")

        # Make the API call
        print(f"   [ROCKET] SENDING REQUEST...")
        response = requests.post(
            API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=45  # Longer timeout for local model
        )

        print(f"   [ENVELOPE] RESPONSE STATUS: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]

            # Log token usage if available
            if "usage" in response_data:
                usage = response_data["usage"]
                print(f"   [CHART_UP] TOKEN USAGE:")
                print(f"      Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"      Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"      Total Tokens: {usage.get('total_tokens', 'N/A')}")

            print(f"   [SUCCESS] SUCCESS: {len(content)} characters generated")
            return content
        else:
            print(f"   [ERROR] API ERROR: {response.status_code}")
            print(f"   [PAGE] Error Details: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print(f"   [ALARM] TIMEOUT: API call exceeded time limit")
        return None
    except requests.exceptions.ConnectionError:
        print(f"   [GLOBE] CONNECTION ERROR: Could not reach {API_BASE_URL}")
        return None
    except Exception as e:
        print(f"   [BOOM] UNEXPECTED ERROR: {e}")
        return None


def _fallback_response(user_input: str, student_context: Dict, 
                      advisor_engine: "PersonalizedAdvisorEngine", 
                      start_time: float) -> Dict[str, Any]:
    """Provide fallback response when LLM fails"""
    preferred_name = ""
    if student_context.get("status") != "error":
        personal_info = student_context.get("personal_info", {})
        preferred_name = personal_info.get("preferred_name", "")
    
    name_part = f"{preferred_name}, " if preferred_name else ""
    
    response = f"I'm sorry {name_part}I'm having trouble processing your request right now. Let me help you in a different way - could you try rephrasing your question or let me know specifically what academic topic you'd like guidance on?"
    
    return {
        "answer": response,
        "confidence": 50,
        "suggested_questions": [
            "What courses are available in my program?",
            "Help me plan my next semester",
            "What are my graduation requirements?"
        ],
        "response_time": round(time.time() - start_time, 3),
        "personalization_level": "basic"
    }


# Backwards compatibility
def ask_llm_enhanced(user_input: str, context: str, history: List[Dict], 
                    user_email: str = "unknown") -> Dict[str, Any]:
    """
    Enhanced LLM call with basic personalization (backwards compatibility)
    """
    # For backwards compatibility, use basic user data
    user_data = {"email": user_email, "name": ""}
    
    # Mock onboarding API if not available
    try:
        from features.onboarding.onboarding_api import OnboardingAPI, get_onboarding_api
        onboarding_api = get_onboarding_api()
    except:
        onboarding_api = None
    
    if onboarding_api:
        return ask_llm_personalized(user_input, context, history, user_email, user_data, onboarding_api)
    else:
        # Fallback to original behavior
        return {
            "answer": "I'm here to help with your academic questions!",
            "confidence": 75,
            "suggested_questions": [
                "What courses should I take?",
                "Help me plan my schedule",
                "What are the requirements for my major?"
            ]
        }


def _enhance_query_with_student_context(query: str, student_context: Dict) -> str:
    """
    Enhance the query with student's academic context for better retrieval
    """
    # Get student's academic information
    academic = student_context.get("academic_profile", {})
    major = academic.get("primary_major", "")
    level = academic.get("academic_level", "")
    
    # If it's a course-related query, enhance with major context
    if _is_course_related_query(query):
        enhanced_query = query
        
        # Add degree program and major context
        degree_program = academic.get("degree_program", "")
        if degree_program:
            enhanced_query += f" {degree_program}"
            
            # Add specific course codes based on degree program
            if "data science" in degree_program.lower():
                enhanced_query += " GCIS Data Science Analytics Machine Learning Statistics Python"
            elif "business analytics" in degree_program.lower():
                enhanced_query += " GMBA Business Analytics Data Analytics Predictive Analytics"
            elif "computer" in degree_program.lower() and "information" in degree_program.lower():
                enhanced_query += " GCIS Computer Information Systems Software Engineering"
            elif "business administration" in degree_program.lower():
                enhanced_query += " GMBA MBA Business Administration Management"
            elif "engineering" in degree_program.lower():
                enhanced_query += " Engineering Mathematics Science"
        
        # Fallback to major if no degree program
        elif major:
            if "data science" in major.lower() or "analytics" in major.lower():
                enhanced_query += f" Data Science Analytics Business Analytics Computer Information Systems GCIS GMBA"
            elif "business" in major.lower():
                enhanced_query += f" Business Administration MBA {major}"
            elif "computer" in major.lower():
                enhanced_query += f" Computer Information Systems GCIS {major}"
            else:
                enhanced_query += f" {major}"
        
        # Add level context
        if level:
            enhanced_query += f" {level}"
            
        # Add course-specific terms
        enhanced_query += " course curriculum requirements prerequisites"
        
        return enhanced_query
    
    return query

def _is_course_related_query(query: str) -> bool:
    """
    Determine if a query is related to courses, including prerequisite queries
    """
    query_lower = query.lower()

    # Course codes (CYSEC, GCIS, CIS, etc.)
    if re.search(r'\b[A-Z]{2,5}\s*\d{3,4}\b', query, re.IGNORECASE):
        return True

    course_keywords = [
        "course", "courses", "class", "classes", "curriculum", "schedule",
        "what should i take", "what courses", "which courses", "course recommendations",
        "major requirements", "degree requirements", "graduation requirements",
        # Prerequisite variations and common misspellings
        "prerequisite", "prerequisites", "prereq", "prereqs", "pre req", "pre-req",
        "pre requisite", "pre-requisite", "pre requisist", "prerequisist",
        "requirements for", "needed for", "before taking", "need to take first"
    ]

    return any(keyword in query_lower for keyword in course_keywords)

def _smart_truncate_context(context: str, user_input: str, max_length: int = 4000) -> str:
    """
    Intelligently truncate context while preserving the most relevant course information.
    For simple scheduling queries, return focused responses to avoid API length limits.
    """
    print(f"[WRENCH] Smart context truncation: input length {len(context)}, max length {max_length}")
    print(f"[SEARCH] Original context preview: {context[:300]}...")

    # Special handling for simple scheduling queries to avoid API length limits
    user_lower = user_input.lower()
    is_simple_scheduling = any(pattern in user_lower for pattern in [
        'when is', 'when can i take', 'what semester', 'offered'
    ]) and any(code in user_input.upper() for code in ['GCIS', 'CYSEC', 'CIS'])

    if is_simple_scheduling and len(context) > max_length:
        print(f"[CALENDAR] Simple scheduling query detected - using focused response")
        # Look for direct course response in context
        if 'GCIS' in context or 'CYSEC' in context:
            # Extract just the course-specific response
            lines = context.split('\n')
            focused_response = []
            in_course_section = False

            for line in lines:
                if any(code in line for code in ['GCIS', 'CYSEC']) and ('**' in line or 'SCHEDULING' in line):
                    in_course_section = True
                    focused_response.append(line)
                elif in_course_section:
                    if line.strip() == '' and len(focused_response) > 5:
                        break  # End of course section
                    focused_response.append(line)
                    if len('\n'.join(focused_response)) > max_length * 0.8:  # 80% of limit
                        break

            if focused_response:
                result = '\n'.join(focused_response)
                print(f"[FOCUS] Focused scheduling response: {len(result)} characters")
                return result

    # Check for cybersecurity-specific content
    cyber_indicators = ['CYSEC', 'cybersecurity', 'Cybersecurity', 'Ethical Hacking', 'Information Assurance']
    cyber_found = [indicator for indicator in context if indicator in cyber_indicators]
    print(f"[LOCKED_KEY] Cybersecurity indicators found: {cyber_found}")

    if len(context) <= max_length:
        print(f"[SUCCESS] Context fits within limit, returning full context")
        return context
    
    # Split context into sections (usually separated by double newlines)
    sections = context.split('\n\n')
    
    # Score sections based on relevance to user query
    user_keywords = user_input.lower().split()
    scored_sections = []
    
    for section in sections:
        score = 0
        section_lower = section.lower()
        
        # Higher score for course codes
        course_codes = re.findall(r'[A-Z]{2,4}\s*\d{3,4}', section)
        score += len(course_codes) * 10

        # CRITICAL: Maximum score for specific course mentioned in query
        query_course_codes = re.findall(r'[A-Z]{2,4}\s*\d{3,4}', user_input.upper())
        for query_code in query_course_codes:
            normalized_query = re.sub(r'\s+', ' ', query_code.strip())
            if normalized_query in section.upper().replace('  ', ' '):
                score += 200  # Highest priority for the specific course being asked about
        
        # VERY HIGH score for CYSEC courses specifically
        if 'CYSEC' in section:
            score += 50
        
        # Score based on keyword matches
        for keyword in user_keywords:
            if keyword in section_lower:
                score += 5
        
        # Higher score for sections with course details
        if any(word in section_lower for word in ['credit', 'prerequisite', 'description']):
            score += 3

        # CRITICAL: CATALOG COURSE DESCRIPTIONS get absolute maximum priority
        is_catalog_description = (
            # Look for actual course descriptions with credits and prerequisites
            (any(pattern in section_lower for pattern in ['credits,', 'credits.', '3 credits']) and
             any(code in section for code in ['GCIS', 'CYSEC', 'CIS'])) or
            # Look for prerequisite information
            ('prerequisite:' in section_lower and any(code in section for code in ['GCIS', 'CYSEC', 'CIS']))
        )

        if is_catalog_description:
            score += 2000  # ABSOLUTE maximum priority for actual catalog descriptions

        # SUPER CRITICAL: For prerequisite queries, prioritize sections with BOTH course code AND prerequisite info
        is_prerequisite_query = any(prereq_word in user_input.lower() for prereq_word in ['prereq', 'prerequisite', 'pre req'])
        if is_prerequisite_query:
            has_query_course = any(normalized_query in section.upper().replace('  ', ' ') for normalized_query in [re.sub(r'\s+', ' ', code.strip()) for code in query_course_codes])
            has_prerequisite_info = 'prerequisite:' in section_lower

            if has_query_course and has_prerequisite_info:
                score += 3000  # MAXIMUM priority for prerequisite information for the specific course

        # CRITICAL: Prerequisite information gets very high priority
        if any(word in user_input.lower() for word in ['prerequisite', 'prereq', 'pre req', 'requirement']):
            if 'prerequisite:' in section_lower or 'prereq:' in section_lower:
                score += 1500  # Very high priority for prerequisite info

        # CRITICAL: Course scheduling format
        if 'course scheduling for' in section_lower and any(word in user_input.lower() for word in ['when', 'offered', 'schedule']):
            score += 1000  # High priority for enhanced format

        # Live course sections with meeting data
        if any(indicator in section_lower for indicator in ['current term availability', 'available now - you can register', 'meeting:']):
            if any(word in user_input.lower() for word in ['when', 'offered', 'schedule']):
                score += 800  # High priority for live data

        # CRITICAL: HEAVILY penalize program sequences and curriculum outlines
        is_program_sequence = any(sequence in section_lower for sequence in [
            'fall start', 'spring start', 'semester 1', 'semester 2', 'semester 3', 'semester 4',
            'project proposal', 'directed research', 'thesis', 'course of study for'
        ])

        if is_program_sequence:
            score -= 1000  # Heavy penalty to ensure program sequences get removed

        # Extra penalty for curriculum planning sections
        if ('semester' in section_lower and
            any(word in section_lower for word in ['fall', 'spring']) and
            any(word in section_lower for word in ['directed', 'proposal', 'research'])):
            score -= 1500  # Maximum penalty for curriculum sequences

        # Extra score for cybersecurity-related terms
        if any(term in section_lower for term in ['ethical hacking', 'information assurance', 'cybersecurity', 'data security']):
            score += 15
        
        scored_sections.append((score, section))
    
    # Sort by score (highest first)
    scored_sections.sort(key=lambda x: x[0], reverse=True)
    
    # Build result with highest scoring sections first
    result = ""
    for score, section in scored_sections:
        if len(result) + len(section) + 2 <= max_length:  # +2 for \n\n
            if result:
                result += "\n\n"
            result += section
        else:
            # Try to fit a truncated version
            remaining_space = max_length - len(result) - 2
            if remaining_space > 100:  # Only if meaningful space left
                if result:
                    result += "\n\n"
                result += section[:remaining_space] + "..."
            break
    
    print(f"[WRENCH] Context truncated from {len(context)} to {len(result)} chars, preserving top-scored content")
    print(f"[TARGET] Final context preview: {result[:200]}...")
    
    # Count course codes in final result to verify we have actual course data
    course_codes = re.findall(r'[A-Z]{2,4}[-\s]*\d{3,4}', result)
    print(f"[BOOKS] Course codes found in final context: {len(course_codes)} - {course_codes[:5] if course_codes else 'None'}")
    
    return result


# Original function for backwards compatibility
def ask_llm(user_input: str, context: str, history: List[Dict]) -> Dict[str, Any]:
    """Original ask_llm function for backwards compatibility"""
    return ask_llm_enhanced(user_input, context, history, "unknown")
