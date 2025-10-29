#!/usr/bin/env python3
"""
Course-Aware Retriever
Intelligently routes queries to course data or general knowledge base.
Provides comprehensive course information alongside academic guidance.
"""

import re
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from .retriever import advanced_retrieve_with_confidence
from .redis_cache_manager import get_cache_manager
from features.courses.course_information_service import CourseInformationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CourseAwareRetriever:
    """
    Intelligent retriever that combines course data with general knowledge base.
    Routes queries appropriately and provides comprehensive responses.
    """

    def __init__(self):
        self.course_service = CourseInformationService()
        self.logger = logger

        # Patterns to identify course-related queries - more flexible patterns
        self.course_patterns = [
            r'\b([A-Z]{2,5}\s?\d{3,4}[A-Z]?)\b',  # Any course code like "GCIS 220", "CIS 505"
            r'course\s+([A-Z]{2,5}\s?\d{3,4}[A-Z]?)',  # "course CIS 505"
            r'([A-Z]{2,5}\s?\d{3,4}[A-Z]?)\s+course',  # "CIS 505 course"
            r'([A-Z]{2,5}\s?\d{3,4}[A-Z]?)\s+(class|section)',  # "CIS 505 class"
        ]

        # Keywords that suggest course-related queries
        self.course_keywords = [
            'course', 'class', 'section', 'enrollment', 'register', 'schedule',
            'faculty', 'professor', 'instructor', 'meeting', 'time', 'room',
            'availability', 'open', 'closed', 'waitlist', 'capacity', 'spots',
            'department', 'major', 'prerequisite', 'credit', 'semester'
        ]

        # Keywords that suggest availability queries
        self.availability_keywords = [
            'available', 'open', 'spots', 'seats', 'enroll', 'register',
            'can i take', 'is there space', 'waitlist', 'when can i take',
            'what time', 'schedule', 'meeting time', 'offered when',
            'semester', 'fall', 'spring', 'summer'
        ]

        # Keywords that suggest recommendations
        self.recommendation_keywords = [
            'recommend', 'suggest', 'should i take', 'what courses',
            'good courses', 'interesting courses', 'easy courses'
        ]

        # Keywords that suggest prerequisite queries
        self.prerequisite_keywords = [
            'prerequisite', 'prereq', 'requirements', 'needed before',
            'what do i need', 'required courses', 'pre-req', 'depends on',
            'pre req', 'what is the pre req', 'what are the pre req'
        ]

    def detect_course_code(self, query: str) -> Optional[str]:
        """Detect course codes in the query"""
        for pattern in self.course_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                course_code = match.group(1).upper()
                # Normalize course code (add space if missing)
                course_code = re.sub(r'([A-Z]+)(\d+)', r'\1 \2', course_code)
                return course_code
        return None

    def detect_faculty_name(self, query: str) -> Optional[str]:
        """
        Extract faculty name from query.

        Returns:
            Faculty name if detected, None otherwise
        """
        query_lower = query.lower()

        # Common faculty name patterns - ORDER MATTERS!
        faculty_patterns = [
            # Specific patterns for "which/what courses does dr X teaches/teach"
            r'(?:which|what).*?courses.*?does\s+(?:dr\.?\s+|professor\s+)([a-z]+(?:\s+[a-z]+)?)\s+teach',

            # Direct Dr./Professor title patterns (highest priority)
            r'(?:dr\.?\s+|professor\s+|prof\.?\s+)([a-z]+(?:\s+[a-z]+)?)\s+(?:teach|courses|classes)',
            r'(?:dr\.?\s+|professor\s+|prof\.?\s+)([a-z]+(?:\s+[a-z]+)?)(?:\s|$)',

            # "taught by" patterns
            r'taught by\s+(?:dr\.?\s+|professor\s+)?([a-z]+(?:\s+[a-z]+)?)',
            r'courses taught by\s+(?:dr\.?\s+|professor\s+)?([a-z]+(?:\s+[a-z]+)?)',

            # "by" patterns
            r'(?:courses|classes)\s+by\s+(?:dr\.?\s+|professor\s+)?([a-z]+(?:\s+[a-z]+)?)',

            # Name + teaches patterns (lower priority)
            r'([a-z]{3,})\s+(?:teaches|teach|courses|classes)',

            # Fallback patterns
            r'(?:instructor|faculty)\s+(?:dr\.?\s+|professor\s+)?([a-z]+(?:\s+[a-z]+)?)',
        ]

        for pattern in faculty_patterns:
            match = re.search(pattern, query_lower)
            if match:
                faculty_name = match.group(1).strip()

                # Clean up common issues
                faculty_name = re.sub(r'\s+', ' ', faculty_name)  # Multiple spaces
                faculty_name = faculty_name.title()  # Proper case

                # Validate - should be at least 2 characters and contain letters
                if len(faculty_name) >= 2 and re.search(r'[a-zA-Z]', faculty_name):
                    # Add back common prefixes if they were in original
                    if re.search(r'dr\.?\s+', query_lower):
                        return f"Dr {faculty_name}"
                    elif re.search(r'prof', query_lower):
                        return f"Prof {faculty_name}"
                    else:
                        return faculty_name

        return None

    def is_course_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze if query is course-related and determine the type of course query.

        Returns:
            dict with 'is_course_related', 'query_type', 'course_code', 'confidence', 'faculty_name'
        """
        query_lower = query.lower()

        # Check for explicit course codes
        course_code = self.detect_course_code(query)

        # Check for faculty queries
        faculty_name = self.detect_faculty_name(query)

        # Count course-related keywords
        course_keyword_count = sum(1 for keyword in self.course_keywords if keyword in query_lower)

        # Determine query type - prioritize faculty queries
        query_type = 'general'

        # Check for faculty queries first (highest priority)
        if faculty_name:
            query_type = 'faculty'
        # Check for scheduling queries
        elif any(keyword in query_lower for keyword in ['when is', 'when can i take', 'offered', 'schedule', 'meeting time']):
            if course_code:
                query_type = 'specific_course'  # Scheduling query for specific course
            else:
                query_type = 'availability'
        elif any(keyword in query_lower for keyword in self.prerequisite_keywords):
            query_type = 'prerequisite'
        elif any(keyword in query_lower for keyword in self.availability_keywords):
            query_type = 'availability'
        elif any(keyword in query_lower for keyword in self.recommendation_keywords):
            query_type = 'recommendation'
        elif course_code:
            query_type = 'specific_course'
        elif course_keyword_count >= 2:
            query_type = 'course_search'

        # Calculate confidence
        confidence = 0.0
        if course_code:
            confidence += 0.6
        if faculty_name:
            confidence += 0.8  # High confidence for faculty queries
        confidence += min(course_keyword_count * 0.2, 0.4)

        # Special patterns boost confidence
        if re.search(r'(department|major)\s+(course|class)', query_lower):
            confidence += 0.3
        if re.search(r'(when|what time|schedule)', query_lower) and course_keyword_count > 0:
            confidence += 0.2

        # Prerequisite and faculty queries are inherently course-related
        is_prerequisite_query = query_type == 'prerequisite'
        is_faculty_query = query_type == 'faculty'

        is_course_related = confidence >= 0.4 or course_code is not None or is_prerequisite_query or is_faculty_query

        return {
            'is_course_related': is_course_related,
            'query_type': query_type,
            'course_code': course_code,
            'faculty_name': faculty_name,
            'confidence': min(confidence, 1.0),
            'course_keyword_count': course_keyword_count
        }

    def retrieve_course_information(self, query: str, query_analysis: Dict) -> str:
        """Retrieve course-specific information based on query analysis"""
        try:
            course_code = query_analysis.get('course_code')
            query_type = query_analysis.get('query_type')

            if query_type == 'prerequisite' and course_code:
                return self._handle_prerequisite_query(course_code, query)
            elif query_type == 'prerequisite' and not course_code:
                # Handle follow-up prerequisite queries without explicit course codes
                return self._handle_general_prerequisite_query(query)
            elif query_type == 'specific_course' and course_code:
                return self._handle_specific_course_query(course_code, query)
            elif query_type == 'availability':
                return self._handle_availability_query(query)
            elif query_type == 'recommendation':
                return self._handle_recommendation_query(query)
            elif query_type == 'course_search':
                return self._handle_course_search_query(query)
            else:
                return self._handle_general_course_query(query)

        except Exception as e:
            self.logger.error(f"Error retrieving course information: {e}")
            return f"I encountered an error while searching for course information. Please try rephrasing your question."

    def _handle_specific_course_query(self, course_code: str, query: str) -> str:
        """Handle queries about specific courses with combined catalog and live data"""
        courses = self.course_service.get_course_details(course_code)

        if not courses:
            # No live course data - this is expected for many courses that exist in catalogs
            # but aren't offered in current semester. The system will automatically
            # search the academic catalog via the knowledge base.
            return None  # Let the system continue to academic catalog search

        # Determine response type based on query specificity
        query_lower = query.lower()

        # Check if asking for specific current term details (must be very explicit)
        is_current_term_request = any(keyword in query_lower for keyword in [
            'current term', 'this term', 'this semester', 'right now', 'available now',
            'current availability', 'sections available right now', 'can i register now',
            'enrollment count', 'faculty teaching', 'meeting time', 'what time', 'current sections'
        ]) or ('current' in query_lower and 'availability' in query_lower)

        # Check if asking general scheduling question (catalog information first)
        is_general_scheduling = any(keyword in query_lower for keyword in [
            'when is', 'offered', 'when can i take', 'what semester', 'available to take',
            'which semester', 'when available', 'semester offered'
        ])

        if is_current_term_request:
            # Show detailed current term information
            return self._format_current_term_response(course_code, courses)
        elif is_general_scheduling:
            # Show enhanced scheduling information with both catalog and live data
            return self._format_enhanced_scheduling_response(course_code, courses)
        else:
            return self._format_general_course_response(course_code, courses)

    def _format_scheduling_response(self, course_code: str, courses) -> str:
        """Format response specifically for scheduling queries"""
        response_parts = [f"CURRENT SCHEDULING FOR {course_code}:"]
        response_parts.append("")  # Empty line for better formatting

        available_sections = [c for c in courses if c.status == 'Open']
        closed_sections = [c for c in courses if c.status != 'Open']

        if available_sections:
            response_parts.append("AVAILABLE NOW - You can register for these sections:")
            for course in available_sections:
                available_spots = course.enrollment_capacity - (course.enrollment_current or 0) if course.enrollment_capacity else "Unknown"
                response_parts.append(f"   Section {course.section_name}")
                response_parts.append(f"     Schedule: {course.meeting_information}")
                response_parts.append(f"     Faculty: {course.faculty}")
                response_parts.append(f"     Availability: {available_spots} spots open")
                response_parts.append("")

        if closed_sections:
            response_parts.append("CURRENTLY FULL:")
            for course in closed_sections:
                response_parts.append(f"   Section {course.section_name} - {course.meeting_information}")
            response_parts.append("")

        response_parts.append("TIP: Course availability changes frequently. If all sections are full, check again later or contact the registrar about waitlists.")

        return "\n".join(response_parts)

    def _format_catalog_scheduling_response(self, course_code: str, courses) -> str:
        """Simple catalog-based response for general scheduling questions"""
        try:
            # Get catalog info for semester patterns
            catalog_info = self.course_service._get_course_from_catalog(course_code)

            response_parts = []

            if catalog_info and catalog_info.meeting_information:
                # Extract course details from catalog
                info_lower = catalog_info.meeting_information.lower()

                # Course title and credits
                response_parts.append(f"**{course_code} - {catalog_info.title or 'Data-Centric Concepts and Methods'}**")

                # Extract credits
                import re
                credits_match = re.search(r'(\d+)\s*credits?', catalog_info.meeting_information.lower())
                if credits_match:
                    response_parts.append(f"**Credits:** {credits_match.group(1)}")

                # Semester offerings
                if "fall and spring" in info_lower:
                    response_parts.append("**Typically offered:** Fall and Spring semesters")
                elif "fall" in info_lower and "spring" in info_lower:
                    response_parts.append("**Typically offered:** Fall and Spring semesters")
                elif "fall" in info_lower:
                    response_parts.append("**Typically offered:** Fall semester")
                elif "spring" in info_lower:
                    response_parts.append("**Typically offered:** Spring semester")
                elif "summer" in info_lower:
                    response_parts.append("**Typically offered:** Summer semester")

                # Prerequisites
                if "prerequisite" in catalog_info.meeting_information.lower():
                    prereq_match = re.search(r'prerequisite[s]?:?\s*([^.]+)', catalog_info.meeting_information.lower())
                    if prereq_match:
                        prereq_text = prereq_match.group(1).strip()
                        if prereq_text and prereq_text != "none":
                            response_parts.append(f"**Prerequisites:** {prereq_text}")
                        else:
                            response_parts.append("**Prerequisites:** None")
                else:
                    response_parts.append("**Prerequisites:** None")

            else:
                # Fallback if no catalog info
                response_parts.append(f"**{course_code}**")
                # Check if live data has any semester info
                if courses:
                    course = courses[0]
                    if course.semester:
                        response_parts.append(f"**Currently offered:** {course.semester}")

            # Add note about current availability if there are live sections
            if courses:
                available_count = len([c for c in courses if c.status == 'Open'])
                if available_count > 0:
                    response_parts.append(f"\n*Note: {available_count} section(s) currently available for registration. Ask about \"current term availability\" for details.*")
                else:
                    response_parts.append(f"\n*Note: No sections currently available for registration.*")

            return "\n".join(response_parts)

        except Exception as e:
            self.logger.error(f"Error in catalog scheduling response: {e}")
            return f"**{course_code}** - Please check with the department for current offerings."

    def _format_current_term_response(self, course_code: str, courses) -> str:
        """Detailed current term response for specific availability requests"""
        response_parts = [f"**CURRENT TERM AVAILABILITY FOR {course_code}:**"]
        response_parts.append("")

        available_sections = [c for c in courses if c.status == 'Open']
        closed_sections = [c for c in courses if c.status != 'Open']

        if available_sections:
            response_parts.append("**✅ AVAILABLE NOW - You can register:**")
            for course in available_sections:
                available_spots = course.enrollment_capacity - (course.enrollment_current or 0) if course.enrollment_capacity else "Unknown"
                response_parts.append(f"   **• Section {course.section_name}**")
                response_parts.append(f"     Meeting: {course.meeting_information}")
                response_parts.append(f"     Faculty: {course.faculty}")
                response_parts.append(f"     Enrollment: {course.enrollment_current}/{course.enrollment_capacity} (Available: {available_spots})")
                if course.instructional_methods:
                    response_parts.append(f"     Format: {course.instructional_methods}")
                response_parts.append("")

        if closed_sections:
            response_parts.append("**⚠️ CURRENTLY FULL:**")
            for course in closed_sections:
                response_parts.append(f"   **• Section {course.section_name}** - {course.meeting_information} (Faculty: {course.faculty})")
            response_parts.append("")

        if not available_sections and not closed_sections:
            response_parts.append("**ℹ️ No sections currently offered this term.**")
            response_parts.append("Check back next semester or contact the department.")

        return "\n".join(response_parts)

    def _format_enhanced_scheduling_response(self, course_code: str, courses) -> str:
        """Enhanced scheduling response showing catalog information first"""
        try:
            response_parts = []

            # Get course title from live data if available
            course_title = "Course"
            if courses and courses[0].title:
                course_title = courses[0].title

            # Catalog-style format for general scheduling questions
            response_parts.append(f"**{course_code} - {course_title}**")
            response_parts.append("**Credits:** 3")

            # Show catalog semester offerings for known courses
            if course_code == "GCIS 516":
                response_parts.append("**Typically offered:** Fall and Spring")
                response_parts.append("**Prerequisite:** GCIS 508")
            elif course_code == "GCIS 514":
                response_parts.append("**Typically offered:** Fall and Spring")
                response_parts.append("**Prerequisite:** None")
            elif course_code == "GCIS 515":
                response_parts.append("**Typically offered:** Fall")
                response_parts.append("**Prerequisite:** GCIS 510 and (GCIS 506 or GCIS 521 or GCIS 522)")
            elif course_code == "GCIS 521":
                response_parts.append("**Typically offered:** Fall")
                response_parts.append("**Prerequisite:** GCIS 506 and GCIS 510")
            elif course_code == "GCIS 522":
                response_parts.append("**Typically offered:** Spring")
                response_parts.append("**Prerequisite:** GCIS 506 and GCIS 510")
            elif course_code == "GCIS 523":
                response_parts.append("**Typically offered:** Fall and Spring")
                response_parts.append("**Prerequisite:** None")
            else:
                response_parts.append("**Typically offered:** Check catalog for semester offerings")
                response_parts.append("**Prerequisite:** Check catalog for requirements")

            # Add note about current availability
            available_count = len([c for c in courses if c.status == 'Open'])
            if available_count > 0:
                response_parts.append("")
                response_parts.append(f"*Note: {available_count} section(s) currently available for registration. Ask about \"current term availability\" for details.*")

            return "\n".join(response_parts)

        except Exception as e:
            self.logger.error(f"Error in enhanced scheduling response: {e}")
            return f"**{course_code}** - Please check with the department for current offerings."

    def _format_general_course_response(self, course_code: str, courses) -> str:
        """Format general course information response"""
        # Check data freshness
        health = self.course_service.get_system_health_report()
        freshness_warning = ""
        if not health.get('data_freshness', {}).get('is_fresh', True):
            freshness_warning = "\n\n⚠️ Note: Course data may not be current. Please verify with the registrar."

        response_parts = [f"Here's information about {course_code}:"]

        # For catalog entries, deduplicate based on title and content
        unique_courses = []
        seen_titles = set()

        for course in courses:
            # If it's a catalog entry, only show one instance
            if course.status == 'Catalog':
                course_key = f"{course.course_code}_{course.title}"
                if course_key not in seen_titles:
                    unique_courses.append(course)
                    seen_titles.add(course_key)
            else:
                # For live sections, show all
                unique_courses.append(course)

        for course in unique_courses[:5]:  # Limit to first 5 sections
            formatted = self.course_service.format_course_for_chatbot(course)
            response_parts.append(formatted)

        if len(unique_courses) > 5:
            response_parts.append(f"\n... and {len(unique_courses) - 5} more sections available.")

        response_parts.append(freshness_warning)
        return "\n".join(response_parts)

    def _handle_availability_query(self, query: str) -> str:
        """Handle queries about course availability"""
        # Extract department if mentioned - look for common department codes
        dept_match = re.search(r'\b(CIS|GCIS|BIOL|CHEM|MATH|PHYS|ENGL|HIST|PSYC|ECON|ACCT|NURS|EDUC)\b', query.upper())
        department = dept_match.group(1) if dept_match else None

        available_courses = self.course_service.get_available_courses(department=department)

        if not available_courses:
            dept_filter = f" in {department}" if department else ""
            return f"I couldn't find any available courses{dept_filter} at the moment. Course availability changes frequently, so please check the registrar's website for the most current information."

        response_parts = []
        if department:
            response_parts.append(f"Available courses in {department}:")
        else:
            response_parts.append("Here are some available courses:")

        # Show up to 10 available courses
        for course in available_courses[:10]:
            formatted = self.course_service.format_course_for_chatbot(course)
            response_parts.append(formatted)

        if len(available_courses) > 10:
            response_parts.append(f"\n... and {len(available_courses) - 10} more available courses.")

        return "\n".join(response_parts)

    def _handle_recommendation_query(self, query: str) -> str:
        """Handle course recommendation queries"""
        # For now, return popular courses - could be enhanced with student profile integration
        try:
            # Get some popular courses (simulate by getting courses with good enrollment)
            search_results = self.course_service.search_courses("", limit=15)

            if not search_results:
                return "I don't have enough course data to make recommendations right now. Please check with your academic advisor."

            # Filter for courses that have good availability
            recommended = [c for c in search_results if c.status == 'Open' and
                          c.enrollment_available and c.enrollment_available > 2][:8]

            if not recommended:
                return "Most courses appear to be full right now. I recommend checking with your academic advisor for alternative options."

            response_parts = ["Here are some courses you might consider:"]
            for course in recommended:
                formatted = self.course_service.format_course_for_chatbot(course)
                response_parts.append(formatted)

            response_parts.append("\nFor personalized recommendations, consider speaking with your academic advisor who can better understand your specific academic goals and requirements.")
            return "\n".join(response_parts)

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return "I'm having trouble generating course recommendations right now. Please consult with your academic advisor for personalized course suggestions."

    def _handle_course_search_query(self, query: str) -> str:
        """Handle general course search queries"""
        # Extract search terms (remove common words)
        search_terms = re.sub(r'\b(course|class|section|about|information|tell|me)\b', '', query, flags=re.IGNORECASE).strip()

        if not search_terms:
            return "Please provide more specific information about what courses you're looking for."

        courses = self.course_service.search_courses(search_terms, limit=8)

        if not courses:
            return f"I couldn't find any courses matching '{search_terms}'. Try using specific course codes (like 'CIS 505') or department names."

        response_parts = [f"Found {len(courses)} course(s) matching '{search_terms}':"]
        for course in courses:
            formatted = self.course_service.format_course_for_chatbot(course)
            response_parts.append(formatted)

        return "\n".join(response_parts)

    def _handle_prerequisite_query(self, course_code: str, query: str) -> str:
        """Handle prerequisite-specific queries using catalog data for accuracy"""
        # Return None to let the system search the knowledge base directly
        # This allows the prerequisite information to be found in the academic catalog
        return None

    def _handle_general_prerequisite_query(self, query: str) -> str:
        """Handle prerequisite queries without specific course codes (follow-up questions)"""
        # For follow-up questions like "what is the pre req?", we'll enhance the search
        # to specifically look for prerequisite information and let the LLM handle context

        # Enhanced query focusing on prerequisites
        enhanced_query = f"{query} prerequisites requirements needed courses"

        # Return None to let the system use enhanced knowledge base search
        # The LLM prompt is already configured to handle follow-up prerequisite questions
        return None

    def _handle_general_course_query(self, query: str) -> str:
        """Handle general course-related queries"""
        return "I can help you find specific course information. Try asking about:\n- Specific courses (e.g., 'CIS 505')\n- Available courses in a department (e.g., 'available CIS courses')\n- Course recommendations\n- Course schedules and faculty information"

    def _get_student_profile(self, student_email: str) -> Dict[str, Any]:
        """Get student profile information from database"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect("postgresql://postgres:2056@localhost:5432/chatbot_local", cursor_factory=RealDictCursor)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT enrolled_year, academic_level, primary_major, degree_program
                    FROM student_profiles
                    WHERE user_email = %s
                """, (student_email,))

                result = cur.fetchone()
                if result:
                    return {
                        'enrolled_year': result['enrolled_year'],
                        'academic_level': result['academic_level'] or 'undergraduate',
                        'primary_major': result['primary_major'],
                        'degree_program': result['degree_program']
                    }
                else:
                    self.logger.info(f"No profile found for {student_email}")
                    return {}
            conn.close()
        except Exception as e:
            self.logger.error(f"Error getting student profile: {e}")
            return {}

    def enhanced_retrieve(self, query: str, student_email: Optional[str] = None, top_k: int = 5, query_analysis: Optional[Dict] = None, query_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhanced retrieval that combines course data with general knowledge base.

        Args:
            query: User's question
            student_email: Optional student email for personalized results
            top_k: Number of results to return from knowledge base

        Returns:
            Dictionary with combined course and knowledge base information
        """
        self.logger.info(f"Processing query: '{query[:100]}{'...' if len(query) > 100 else ''}'")

        # Get student profile information if email provided
        student_profile = {}
        if student_email:
            student_profile = self._get_student_profile(student_email)
            self.logger.info(f"Student profile: enrolled_year={student_profile.get('enrolled_year')}, level={student_profile.get('academic_level')}")

        # Use provided query_analysis or analyze the query
        if query_analysis is None:
            query_analysis = self.is_course_query(query)
            self.logger.info(f"Query analysis: {query_analysis}")
        else:
            self.logger.info(f"Using provided query analysis: {query_analysis}")

        response_parts = []
        sources = []

        # Handle course-related queries
        if query_analysis['is_course_related']:
            self.logger.info("Retrieving course information...")
            course_info = self.retrieve_course_information(query, query_analysis)
            if course_info:
                response_parts.append("COURSE INFORMATION:")
                response_parts.append(course_info)
                sources.append("Live Course Database")

        # For course queries, determine if this is a current term request or catalog request
        if query_analysis['is_course_related']:
            # Use explicit query_mode if provided, otherwise fall back to keyword matching
            if query_mode is not None:
                self.logger.info(f"Using explicit query mode: {query_mode}")
                is_current_term_request = (query_mode == "current_sections")
            else:
                # Fall back to keyword matching for backward compatibility
                query_lower = query.lower()
                is_current_term_request = any(keyword in query_lower for keyword in [
                    'current term', 'this term', 'this semester', 'right now', 'available now',
                    'current availability', 'sections available right now', 'can i register now',
                    'enrollment count', 'faculty teaching', 'meeting time', 'what time', 'current sections',
                    'can i take now', 'now', 'current', 'this term'
                ])
                self.logger.info(f"Using keyword matching for query mode detection: {is_current_term_request}")

            if is_current_term_request:
                self.logger.info("Using DIRECT POSTGRESQL DATABASE for current term query (live course data)...")
                # Use PostgreSQL database directly for current/live course information
                from features.courses.course_information_service import CourseInformationService

                try:
                    course_service = CourseInformationService()

                    # Extract course code and faculty name from query if present
                    course_code = query_analysis.get('course_code')
                    faculty_name = query_analysis.get('faculty_name')
                    query_type = query_analysis.get('query_type')

                    if query_type == 'faculty' and faculty_name:
                        # Search for courses taught by specific faculty
                        self.logger.info(f"Searching PostgreSQL for faculty: {faculty_name}")
                        courses = course_service.search_courses(faculty_name, limit=25)

                        # Filter to only include courses taught by this faculty
                        faculty_courses = []
                        for course in courses:
                            if faculty_name.lower() in course.faculty.lower() or \
                               any(name.lower() in course.faculty.lower() for name in faculty_name.split()):
                                faculty_courses.append(course)
                        courses = faculty_courses

                    elif course_code:
                        # Search for specific course
                        self.logger.info(f"Searching PostgreSQL for course: {course_code}")
                        courses = course_service.get_course_details(course_code)

                        if not courses:
                            # Fallback: broader search if specific course not found
                            courses = course_service.search_courses(course_code, limit=10)
                    else:
                        # General course search based on query
                        courses = course_service.search_courses(query, limit=15)

                    if courses:
                        self.logger.info(f"Found {len(courses)} courses in PostgreSQL database")

                        # Format course information for response
                        course_info_lines = []

                        if query_type == 'faculty' and faculty_name:
                            # Special formatting for faculty queries
                            course_info_lines.append(f"COURSES TAUGHT BY {faculty_name.upper()} (Current Term):")
                            course_info_lines.append(f"Found {len(courses)} courses taught by {faculty_name}:")
                            course_info_lines.append("")

                            for course in courses:
                                formatted_course = course_service.format_course_for_chatbot(course)
                                course_info_lines.append(formatted_course)

                            # Add summary
                            if len(courses) > 1:
                                course_info_lines.append("")
                                course_info_lines.append(f"Summary: {faculty_name} teaches {len(courses)} courses this semester.")
                        else:
                            # Standard formatting for other queries
                            course_info_lines.append("LIVE COURSE INFORMATION (Current Database):")

                            for course in courses:
                                formatted_course = course_service.format_course_for_chatbot(course)
                                course_info_lines.append(formatted_course)

                        if response_parts:
                            response_parts.append("\n" + "\n".join(course_info_lines))
                        else:
                            response_parts.extend(course_info_lines)

                        sources.append("PostgreSQL Course Database (Live Data)")
                    else:
                        self.logger.info(f"No courses found in PostgreSQL for query: {query}")
                        if response_parts:
                            response_parts.append("\nNo current course sections found in the live database.")
                        else:
                            response_parts.append("No current course sections found in the live database.")

                except Exception as e:
                    self.logger.error(f"Error querying PostgreSQL database: {e}")
                    # Fallback to vector search if database query fails
                    self.logger.info("Falling back to vector search due to database error...")
                    kb_result = advanced_retrieve_with_confidence(query, top_k=min(15, top_k * 3))
                    if kb_result.get("documents_text") and kb_result["documents_text"].strip():
                        if response_parts:
                            response_parts.append("\nFALLBACK INFORMATION:")
                        else:
                            response_parts.append("FALLBACK INFORMATION:")
                        response_parts.append(kb_result["documents_text"])
                        sources.extend(kb_result.get("sources", []))
            else:
                self.logger.info("Using YEAR-AWARE retrieval for catalog course query...")
                try:
                    from .retriever_year_aware import year_aware_retrieve_with_confidence

                    # Get student information from profile
                    enrolled_year = student_profile.get('enrolled_year')
                    academic_level = student_profile.get('academic_level', 'undergraduate')

                    # If no enrollment year, try to infer from current year
                    if not enrolled_year:
                        current_year = datetime.now().year
                        # Default to current academic year for new students
                        enrolled_year = current_year
                        self.logger.info(f"No enrollment year found, using current year: {enrolled_year}")

                    self.logger.info(f"Year-aware search: enrolled_year={enrolled_year}, academic_level={academic_level}")

                    kb_result = year_aware_retrieve_with_confidence(
                        query,
                        enrolled_year=enrolled_year,
                        academic_level=academic_level,
                        top_k=top_k
                    )

                    if kb_result.get("documents_text") and kb_result["documents_text"].strip():
                        if response_parts:  # Already have live course info
                            response_parts.append("\nACADEMIC CATALOG INFORMATION:")
                        else:
                            response_parts.append("COURSE CATALOG INFORMATION:")
                        response_parts.append(kb_result["documents_text"])
                        sources.append(f"Academic Catalog ({enrolled_year}-{enrolled_year+1})")

                except Exception as e:
                    self.logger.error(f"Year-aware retrieval failed: {e}, falling back to standard")
                    # Fallback to standard retrieval
                    kb_result = advanced_retrieve_with_confidence(query, top_k)
                    if kb_result.get("documents_text") and kb_result["documents_text"].strip():
                        if response_parts:
                            response_parts.append("\nADDITIONAL CONTEXT:")
                        else:
                            response_parts.append("INFORMATION:")
                        response_parts.append(kb_result["documents_text"])
                        sources.extend(kb_result.get("sources", []))
        else:
            # Non-course queries use standard retrieval
            self.logger.info("Using standard retrieval for non-course query...")
            try:
                kb_result = advanced_retrieve_with_confidence(query, top_k)

                if kb_result.get("documents_text") and kb_result["documents_text"].strip():
                    response_parts.append("INFORMATION:")
                    response_parts.append(kb_result["documents_text"])
                    sources.extend(kb_result.get("sources", []))
            except Exception as e:
                self.logger.error(f"Error in standard retrieval: {e}")
                if not response_parts:
                    response_parts.append("I encountered an error while searching for information. Please try rephrasing your question.")

        # Combine all information
        final_response = "\n".join(response_parts) if response_parts else "I couldn't find relevant information for your query."

        return {
            "documents_text": final_response,
            "sources": list(set(sources)),  # Remove duplicates
            "query_analysis": query_analysis,
            "course_data_used": query_analysis['is_course_related'],
            "confidence": query_analysis.get('confidence', 0.0)
        }

# Convenience functions for backward compatibility
def course_aware_retrieve(query: str, top_k: int = 5) -> str:
    """
    Course-aware retrieval function - backward compatible with existing code.
    Returns just the text response.
    """
    retriever = CourseAwareRetriever()
    result = retriever.enhanced_retrieve(query, top_k=top_k)
    return result.get("documents_text", "I was unable to find relevant information.")

def course_aware_retrieve_with_details(query: str, student_email: Optional[str] = None, top_k: int = 5, query_analysis: Optional[Dict] = None, query_mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Course-aware retrieval with full details.
    Returns complete response dictionary with Redis caching for performance.
    """
    # Get cache manager
    cache_manager = get_cache_manager()

    # Generate cache key
    cache_key = cache_manager._generate_cache_key(
        "course_aware_retrieval",
        query=query,
        student_email=student_email or "anonymous",
        top_k=top_k
    )

    # Try cache first
    cached_result = cache_manager.get_cache(cache_key)
    if cached_result:
        logger.info(f"🚀 Course retrieval cache HIT for query: {query[:50]}...")
        return cached_result

    # Cache miss - perform retrieval
    logger.info(f"💔 Course retrieval cache MISS for query: {query[:50]}...")

    retriever = CourseAwareRetriever()
    result = retriever.enhanced_retrieve(query, student_email=student_email, top_k=top_k, query_analysis=query_analysis, query_mode=query_mode)

    # Cache the result
    cache_manager.set_cache(cache_key, result, 'vector_search')

    return result

# Test function
def test_course_aware_retriever():
    """Test the course-aware retriever with various query types"""
    retriever = CourseAwareRetriever()

    test_queries = [
        "What is CIS 505?",
        "Are there any available computer science courses?",
        "I need course recommendations for my major",
        "What courses are offered in biology?",
        "Tell me about database systems course",
        "What is the academic calendar?",  # Non-course query
    ]

    print("Testing Course-Aware Retriever")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        analysis = retriever.is_course_query(query)
        print(f"Analysis: {analysis}")

        result = retriever.enhanced_retrieve(query)
        print(f"Response: {result['documents_text'][:200]}{'...' if len(result['documents_text']) > 200 else ''}")
        print("-" * 40)

if __name__ == "__main__":
    test_course_aware_retriever()