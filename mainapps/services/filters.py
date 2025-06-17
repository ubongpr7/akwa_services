"""
Services Microservice Filters
Advanced filtering for services-related models
"""

import django_filters
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    ServiceCategory, ServiceProvider, Service, ServiceBooking,
    ServiceReview, ServiceAvailability
)


class ServiceCategoryFilter(django_filters.FilterSet):
    """Filter for service categories"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    is_professional = django_filters.BooleanFilter()
    has_services = django_filters.BooleanFilter(method='filter_has_services')
    parent_id = django_filters.UUIDFilter(field_name='parent__id')
    
    class Meta:
        model = ServiceCategory
        fields = ['name', 'is_professional', 'parent_id']
    
    def filter_has_services(self, queryset, name, value):
        if value:
            return queryset.filter(services__is_active=True).distinct()
        return queryset


class ServiceProviderFilter(django_filters.FilterSet):
    """Advanced filter for service providers"""
    
    # Basic filters
    business_name = django_filters.CharFilter(lookup_expr='icontains')
    city = django_filters.CharFilter(lookup_expr='icontains')
    state = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='iexact')
    
    # Specialization filters
    specialization = django_filters.CharFilter(
        field_name='specializations__slug',
        lookup_expr='iexact'
    )
    specializations = django_filters.CharFilter(method='filter_specializations')
    
    # Rating and review filters
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='lte')
    min_reviews = django_filters.NumberFilter(field_name='total_reviews', lookup_expr='gte')
    
    # Pricing filters
    min_hourly_rate = django_filters.NumberFilter(field_name='hourly_rate_min', lookup_expr='gte')
    max_hourly_rate = django_filters.NumberFilter(field_name='hourly_rate_max', lookup_expr='lte')
    
    # Status filters
    is_available = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    is_verified = django_filters.BooleanFilter()
    background_checked = django_filters.BooleanFilter()
    
    # Experience filters
    min_years_experience = django_filters.NumberFilter(
        field_name='years_in_business',
        lookup_expr='gte'
    )
    min_jobs_completed = django_filters.NumberFilter(
        field_name='total_jobs_completed',
        lookup_expr='gte'
    )
    
    # Availability filters
    available_date = django_filters.DateFilter(method='filter_available_date')
    available_today = django_filters.BooleanFilter(method='filter_available_today')
    available_this_week = django_filters.BooleanFilter(method='filter_available_this_week')
    
    # Location filters (for future geolocation)
    near_location = django_filters.CharFilter(method='filter_near_location')
    within_radius = django_filters.NumberFilter(method='filter_within_radius')
    
    # Search
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = ServiceProvider
        fields = [
            'business_name', 'city', 'state', 'country', 'is_available',
            'is_featured', 'is_verified', 'background_checked'
        ]
    
    def filter_specializations(self, queryset, name, value):
        """Filter by multiple specializations (comma-separated)"""
        if value:
            specializations = [s.strip() for s in value.split(',')]
            return queryset.filter(specializations__slug__in=specializations).distinct()
        return queryset
    
    def filter_available_date(self, queryset, name, value):
        """Filter providers available on specific date"""
        if value:
            return queryset.filter(
                availability__date=value,
                availability__is_available=True,
                availability__is_blocked=False
            ).distinct()
        return queryset
    
    def filter_available_today(self, queryset, name, value):
        """Filter providers available today"""
        if value:
            today = timezone.now().date()
            return queryset.filter(
                availability__date=today,
                availability__is_available=True,
                availability__is_blocked=False
            ).distinct()
        return queryset
    
    def filter_available_this_week(self, queryset, name, value):
        """Filter providers available this week"""
        if value:
            today = timezone.now().date()
            week_end = today + timedelta(days=7)
            return queryset.filter(
                availability__date__range=[today, week_end],
                availability__is_available=True,
                availability__is_blocked=False
            ).distinct()
        return queryset
    
    def filter_near_location(self, queryset, name, value):
        """Filter providers near a location (placeholder for geolocation)"""
        # This would implement geolocation-based filtering
        # For now, filter by city name
        if value:
            return queryset.filter(city__icontains=value)
        return queryset
    
    def filter_within_radius(self, queryset, name, value):
        """Filter providers within radius (placeholder for geolocation)"""
        # This would implement radius-based filtering with lat/lng
        # For now, return all providers
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Global search across provider fields"""
        if value:
            return queryset.filter(
                Q(business_name__icontains=value) |
                Q(description__icontains=value) |
                Q(short_description__icontains=value) |
                Q(specializations__name__icontains=value) |
                Q(city__icontains=value) |
                Q(services__title__icontains=value)
            ).distinct()
        return queryset


class ServiceFilter(django_filters.FilterSet):
    """Advanced filter for services"""
    
    # Basic filters
    title = django_filters.CharFilter(lookup_expr='icontains')
    service_type = django_filters.ChoiceFilter(choices=Service._meta.get_field('service_type').choices)
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='iexact')
    categories = django_filters.CharFilter(method='filter_categories')
    
    # Provider filters
    provider = django_filters.UUIDFilter(field_name='provider__id')
    provider_city = django_filters.CharFilter(field_name='provider__city', lookup_expr='icontains')
    provider_verified = django_filters.BooleanFilter(field_name='provider__is_verified')
    
    # Pricing filters
    pricing_type = django_filters.ChoiceFilter(choices=Service._meta.get_field('pricing_type').choices)
    min_hourly_rate = django_filters.NumberFilter(field_name='hourly_rate', lookup_expr='gte')
    max_hourly_rate = django_filters.NumberFilter(field_name='hourly_rate', lookup_expr='lte')
    min_fixed_price = django_filters.NumberFilter(field_name='fixed_price', lookup_expr='gte')
    max_fixed_price = django_filters.NumberFilter(field_name='fixed_price', lookup_expr='lte')
    
    # Rating filters
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='lte')
    min_reviews = django_filters.NumberFilter(field_name='total_reviews', lookup_expr='gte')
    
    # Feature filters
    materials_included = django_filters.BooleanFilter()
    requires_consultation = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    
    # Duration filters
    max_duration_hours = django_filters.NumberFilter(method='filter_max_duration')
    min_duration_hours = django_filters.NumberFilter(method='filter_min_duration')
    
    # Availability filters
    available_date = django_filters.DateFilter(method='filter_available_date')
    available_day = django_filters.NumberFilter(method='filter_available_day')
    
    # Search
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Service
        fields = [
            'title', 'service_type', 'pricing_type', 'materials_included',
            'requires_consultation', 'is_featured', 'is_active'
        ]
    
    def filter_categories(self, queryset, name, value):
        """Filter by multiple categories (comma-separated)"""
        if value:
            categories = [c.strip() for c in value.split(',')]
            return queryset.filter(category__slug__in=categories)
        return queryset
    
    def filter_max_duration(self, queryset, name, value):
        """Filter services with duration less than specified hours"""
        if value:
            max_duration = timedelta(hours=value)
            return queryset.filter(estimated_duration__lte=max_duration)
        return queryset
    
    def filter_min_duration(self, queryset, name, value):
        """Filter services with duration greater than specified hours"""
        if value:
            min_duration = timedelta(hours=value)
            return queryset.filter(estimated_duration__gte=min_duration)
        return queryset
    
    def filter_available_date(self, queryset, name, value):
        """Filter services available on specific date"""
        if value:
            return queryset.filter(
                availability__date=value,
                availability__is_available=True,
                availability__is_blocked=False
            ).distinct()
        return queryset
    
    def filter_available_day(self, queryset, name, value):
        """Filter services available on specific day of week (0=Monday)"""
        if value is not None:
            return queryset.filter(available_days__contains=[value])
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Global search across service fields"""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value) |
                Q(short_description__icontains=value) |
                Q(category__name__icontains=value) |
                Q(provider__business_name__icontains=value) |
                Q(customer_requirements__icontains=value) |
                Q(tools_equipment__icontains=value)
            ).distinct()
        return queryset


class ServiceBookingFilter(django_filters.FilterSet):
    """Filter for service bookings"""
    
    # Basic filters
    booking_reference = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=ServiceBooking._meta.get_field('status').choices)
    
    # Date filters
    booking_date_from = django_filters.DateFilter(field_name='booking_date', lookup_expr='gte')
    booking_date_to = django_filters.DateFilter(field_name='booking_date', lookup_expr='lte')
    scheduled_date_from = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='gte')
    scheduled_date_to = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='lte')
    
    # Service and provider filters
    service = django_filters.UUIDFilter(field_name='service__id')
    provider = django_filters.UUIDFilter(field_name='provider__id')
    service_type = django_filters.CharFilter(field_name='service__service_type')
    
    # Customer filters
    customer_user_id = django_filters.CharFilter()
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    customer_email = django_filters.CharFilter(lookup_expr='icontains')
    
    # Price filters
    min_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    
    # Payment filters
    payment_status = django_filters.CharFilter()
    
    # Time-based filters
    today = django_filters.BooleanFilter(method='filter_today')
    this_week = django_filters.BooleanFilter(method='filter_this_week')
    this_month = django_filters.BooleanFilter(method='filter_this_month')
    upcoming = django_filters.BooleanFilter(method='filter_upcoming')
    past = django_filters.BooleanFilter(method='filter_past')
    
    class Meta:
        model = ServiceBooking
        fields = [
            'booking_reference', 'status', 'service', 'provider',
            'customer_user_id', 'payment_status'
        ]
    
    def filter_today(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(scheduled_date=today)
        return queryset
    
    def filter_this_week(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return queryset.filter(scheduled_date__range=[week_start, week_end])
        return queryset
    
    def filter_this_month(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(
                scheduled_date__year=today.year,
                scheduled_date__month=today.month
            )
        return queryset
    
    def filter_upcoming(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(scheduled_date__gte=today)
        return queryset
    
    def filter_past(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(scheduled_date__lt=today)
        return queryset


class ServiceReviewFilter(django_filters.FilterSet):
    """Filter for service reviews"""
    
    # Basic filters
    rating = django_filters.NumberFilter()
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    
    # Service and provider filters
    service = django_filters.UUIDFilter(field_name='service__id')
    provider = django_filters.UUIDFilter(field_name='provider__id')
    service_type = django_filters.CharFilter(field_name='service__service_type')
    
    # Content filters
    has_comment = django_filters.BooleanFilter(method='filter_has_comment')
    has_response = django_filters.BooleanFilter(method='filter_has_response')
    
    # Recommendation filters
    would_recommend = django_filters.BooleanFilter()
    would_book_again = django_filters.BooleanFilter()
    
    # Status filters
    is_verified = django_filters.BooleanFilter()
    is_published = django_filters.BooleanFilter()
    
    # Date filters
    created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = ServiceReview
        fields = [
            'rating', 'service', 'provider', 'would_recommend',
            'would_book_again', 'is_verified', 'is_published'
        ]
    
    def filter_has_comment(self, queryset, name, value):
        if value:
            return queryset.exclude(comment='')
        return queryset.filter(comment='')
    
    def filter_has_response(self, queryset, name, value):
        if value:
            return queryset.exclude(response='')
        return queryset.filter(response='')


class ServiceAvailabilityFilter(django_filters.FilterSet):
    """Filter for service availability"""
    
    # Date filters
    date = django_filters.DateFilter()
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    
    # Time filters
    start_time_from = django_filters.TimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = django_filters.TimeFilter(field_name='start_time', lookup_expr='lte')
    
    # Provider and service filters
    provider = django_filters.UUIDFilter(field_name='provider__id')
    service = django_filters.UUIDFilter(field_name='service__id')
    
    # Status filters
    is_available = django_filters.BooleanFilter()
    is_blocked = django_filters.BooleanFilter()
    
    # Special filters
    has_special_rate = django_filters.BooleanFilter(method='filter_has_special_rate')
    today = django_filters.BooleanFilter(method='filter_today')
    this_week = django_filters.BooleanFilter(method='filter_this_week')
    
    class Meta:
        model = ServiceAvailability
        fields = ['date', 'provider', 'service', 'is_available', 'is_blocked']
    
    def filter_has_special_rate(self, queryset, name, value):
        if value:
            return queryset.filter(special_rate__isnull=False)
        return queryset.filter(special_rate__isnull=True)
    
    def filter_today(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(date=today)
        return queryset
    
    def filter_this_week(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            week_end = today + timedelta(days=7)
            return queryset.filter(date__range=[today, week_end])
        return queryset
