"""
Services Microservice URLs
URL patterns for all services-related endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet, ServiceProviderViewSet, ServiceViewSet,
    ServiceBookingViewSet, ServiceReviewViewSet, ServiceAvailabilityViewSet,
    ServiceCertificationViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='servicecategory')
router.register(r'providers', ServiceProviderViewSet, basename='serviceprovider')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'bookings', ServiceBookingViewSet, basename='servicebooking')
router.register(r'reviews', ServiceReviewViewSet, basename='servicereview')
router.register(r'availability', ServiceAvailabilityViewSet, basename='serviceavailability')
router.register(r'certifications', ServiceCertificationViewSet, basename='servicecertification')

app_name = 'services'

urlpatterns = [
    path('', include(router.urls)),
    
    # path('api/v1/services/search/', views.ServiceSearchView.as_view(), name='service-search'),
    # path('api/v1/services/recommendations/', views.ServiceRecommendationView.as_view(), name='service-recommendations'),
]
