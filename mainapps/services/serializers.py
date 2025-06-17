"""
Services Microservice Serializers
Comprehensive serializers for all services-related models
"""

from rest_framework import serializers
from django.db.models import Avg, Count, Q
from decimal import Decimal
from .models import (
    ServiceCategory, ServiceProvider, Service, ServiceImage,
    ServiceAvailability, ServiceBooking, ServiceReview, ServiceCertification
)


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for service categories"""
    
    subcategories = serializers.SerializerMethodField()
    services_count = serializers.SerializerMethodField()
    providers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'parent',
            'is_professional', 'subcategories', 'services_count', 'providers_count'
        ]
    
    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return ServiceCategorySerializer(obj.subcategories.all(), many=True).data
        return []
    
    def get_services_count(self, obj):
        return obj.services.filter(is_active=True).count()
    
    def get_providers_count(self, obj):
        return obj.providers.filter(is_active=True).count()


class ServiceImageSerializer(serializers.ModelSerializer):
    """Serializer for service images"""
    
    class Meta:
        model = ServiceImage
        fields = [
            'id', 'image', 'caption', 'alt_text', 'is_primary', 'order'
        ]


class ServiceCertificationSerializer(serializers.ModelSerializer):
    """Serializer for service provider certifications"""
    
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCertification
        fields = [
            'id', 'name', 'issuing_organization', 'certification_number',
            'issue_date', 'expiry_date', 'is_verified', 'verified_at',
            'is_expired', 'days_until_expiry'
        ]
    
    def get_is_expired(self, obj):
        if obj.expiry_date:
            from django.utils import timezone
            return obj.expiry_date < timezone.now().date()
        return False
    
    def get_days_until_expiry(self, obj):
        if obj.expiry_date:
            from django.utils import timezone
            delta = obj.expiry_date - timezone.now().date()
            return delta.days if delta.days > 0 else 0
        return None


class ServiceProviderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for provider listings"""
    
    specializations = ServiceCategorySerializer(many=True, read_only=True)
    services_count = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    next_available = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'business_name', 'slug', 'short_description', 'city', 'state',
            'average_rating', 'total_reviews', 'total_jobs_completed',
            'hourly_rate_min', 'hourly_rate_max', 'currency', 'is_available',
            'is_featured', 'is_verified', 'background_checked', 'response_time',
            'specializations', 'services_count', 'distance', 'next_available'
        ]
    
    def get_services_count(self, obj):
        return obj.services.filter(is_active=True).count()
    
    def get_distance(self, obj):
        # This would be calculated based on user's location
        # For now, return None - implement with geolocation
        return None
    
    def get_next_available(self, obj):
        from django.utils import timezone
        next_slot = obj.availability.filter(
            date__gte=timezone.now().date(),
            is_available=True,
            is_blocked=False
        ).first()
        return next_slot.date if next_slot else None


class ServiceProviderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for service providers"""
    
    specializations = ServiceCategorySerializer(many=True, read_only=True)
    certifications = ServiceCertificationSerializer(many=True, read_only=True)
    services_count = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    availability_summary = serializers.SerializerMethodField()
    rating_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'business_name', 'slug', 'description', 'short_description',
            'phone', 'email', 'website', 'address', 'city', 'state', 'country',
            'postal_code', 'latitude', 'longitude', 'service_radius',
            'license_number', 'insurance_policy', 'years_in_business',
            'employee_count', 'specializations', 'average_rating', 'total_reviews',
            'total_jobs_completed', 'is_available', 'response_time',
            'hourly_rate_min', 'hourly_rate_max', 'currency', 'is_active',
            'is_featured', 'is_verified', 'background_checked',
            'certifications', 'services_count', 'recent_reviews',
            'availability_summary', 'rating_breakdown', 'created_at'
        ]
    
    def get_services_count(self, obj):
        return obj.services.filter(is_active=True).count()
    
    def get_recent_reviews(self, obj):
        recent_reviews = obj.reviews.filter(is_published=True)[:5]
        return ServiceReviewSerializer(recent_reviews, many=True).data
    
    def get_availability_summary(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        available_slots = obj.availability.filter(
            date__range=[today, next_week],
            is_available=True,
            is_blocked=False
        ).count()
        
        return {
            'available_slots_next_7_days': available_slots,
            'is_available_today': obj.availability.filter(
                date=today,
                is_available=True,
                is_blocked=False
            ).exists()
        }
    
    def get_rating_breakdown(self, obj):
        reviews = obj.reviews.filter(is_published=True)
        if not reviews.exists():
            return None
        
        return {
            'quality_avg': reviews.aggregate(avg=Avg('quality_rating'))['avg'] or 0,
            'timeliness_avg': reviews.aggregate(avg=Avg('timeliness_rating'))['avg'] or 0,
            'communication_avg': reviews.aggregate(avg=Avg('communication_rating'))['avg'] or 0,
            'value_avg': reviews.aggregate(avg=Avg('value_rating'))['avg'] or 0,
            'professionalism_avg': reviews.aggregate(avg=Avg('professionalism_rating'))['avg'] or 0,
            'recommendation_rate': reviews.filter(would_recommend=True).count() / reviews.count() * 100
        }


class ServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for service listings"""
    
    provider = ServiceProviderListSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'slug', 'short_description', 'service_type',
            'pricing_type', 'hourly_rate', 'fixed_price', 'minimum_charge',
            'estimated_duration', 'materials_included', 'travel_charge',
            'average_rating', 'total_reviews', 'is_active', 'is_featured',
            'requires_consultation', 'provider', 'category', 'primary_image'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ServiceImageSerializer(primary_image).data
        return None


class ServiceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for services"""
    
    provider = ServiceProviderDetailSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    availability_next_7_days = serializers.SerializerMethodField()
    similar_services = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'service_type', 'pricing_type', 'hourly_rate', 'fixed_price',
            'minimum_charge', 'estimated_duration', 'materials_included',
            'travel_charge', 'customer_requirements', 'tools_equipment',
            'available_days', 'available_hours_start', 'available_hours_end',
            'advance_booking_required', 'average_rating', 'total_reviews',
            'is_active', 'is_featured', 'requires_consultation',
            'provider', 'category', 'images', 'recent_reviews',
            'availability_next_7_days', 'similar_services', 'created_at'
        ]
    
    def get_recent_reviews(self, obj):
        recent_reviews = obj.reviews.filter(is_published=True)[:5]
        return ServiceReviewSerializer(recent_reviews, many=True).data
    
    def get_availability_next_7_days(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        availability = obj.availability.filter(
            date__range=[today, next_week],
            is_available=True,
            is_blocked=False
        ).order_by('date', 'start_time')
        
        return ServiceAvailabilitySerializer(availability, many=True).data
    
    def get_similar_services(self, obj):
        similar = Service.objects.filter(
            category=obj.category,
            is_active=True
        ).exclude(id=obj.id)[:4]
        
        return ServiceListSerializer(similar, many=True).data


class ServiceAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for service availability"""
    
    provider_name = serializers.CharField(source='provider.business_name', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    is_past = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceAvailability
        fields = [
            'id', 'date', 'start_time', 'end_time', 'is_available',
            'is_blocked', 'block_reason', 'special_rate',
            'provider_name', 'service_title', 'is_past'
        ]
    
    def get_is_past(self, obj):
        from django.utils import timezone
        return obj.date < timezone.now().date()


class ServiceBookingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for booking listings"""
    
    service_title = serializers.CharField(source='service.title', read_only=True)
    provider_name = serializers.CharField(source='provider.business_name', read_only=True)
    
    class Meta:
        model = ServiceBooking
        fields = [
            'id', 'booking_reference', 'service_title', 'provider_name',
            'customer_name', 'scheduled_date', 'scheduled_start_time',
            'status', 'total_amount', 'currency', 'booking_date'
        ]


class ServiceBookingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for service bookings"""
    
    service = ServiceListSerializer(read_only=True)
    provider = ServiceProviderListSerializer(read_only=True)
    
    class Meta:
        model = ServiceBooking
        fields = [
            'id', 'booking_reference', 'service', 'provider',
            'customer_user_id', 'customer_name', 'customer_email', 'customer_phone',
            'service_address', 'service_city', 'service_instructions',
            'scheduled_date', 'scheduled_start_time', 'scheduled_end_time',
            'estimated_duration', 'actual_start_time', 'actual_end_time',
            'quoted_price', 'final_price', 'travel_charge', 'material_cost',
            'taxes', 'total_amount', 'currency', 'status', 'payment_id',
            'payment_status', 'service_description', 'special_requirements',
            'materials_needed', 'customer_notes', 'provider_notes',
            'booking_date', 'confirmation_date', 'completion_date',
            'cancellation_date'
        ]


class ServiceBookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating service bookings"""
    
    class Meta:
        model = ServiceBooking
        fields = [
            'service', 'customer_name', 'customer_email', 'customer_phone',
            'service_address', 'service_city', 'service_instructions',
            'scheduled_date', 'scheduled_start_time', 'scheduled_end_time',
            'service_description', 'special_requirements', 'customer_notes'
        ]
    
    def validate(self, data):
        """Validate booking data"""
        from django.utils import timezone
        
        # Check if scheduled date is in the future
        if data['scheduled_date'] < timezone.now().date():
            raise serializers.ValidationError("Cannot book services for past dates")
        
        # Check if start time is before end time
        if data['scheduled_start_time'] >= data['scheduled_end_time']:
            raise serializers.ValidationError("Start time must be before end time")
        
        # Check provider availability
        service = data['service']
        availability = service.availability.filter(
            date=data['scheduled_date'],
            start_time__lte=data['scheduled_start_time'],
            end_time__gte=data['scheduled_end_time'],
            is_available=True,
            is_blocked=False
        )
        
        if not availability.exists():
            raise serializers.ValidationError("Service is not available at the requested time")
        
        return data
    
    def create(self, validated_data):
        """Create booking with calculated pricing"""
        service = validated_data['service']
        
        # Calculate pricing based on service pricing type
        if service.pricing_type == 'hourly':
            duration_hours = (
                validated_data['scheduled_end_time'].hour - 
                validated_data['scheduled_start_time'].hour
            )
            quoted_price = service.hourly_rate * duration_hours
        elif service.pricing_type == 'fixed':
            quoted_price = service.fixed_price
        else:
            quoted_price = service.minimum_charge or Decimal('0.00')
        
        validated_data.update({
            'provider': service.provider,
            'quoted_price': quoted_price,
            'travel_charge': service.travel_charge,
            'total_amount': quoted_price + service.travel_charge,
            'currency': service.provider.currency,
            'profile_id': self.context['request'].user.profile_id,
            'customer_user_id': str(self.context['request'].user.id),
        })
        
        return super().create(validated_data)


class ServiceReviewSerializer(serializers.ModelSerializer):
    """Serializer for service reviews"""
    
    service_title = serializers.CharField(source='service.title', read_only=True)
    provider_name = serializers.CharField(source='provider.business_name', read_only=True)
    overall_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceReview
        fields = [
            'id', 'service_title', 'provider_name', 'reviewer_name',
            'rating', 'title', 'comment', 'quality_rating', 'timeliness_rating',
            'communication_rating', 'value_rating', 'professionalism_rating',
            'would_recommend', 'would_book_again', 'is_verified',
            'response', 'response_date', 'overall_rating', 'created_at'
        ]
    
    def get_overall_rating(self, obj):
        """Calculate overall rating from individual ratings"""
        ratings = [
            obj.quality_rating, obj.timeliness_rating, obj.communication_rating,
            obj.value_rating, obj.professionalism_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else obj.rating


class ServiceReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating service reviews"""
    
    class Meta:
        model = ServiceReview
        fields = [
            'booking', 'rating', 'title', 'comment', 'quality_rating',
            'timeliness_rating', 'communication_rating', 'value_rating',
            'professionalism_rating', 'would_recommend', 'would_book_again'
        ]
    
    def validate_booking(self, value):
        """Validate that booking belongs to the user and is completed"""
        request = self.context['request']
        
        if value.customer_user_id != str(request.user.id):
            raise serializers.ValidationError("You can only review your own bookings")
        
        if value.status != 'completed':
            raise serializers.ValidationError("You can only review completed bookings")
        
        if hasattr(value, 'review'):
            raise serializers.ValidationError("This booking has already been reviewed")
        
        return value
    
    def create(self, validated_data):
        """Create review with auto-populated fields"""
        booking = validated_data['booking']
        
        validated_data.update({
            'service': booking.service,
            'provider': booking.provider,
            'reviewer_user_id': str(self.context['request'].user.id),
            'reviewer_name': booking.customer_name,
            'profile_id': self.context['request'].user.profile_id,
        })
        
        return super().create(validated_data)


# Nested serializers for complex operations
class ServiceWithImagesSerializer(ServiceDetailSerializer):
    """Service serializer with image upload support"""
    
    images = ServiceImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    
    class Meta(ServiceDetailSerializer.Meta):
        fields = ServiceDetailSerializer.Meta.fields + ['uploaded_images']
    
    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        service = super().create(validated_data)
        
        for i, image in enumerate(uploaded_images):
            ServiceImage.objects.create(
                service=service,
                image=image,
                is_primary=(i == 0),
                order=i,
                profile_id=service.profile_id
            )
        
        return service


class ProviderWithServicesSerializer(ServiceProviderDetailSerializer):
    """Provider serializer with nested services"""
    
    services = ServiceListSerializer(many=True, read_only=True)
    
    class Meta(ServiceProviderDetailSerializer.Meta):
        fields = ServiceProviderDetailSerializer.Meta.fields + ['services']
