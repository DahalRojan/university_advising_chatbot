#!/usr/bin/env python3
"""
Course Information API
FastAPI endpoints for course search, recommendations, and information retrieval.
Provides reliable, accurate course data to the frontend and chatbot.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .course_information_service import CourseInformationService, CourseInfo

# Create router
router = APIRouter(prefix="/api/courses", tags=["courses"])

# Initialize service
course_service = CourseInformationService()

# Pydantic models for API responses
class CourseInfoResponse(BaseModel):
    course_code: str
    section_name: str
    title: Optional[str]
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

    @classmethod
    def from_course_info(cls, course: CourseInfo):
        return cls(
            course_code=course.course_code,
            section_name=course.section_name,
            title=course.title,
            term=course.term,
            status=course.status,
            enrollment_current=course.enrollment_current,
            enrollment_capacity=course.enrollment_capacity,
            enrollment_available=course.enrollment_available,
            faculty=course.faculty,
            meeting_information=course.meeting_information,
            instructional_methods=course.instructional_methods,
            academic_level=course.academic_level,
            academic_year=course.academic_year,
            semester=course.semester,
            last_updated=course.last_updated,
            is_current=course.is_current
        )

class CourseSearchResponse(BaseModel):
    courses: List[CourseInfoResponse]
    total_results: int
    search_query: str
    filters_applied: Dict[str, Any]
    data_freshness: Dict[str, Any]

class DepartmentInfoResponse(BaseModel):
    department: str
    statistics: Dict[str, Any]
    courses: List[CourseInfoResponse]

class SystemHealthResponse(BaseModel):
    system_status: str
    data_freshness: Dict[str, Any]
    data_quality: Dict[str, Any]
    timestamp: str

class CourseSearchRequest(BaseModel):
    query: str = Field(default="", description="Search term for courses")
    department: Optional[str] = Field(default=None, description="Filter by department code")
    status: Optional[str] = Field(default=None, description="Filter by course status")
    semester: Optional[str] = Field(default=None, description="Filter by semester")
    academic_year: Optional[int] = Field(default=None, description="Filter by academic year")
    available_only: Optional[bool] = Field(default=False, description="Show only available courses")
    limit: Optional[int] = Field(default=20, description="Maximum results to return")

@router.get("/search", response_model=CourseSearchResponse)
async def search_courses(
    query: str = Query(default="", description="Search term for courses"),
    department: Optional[str] = Query(default=None, description="Filter by department code"),
    status: Optional[str] = Query(default=None, description="Filter by course status"),
    semester: Optional[str] = Query(default=None, description="Filter by semester"),
    academic_year: Optional[int] = Query(default=None, description="Filter by academic year"),
    available_only: Optional[bool] = Query(default=False, description="Show only available courses"),
    limit: Optional[int] = Query(default=20, ge=1, le=100, description="Maximum results to return")
):
    """
    Search for courses with intelligent filtering and fuzzy matching.

    Examples:
    - /search?query=CIS 505
    - /search?query=database&department=CIS
    - /search?available_only=true&department=BIOL
    """
    try:
        # Build filters
        filters = {}
        if department:
            filters['department'] = department
        if status:
            filters['status'] = status
        if semester:
            filters['semester'] = semester
        if academic_year:
            filters['academic_year'] = academic_year
        if available_only:
            filters['available_only'] = available_only

        # Perform search
        courses = course_service.search_courses(query, filters=filters, limit=limit)

        # Get data freshness info
        health_report = course_service.get_system_health_report()

        # Convert to response format
        course_responses = [CourseInfoResponse.from_course_info(course) for course in courses]

        return CourseSearchResponse(
            courses=course_responses,
            total_results=len(course_responses),
            search_query=query,
            filters_applied=filters,
            data_freshness=health_report.get('data_freshness', {})
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching courses: {str(e)}")

@router.post("/search", response_model=CourseSearchResponse)
async def search_courses_post(request: CourseSearchRequest):
    """
    Search for courses using POST request for complex queries.
    """
    try:
        # Build filters from request
        filters = {}
        if request.department:
            filters['department'] = request.department
        if request.status:
            filters['status'] = request.status
        if request.semester:
            filters['semester'] = request.semester
        if request.academic_year:
            filters['academic_year'] = request.academic_year
        if request.available_only:
            filters['available_only'] = request.available_only

        # Perform search
        courses = course_service.search_courses(request.query, filters=filters, limit=request.limit)

        # Get data freshness info
        health_report = course_service.get_system_health_report()

        # Convert to response format
        course_responses = [CourseInfoResponse.from_course_info(course) for course in courses]

        return CourseSearchResponse(
            courses=course_responses,
            total_results=len(course_responses),
            search_query=request.query,
            filters_applied=filters,
            data_freshness=health_report.get('data_freshness', {})
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching courses: {str(e)}")

@router.get("/details/{course_code}", response_model=List[CourseInfoResponse])
async def get_course_details(
    course_code: str,
    section: Optional[str] = Query(default=None, description="Specific section to retrieve")
):
    """
    Get detailed information for a specific course.

    Examples:
    - /details/CIS%20505
    - /details/BIOL%20105?section=001
    """
    try:
        courses = course_service.get_course_details(course_code, section)

        if not courses:
            raise HTTPException(status_code=404, detail=f"Course {course_code} not found")

        return [CourseInfoResponse.from_course_info(course) for course in courses]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving course details: {str(e)}")

@router.get("/available", response_model=List[CourseInfoResponse])
async def get_available_courses(
    department: Optional[str] = Query(default=None, description="Filter by department"),
    semester: Optional[str] = Query(default=None, description="Filter by semester"),
    limit: Optional[int] = Query(default=50, ge=1, le=200, description="Maximum results")
):
    """
    Get all available (open) courses with enrollment capacity.

    Examples:
    - /available
    - /available?department=CIS
    - /available?semester=Spring&limit=100
    """
    try:
        courses = course_service.get_available_courses(department, semester)

        # Apply limit
        if limit:
            courses = courses[:limit]

        return [CourseInfoResponse.from_course_info(course) for course in courses]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving available courses: {str(e)}")

@router.get("/department/{department}", response_model=DepartmentInfoResponse)
async def get_department_info(department: str):
    """
    Get comprehensive information about courses in a specific department.

    Examples:
    - /department/CIS
    - /department/BIOL
    """
    try:
        dept_info = course_service.get_department_courses(department)

        if 'error' in dept_info:
            raise HTTPException(status_code=500, detail=dept_info['error'])

        course_responses = [CourseInfoResponse.from_course_info(course) for course in dept_info['courses']]

        return DepartmentInfoResponse(
            department=dept_info['department'],
            statistics=dept_info['statistics'],
            courses=course_responses
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving department info: {str(e)}")

@router.get("/recommendations/{student_email}", response_model=List[CourseInfoResponse])
async def get_course_recommendations(
    student_email: str,
    limit: Optional[int] = Query(default=10, ge=1, le=50, description="Maximum recommendations")
):
    """
    Get personalized course recommendations for a student.

    Examples:
    - /recommendations/student@gannon.edu
    - /recommendations/student@gannon.edu?limit=20
    """
    try:
        recommendations = course_service.recommend_courses_for_student(student_email)

        if not recommendations:
            raise HTTPException(status_code=404, detail=f"No recommendations found for {student_email}")

        # Apply limit
        if limit:
            recommendations = recommendations[:limit]

        return [CourseInfoResponse.from_course_info(course) for course in recommendations]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """
    Get system health and data quality information.
    """
    try:
        health_report = course_service.get_system_health_report()

        return SystemHealthResponse(
            system_status=health_report['system_status'],
            data_freshness=health_report['data_freshness'],
            data_quality=health_report.get('data_quality', {}),
            timestamp=health_report['timestamp']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system health: {str(e)}")

@router.get("/stats")
async def get_course_statistics():
    """
    Get overall course statistics for dashboard purposes.
    """
    try:
        # Get basic stats from the health report
        health_report = course_service.get_system_health_report()

        # Add some additional useful stats
        freshness = health_report.get('data_freshness', {})
        quality = health_report.get('data_quality', {})

        stats = {
            'total_sections': freshness.get('total_sections', 0),
            'current_sections': freshness.get('current_sections', 0),
            'freshness_score': freshness.get('freshness_score', 0),
            'completeness_score': freshness.get('completeness_score', 0),
            'last_update': freshness.get('last_update'),
            'overenrolled_sections': quality.get('overenrolled_sections', 0),
            'sections_without_faculty': quality.get('sections_without_faculty', 0),
            'active_terms': quality.get('active_terms', 0),
            'system_status': health_report.get('system_status', 'unknown')
        }

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

# Utility endpoints for chatbot integration
@router.get("/chatbot/format/{course_code}")
async def format_course_for_chatbot(course_code: str, section: Optional[str] = None):
    """
    Get course information formatted for chatbot responses.
    """
    try:
        courses = course_service.get_course_details(course_code, section)

        if not courses:
            return {"formatted_text": f"Course {course_code} not found."}

        formatted_courses = []
        for course in courses:
            formatted_courses.append(course_service.format_course_for_chatbot(course))

        return {
            "formatted_text": "\n".join(formatted_courses),
            "course_count": len(formatted_courses)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting course info: {str(e)}")

@router.get("/chatbot/quick-search/{query}")
async def quick_search_for_chatbot(query: str):
    """
    Quick search optimized for chatbot responses.
    Returns formatted text ready for display.
    """
    try:
        courses = course_service.search_courses(query, limit=5)

        if not courses:
            return {
                "formatted_text": f"No courses found for '{query}'.",
                "course_count": 0
            }

        formatted_courses = []
        for course in courses:
            formatted_courses.append(course_service.format_course_for_chatbot(course))

        response_text = f"Found {len(courses)} course(s) for '{query}':\n\n" + "\n".join(formatted_courses)

        return {
            "formatted_text": response_text,
            "course_count": len(courses)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in quick search: {str(e)}")