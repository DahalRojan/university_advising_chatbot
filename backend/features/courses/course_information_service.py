#!/usr/bin/env python3
"""
Course Information Service
Provides reliable, accurate course information retrieval for the university advising system.
Integrates with the chatbot to answer course-related queries.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import redis
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CourseInfo:
    """Structured course information"""
    course_code: str
    section_name: str
    title: str
    term: str
    status: str
    enrollment_current: Optional[int]
    enrollment_capacity: Optional[int]
    enrollment_available: Optional[int]
    faculty: Optional[str]
    meeting_information: Optional[str]
    instructional_methods: Optional[str]
    academic_level: Optional[str]
    academic_year: Optional[int]
    semester: Optional[str]
    last_updated: Optional[datetime]
    is_current: bool

class CourseInformationService:
    """
    Comprehensive course information service for reliable course data retrieval.
    Designed to be highly accurate and integrate seamlessly with the chatbot.
    """

    def __init__(self, database_url: str = "postgresql://postgres:2056@localhost:5432/chatbot_local",
                 redis_url: str = "redis://localhost:6379/0", enable_cache: bool = True):
        self.database_url = database_url
        self.logger = logger
        self.data_freshness_threshold = timedelta(hours=24)  # Data older than 24h is stale
        self.enable_cache = enable_cache

        # Initialize Redis connection
        if self.enable_cache:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                self.logger.info("✅ Redis cache connected successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ Redis connection failed: {e}. Running without cache.")
                self.redis_client = None
                self.enable_cache = False
        else:
            self.redis_client = None

        # Cache configuration
        self.cache_ttl = {
            'course_search': 300,      # 5 minutes - frequent queries
            'course_details': 600,     # 10 minutes - specific course info
            'available_courses': 180,  # 3 minutes - availability changes frequently
            'departments': 3600,       # 1 hour - department list rarely changes
            'health_check': 60         # 1 minute - health status
        }

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate consistent cache key"""
        # Sort kwargs for consistent key generation
        key_data = f"{prefix}:" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        # Hash for cleaner keys and avoid Redis key length limits
        return f"course_service:{hashlib.md5(key_data.encode()).hexdigest()}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from Redis cache"""
        if not self.enable_cache or not self.redis_client:
            return None

        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                self.logger.debug(f"🚀 Cache HIT: {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            self.logger.warning(f"Cache read error: {e}")

        self.logger.debug(f"💔 Cache MISS: {cache_key}")
        return None

    def _set_cache(self, cache_key: str, data: Any, ttl_key: str) -> None:
        """Set data in Redis cache"""
        if not self.enable_cache or not self.redis_client:
            return

        try:
            ttl = self.cache_ttl.get(ttl_key, 300)  # Default 5 minutes
            serialized_data = json.dumps(data, default=str)  # Handle datetime objects
            self.redis_client.setex(cache_key, ttl, serialized_data)
            self.logger.debug(f"✅ Cache SET: {cache_key} (TTL: {ttl}s)")
        except Exception as e:
            self.logger.warning(f"Cache write error: {e}")

    def _invalidate_cache_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern"""
        if not self.enable_cache or not self.redis_client:
            return

        try:
            keys = self.redis_client.keys(f"course_service:*{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
                self.logger.info(f"🗑️ Invalidated {len(keys)} cache entries matching: {pattern}")
        except Exception as e:
            self.logger.warning(f"Cache invalidation error: {e}")

    def validate_data_freshness(self) -> Dict[str, Any]:
        """Check if course data is fresh and reliable"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            COUNT(*) as total_sections,
                            COUNT(*) FILTER (WHERE is_current = true) as current_sections,
                            MAX(last_scraped) as last_update,
                            COUNT(*) FILTER (WHERE last_scraped > NOW() - INTERVAL '24 hours') as fresh_sections,
                            COUNT(*) FILTER (WHERE enrollment_current IS NOT NULL) as sections_with_enrollment
                        FROM course_sections
                    """)

                    stats = dict(cur.fetchone())

                    # Calculate data freshness score
                    if stats['total_sections'] > 0:
                        freshness_score = (stats['fresh_sections'] / stats['total_sections']) * 100
                        completeness_score = (stats['sections_with_enrollment'] / stats['total_sections']) * 100
                    else:
                        freshness_score = 0
                        completeness_score = 0

                    return {
                        'is_fresh': freshness_score >= 80,  # At least 80% of data is fresh
                        'is_complete': completeness_score >= 70,  # At least 70% has enrollment data
                        'freshness_score': round(freshness_score, 1),
                        'completeness_score': round(completeness_score, 1),
                        'last_update': stats['last_update'],
                        'total_sections': stats['total_sections'],
                        'current_sections': stats['current_sections']
                    }

        except Exception as e:
            self.logger.error(f"Error validating data freshness: {e}")
            return {'is_fresh': False, 'is_complete': False, 'error': str(e)}

    def search_courses(self, query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[CourseInfo]:
        """
        Intelligent course search with fuzzy matching and multiple search criteria.

        Args:
            query: Search term (course code, title, faculty, etc.)
            filters: Optional filters (department, status, semester, etc.)
            limit: Maximum results to return
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            "search_courses",
            query=query or "",
            filters=filters or {},
            limit=limit
        )

        # Try cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            # Convert cached dict back to CourseInfo objects
            return [CourseInfo(**course_data) for course_data in cached_result]

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Build dynamic query based on search term and filters
                    where_conditions = ["is_current = true"]
                    params = []

                    if query and query.strip():
                        # Support multiple search patterns
                        query = query.strip()

                        # Course code pattern (e.g., "CIS 505", "BIOL301")
                        if re.match(r'^[A-Z]{2,4}\s?\d{3,4}[A-Z]?$', query.upper()):
                            normalized_code = re.sub(r'([A-Z]+)(\d+)', r'\1 \2', query.upper())
                            where_conditions.append("course_code ILIKE %s")
                            params.append(f"%{normalized_code}%")
                        else:
                            # General text search across multiple fields
                            where_conditions.append("""(
                                course_code ILIKE %s OR
                                title ILIKE %s OR
                                faculty ILIKE %s OR
                                meeting_information ILIKE %s
                            )""")
                            search_pattern = f"%{query}%"
                            params.extend([search_pattern] * 4)

                    # Apply filters
                    if filters:
                        if 'department' in filters:
                            where_conditions.append("course_code LIKE %s")
                            params.append(f"{filters['department'].upper()}%")

                        if 'status' in filters:
                            where_conditions.append("status = %s")
                            params.append(filters['status'])

                        if 'semester' in filters:
                            where_conditions.append("semester = %s")
                            params.append(filters['semester'])

                        if 'academic_year' in filters:
                            where_conditions.append("academic_year = %s")
                            params.append(filters['academic_year'])

                        if 'available_only' in filters and filters['available_only']:
                            where_conditions.append("status = 'Open'")
                            where_conditions.append("enrollment_current < enrollment_capacity")

                    # Construct final query
                    sql = f"""
                        SELECT
                            course_code, section_name, title, term, status,
                            enrollment_current, enrollment_capacity,
                            CASE
                                WHEN enrollment_capacity IS NOT NULL AND enrollment_current IS NOT NULL
                                THEN enrollment_capacity - enrollment_current
                                ELSE NULL
                            END as enrollment_available,
                            faculty, meeting_information, instructional_methods,
                            academic_level, academic_year, semester, last_scraped, is_current
                        FROM course_sections
                        WHERE {' AND '.join(where_conditions)}
                        ORDER BY course_code, section_name
                        LIMIT %s
                    """

                    params.append(limit)
                    cur.execute(sql, params)

                    results = []
                    for row in cur.fetchall():
                        results.append(CourseInfo(
                            course_code=row['course_code'],
                            section_name=row['section_name'],
                            title=row['title'],
                            term=row['term'],
                            status=row['status'],
                            enrollment_current=row['enrollment_current'],
                            enrollment_capacity=row['enrollment_capacity'],
                            enrollment_available=row['enrollment_available'],
                            faculty=row['faculty'],
                            meeting_information=row['meeting_information'],
                            instructional_methods=row['instructional_methods'],
                            academic_level=row['academic_level'],
                            academic_year=row['academic_year'],
                            semester=row['semester'],
                            last_updated=row['last_scraped'],
                            is_current=row['is_current']
                        ))

                    # Cache the results (convert CourseInfo to dict for JSON serialization)
                    cache_data = [
                        {
                            'course_code': course.course_code,
                            'section_name': course.section_name,
                            'title': course.title,
                            'term': course.term,
                            'status': course.status,
                            'enrollment_current': course.enrollment_current,
                            'enrollment_capacity': course.enrollment_capacity,
                            'enrollment_available': course.enrollment_available,
                            'faculty': course.faculty,
                            'meeting_information': course.meeting_information,
                            'instructional_methods': course.instructional_methods,
                            'academic_level': course.academic_level,
                            'academic_year': course.academic_year,
                            'semester': course.semester,
                            'last_updated': course.last_updated,
                            'is_current': course.is_current
                        }
                        for course in results
                    ]
                    self._set_cache(cache_key, cache_data, 'course_search')

                    return results

        except Exception as e:
            self.logger.error(f"Error searching courses: {e}")
            return []

    def get_course_details(self, course_code: str, section: Optional[str] = None) -> List[CourseInfo]:
        """Get detailed information for a specific course"""
        filters = {}
        if section:
            # Search for specific section
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            course_code, section_name, title, term, status,
                            enrollment_current, enrollment_capacity,
                            enrollment_capacity - COALESCE(enrollment_current, 0) as enrollment_available,
                            faculty, meeting_information, instructional_methods,
                            academic_level, academic_year, semester, last_scraped, is_current
                        FROM course_sections
                        WHERE course_code ILIKE %s AND section_name = %s AND is_current = true
                        ORDER BY term DESC
                    """, (course_code, section))

                    results = []
                    for row in cur.fetchall():
                        results.append(CourseInfo(
                            course_code=row['course_code'],
                            section_name=row['section_name'],
                            title=row['title'],
                            term=row['term'],
                            status=row['status'],
                            enrollment_current=row['enrollment_current'],
                            enrollment_capacity=row['enrollment_capacity'],
                            enrollment_available=row['enrollment_available'],
                            faculty=row['faculty'],
                            meeting_information=row['meeting_information'],
                            instructional_methods=row['instructional_methods'],
                            academic_level=row['academic_level'],
                            academic_year=row['academic_year'],
                            semester=row['semester'],
                            last_updated=row['last_scraped'],
                            is_current=row['is_current']
                        ))
                    return results
        else:
            # Search all sections of the course
            live_sections = self.search_courses(course_code)

            # If no live sections found, create a placeholder from academic catalog
            if not live_sections:
                catalog_info = self._get_course_from_catalog(course_code)
                if catalog_info:
                    return [catalog_info]

            return live_sections

    def get_available_courses(self, department: Optional[str] = None, semester: Optional[str] = None) -> List[CourseInfo]:
        """Get all available (open) courses with enrollment capacity"""
        filters = {
            'available_only': True
        }
        if department:
            filters['department'] = department
        if semester:
            filters['semester'] = semester

        return self.search_courses("", filters=filters, limit=100)

    def get_department_courses(self, department: str) -> Dict[str, Any]:
        """Get comprehensive information about courses in a department"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get department statistics
                    cur.execute("""
                        SELECT
                            COUNT(*) as total_sections,
                            COUNT(DISTINCT course_code) as unique_courses,
                            COUNT(*) FILTER (WHERE status = 'Open') as open_sections,
                            COUNT(*) FILTER (WHERE status = 'Closed') as closed_sections,
                            COUNT(*) FILTER (WHERE status = 'Waitlisted') as waitlisted_sections,
                            SUM(enrollment_capacity) as total_capacity,
                            SUM(enrollment_current) as total_enrolled
                        FROM course_sections
                        WHERE course_code LIKE %s AND is_current = true
                    """, (f"{department.upper()}%",))

                    stats = dict(cur.fetchone())

                    # Get course list
                    courses = self.search_courses("", filters={'department': department}, limit=200)

                    return {
                        'department': department.upper(),
                        'statistics': stats,
                        'courses': courses
                    }

        except Exception as e:
            self.logger.error(f"Error getting department courses: {e}")
            return {'department': department, 'error': str(e)}

    def recommend_courses_for_student(self, student_email: str, preferences: Optional[Dict] = None) -> List[CourseInfo]:
        """
        Recommend courses based on student profile and preferences.
        This integrates with the student's academic information.
        """
        try:
            # Get student context
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get student information
                    cur.execute("""
                        SELECT major, current_year, gpa
                        FROM student_context_view
                        WHERE user_email = %s
                    """, (student_email,))

                    student_info = cur.fetchone()
                    if not student_info:
                        self.logger.warning(f"No student info found for {student_email}")
                        return []

                    # Build recommendation criteria
                    recommendations = []

                    # Major-related courses
                    if student_info['major']:
                        major_keywords = student_info['major'].split()
                        for keyword in major_keywords:
                            if len(keyword) >= 3:  # Avoid short words
                                courses = self.search_courses(keyword,
                                                            filters={'available_only': True},
                                                            limit=10)
                                recommendations.extend(courses)

                    # Remove duplicates and limit results
                    seen_courses = set()
                    unique_recommendations = []
                    for course in recommendations:
                        course_key = f"{course.course_code}_{course.section_name}"
                        if course_key not in seen_courses:
                            seen_courses.add(course_key)
                            unique_recommendations.append(course)

                    return unique_recommendations[:20]  # Top 20 recommendations

        except Exception as e:
            self.logger.error(f"Error recommending courses: {e}")
            return []

    def format_course_for_chatbot(self, course: CourseInfo) -> str:
        """Format course information for chatbot responses"""
        status_indicator = {
            'Open': '[OPEN]',
            'Closed': '[CLOSED]',
            'Waitlisted': '[WAITLIST]',
            'Catalog': '[CATALOG]'
        }

        indicator = status_indicator.get(course.status, '[UNKNOWN]')

        # Handle catalog entries differently - they don't have enrollment or live sections
        if course.status == 'Catalog':
            return f"{indicator} {course.course_code} - {course.title or 'No title'} | {course.meeting_information or 'See department for current scheduling'}"

        enrollment_info = ""
        if course.enrollment_current is not None and course.enrollment_capacity is not None:
            available = course.enrollment_capacity - course.enrollment_current
            enrollment_info = f" | Enrollment: {course.enrollment_current}/{course.enrollment_capacity} (Available: {available})"

        faculty_info = f" | Faculty: {course.faculty}" if course.faculty else ""
        meeting_info = f" | Meeting: {course.meeting_information}" if course.meeting_information else ""

        return f"{indicator} {course.course_code} {course.section_name} - {course.title or 'No title'}{enrollment_info}{faculty_info}{meeting_info}"

    def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report for monitoring"""
        freshness_check = self.validate_data_freshness()

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get additional health metrics
                    cur.execute("""
                        SELECT
                            COUNT(*) FILTER (WHERE enrollment_current > enrollment_capacity) as overenrolled_sections,
                            COUNT(*) FILTER (WHERE faculty IS NULL OR faculty = '') as sections_without_faculty,
                            COUNT(*) FILTER (WHERE meeting_information IS NULL OR meeting_information = '') as sections_without_meeting_info,
                            COUNT(DISTINCT term) as active_terms
                        FROM course_sections
                        WHERE is_current = true
                    """)

                    health_metrics = dict(cur.fetchone())

                    return {
                        'data_freshness': freshness_check,
                        'data_quality': health_metrics,
                        'timestamp': datetime.now().isoformat(),
                        'system_status': 'healthy' if freshness_check.get('is_fresh', False) else 'degraded'
                    }

        except Exception as e:
            return {
                'data_freshness': freshness_check,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'system_status': 'error'
            }

    def _get_course_from_catalog(self, course_code: str) -> Optional[CourseInfo]:
        """
        Get course information from the academic catalog (courses table)
        when no live sections are available
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT code, title, description, credits, level, prerequisites
                        FROM courses
                        WHERE code ILIKE %s AND is_active = true
                        LIMIT 1
                    """, (course_code,))

                    row = cur.fetchone()
                    if row:
                        # Determine typical semester from description
                        description = row['description'] or ''
                        typical_semester = None
                        if 'spring' in description.lower():
                            typical_semester = 'Spring'
                        elif 'fall' in description.lower():
                            typical_semester = 'Fall'
                        elif 'summer' in description.lower():
                            typical_semester = 'Summer'

                        # Create CourseInfo object from catalog data
                        prerequisites_text = f"Prerequisites: {row['prerequisites']}" if row['prerequisites'] else ""
                        meeting_info = f"Typically offered: {typical_semester or 'See Catalog'}, {row['credits']} credits. {prerequisites_text}"

                        return CourseInfo(
                            course_code=row['code'],
                            section_name='N/A',  # No section for catalog info
                            title=row['title'],
                            term='Not Currently Offered',
                            status='Catalog',
                            enrollment_current=None,
                            enrollment_capacity=None,
                            enrollment_available=None,
                            faculty='See Department',
                            meeting_information=meeting_info.strip(),
                            instructional_methods=None,
                            academic_level=row['level'],
                            academic_year=None,
                            semester=typical_semester,
                            last_updated=None,
                            is_current=False
                        )
                    return None

        except Exception as e:
            self.logger.error(f"Error getting course from catalog: {e}")
            return None

# Example usage and testing functions
def test_course_service():
    """Test the course information service"""
    service = CourseInformationService()

    print("Testing Course Information Service...")
    print("=" * 60)

    # Test data freshness
    health = service.get_system_health_report()
    print(f"System Health: {health['system_status']}")
    print(f"Data Freshness: {health['data_freshness']['freshness_score']}%")
    print()

    # Test course search
    print("Testing Course Search:")
    courses = service.search_courses("CIS")
    for course in courses[:3]:
        print(service.format_course_for_chatbot(course))
    print()

    # Test specific course lookup
    print("Testing Specific Course Lookup:")
    bio_courses = service.get_course_details("BIOL 105")
    for course in bio_courses[:2]:
        print(service.format_course_for_chatbot(course))
    print()

    # Test available courses
    print("Testing Available Courses:")
    available = service.get_available_courses(department="CIS")
    for course in available[:3]:
        print(service.format_course_for_chatbot(course))

if __name__ == "__main__":
    test_course_service()