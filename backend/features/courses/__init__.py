"""
Course Information Module
Provides comprehensive course data retrieval and management for the university advising system.
"""

from .course_information_service import CourseInformationService, CourseInfo
from .course_api import router as course_router

__all__ = ['CourseInformationService', 'CourseInfo', 'course_router']