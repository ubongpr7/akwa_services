"""
Services Microservice Views
Comprehensive viewsets for all services-related models
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Prefetch
from django.utils import timezone
from datetime import timedelta

from .models import (
    ServiceCategory, ServiceProvider, Service, ServiceImage,
    ServiceAvailability, ServiceBooking, ServiceReview, ServiceCertification
)
from .serializers import (
    ServiceCategorySerializer, ServiceProviderListSerializer, ServiceProviderDetailSerializer,
    ServiceListSerializer, ServiceDetailSerializer, ServiceWithImagesSerializer,
    ServiceAvailabilitySerializer, ServiceBookingListSerializer, ServiceBookingDetailSerializer,
    ServiceBookingCreateSerializer, ServiceReviewSerializer, ServiceReviewCreateSerializer,
    ServiceCertificationSerializer, ProviderWithServicesSerializer
)
from .filters import (
    ServiceCategoryFilter, ServiceProviderFilter, ServiceFilter,
    ServiceBookingFilter, ServiceReviewFilter, ServiceAvailabilityFilter
)


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for service categories
    Provides list and detail views for service categories
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    filterset_class = ServiceCategoryFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'id']
    ordering = ['name']
    lookup_field = 'slug'
    
    def get_queryset(self):
        return ServiceCategory.objects.prefetch_related(
            'subcategories',
            'services',
            'providers'
        )
    
    @action(detail=True, methods=['get'])
    def services(self, request, slug=None):
        """Get all services in this category"""
        category = self.get_object()
        services = Service.objects.filter(
            category=category,
            is_active=True
        ).select_related('provider', 'category').prefetch_related('images')
        
        # Apply service filters
        service_filter = ServiceFilter(request.GET, queryset=services)
        services = service_filter.qs
        
        page = self.paginate_queryset(services)
        if page is not None:
            serializer = ServiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def providers(self, request, slug=None):
        """Get all providers in this category"""
        category = self.get_object()
        providers = ServiceProvider.objects.filter(
            specializations=category,
            is_active=True
        ).prefetch_related('specializations', 'certifications')
        
        # Apply provider filters
        provider_filter = ServiceProviderFilter(request.GET, queryset=providers)
        providers = provider_filter.qs
        
        page = self.paginate_queryset(providers)
        if page is not None:
            serializer = ServiceProviderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceProviderListSerializer(providers, many=True)
        return Response(serializer.data)


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service providers
    Provides CRUD operations for service providers
    """
    queryset = ServiceProvider.objects.all()
    filterset_class = ServiceProviderFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['business_name', 'description', 'city', 'specializations__name']
    ordering_fields = [
        'business_name', 'average_rating', 'total_reviews', 'total_jobs_completed',
        'hourly_rate_min', 'years_in_business', 'created_at'
    ]
    ordering = ['-is_featured', '-average_rating', '-total_reviews']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceProviderListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ServiceProviderDetailSerializer
        elif self.action == 'with_services':
            return ProviderWithServicesSerializer
        return ServiceProviderDetailSerializer
    
    def get_queryset(self):
        queryset = ServiceProvider.objects.select_related().prefetch_related(
            'specializations',
            'certifications',
            'services__category',
            'services__images',
            'reviews'
        )
        
        # Filter by profile for authenticated users
        if self.request.user.is_authenticated:
            if self.action in ['create', 'update', 'partial_update', 'destroy']:
                queryset = queryset.filter(profile_id=self.request.user.profile_id)
            elif self.request.GET.get('my_providers'):
                queryset = queryset.filter(profile_id=self.request.user.profile_id)
        
        return queryset.filter(is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(
            profile_id=self.request.user.profile_id,
            created_by_id=str(self.request.user.id)
        )
    
    def perform_update(self, serializer):
        serializer.save(modified_by_id=str(self.request.user.id))
    
    @action(detail=True, methods=['get'])
    def services(self, request, slug=None):
        """Get all services offered by this provider"""
        provider = self.get_object()
        services = provider.services.filter(is_active=True).select_related(
            'category'
        ).prefetch_related('images')
        
        # Apply service filters
        service_filter = ServiceFilter(request.GET, queryset=services)
        services = service_filter.qs
        
        page = self.paginate_queryset(services)
        if page is not None:
            serializer = ServiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def availability(self, request, slug=None):
        """Get provider availability"""
        provider = self.get_object()
        
        # Get date range from query params
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if not date_from:
            date_from = timezone.now().date()
        if not date_to:
            date_to = date_from + timedelta(days=30)
        
        availability = provider.availability.filter(
            date__range=[date_from, date_to]
        ).order_by('date', 'start_time')
        
        serializer = ServiceAvailabilitySerializer(availability, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """Get provider reviews"""
        provider = self.get_object()
        reviews = provider.reviews.filter(is_published=True).select_related(
            'service'
        ).order_by('-created_at')
        
        # Apply review filters
        review_filter = ServiceReviewFilter(request.GET, queryset=reviews)
        reviews = review_filter.qs
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ServiceReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        """Get provider statistics"""
        provider = self.get_object()
        
        # Calculate various statistics
        total_bookings = provider.bookings.count()
        completed_bookings = provider.bookings.filter(status='completed').count()
        
        # Rating breakdown
        reviews = provider.reviews.filter(is_published=True)
        rating_breakdown = {
            '5_star': reviews.filter(rating=5).count(),
            '4_star': reviews.filter(rating=4).count(),
            '3_star': reviews.filter(rating=3).count(),
            '2_star': reviews.filter(rating=2).count(),
            '1_star': reviews.filter(rating=1).count(),
        }
        
        # Monthly booking trends (last 12 months)
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        
        monthly_bookings = provider.bookings.filter(
            booking_date__gte=timezone.now() - timedelta(days=365)
        ).annotate(
            month=TruncMonth('booking_date')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        stats = {
            'total_bookings': total_bookings,
            'completed_bookings': completed_bookings,
            'completion_rate': (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0,
            'rating_breakdown': rating_breakdown,
            'monthly_bookings': list(monthly_bookings),
            'services_count': provider.services.filter(is_active=True).count(),
            'certifications_count': provider.certifications.filter(is_verified=True).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured providers"""
        providers = self.get_queryset().filter(is_featured=True)[:10]
        serializer = self.get_serializer(providers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top-rated providers"""
        providers = self.get_queryset().filter(
            total_reviews__gte=5
        ).order_by('-average_rating', '-total_reviews')[:10]
        
        serializer = self.get_serializer(providers, many=True)
        return Response(serializer.data)


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for services
    Provides CRUD operations for services
    """
    queryset = Service.objects.all()
    filterset_class = ServiceFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'provider__business_name', 'category__name']
    ordering_fields = [
        'title', 'average_rating', 'total_reviews', 'hourly_rate',
        'fixed_price', 'created_at'
    ]
    ordering = ['-is_featured', '-average_rating', '-total_reviews']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ServiceWithImagesSerializer
        return ServiceDetailSerializer
    
    def get_queryset(self):
        queryset = Service.objects.select_related(
            'provider',
            'category'
        ).prefetch_related(
            'images',
            'reviews',
            'availability'
        )
        
        # Filter by profile for authenticated users
        if self.request.user.is_authenticated:
            if self.action in ['create', 'update', 'partial_update', 'destroy']:
                queryset = queryset.filter(profile_id=self.request.user.profile_id)
            elif self.request.GET.get('my_services'):
                queryset = queryset.filter(profile_id=self.request.user.profile_id)
        
        return queryset.filter(is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(
            profile_id=self.request.user.profile_id,
            created_by_id=str(self.request.user.id)
        )
    
    def perform_update(self, serializer):
        serializer.save(modified_by_id=str(self.request.user.id))
    
    @action(detail=True, methods=['get'])
    def availability(self, request, slug=None):
        """Get service availability"""
        service = self.get_object()
        
        # Get date range from query params
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if not date_from:
            date_from = timezone.now().date()
        if not date_to:
            date_to = date_from + timedelta(days=30)
        
        availability = service.availability.filter(
            date__range=[date_from, date_to],
            is_available=True,
            is_blocked=False
        ).order_by('date', 'start_time')
        
        serializer = ServiceAvailabilitySerializer(availability, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """Get service reviews"""
        service = self.get_object()
        reviews = service.reviews.filter(is_published=True).order_by('-created_at')
        
        # Apply review filters
        review_filter = ServiceReviewFilter(request.GET, queryset=reviews)
        reviews = review_filter.qs
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ServiceReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, slug=None):
        """Get similar services"""
        service = self.get_object()
        
        similar_services = Service.objects.filter(
            category=service.category,
            is_active=True
        ).exclude(id=service.id).select_related(
            'provider', 'category'
        ).prefetch_related('images')[:8]
        
        serializer = ServiceListSerializer(similar_services, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def book(self, request, slug=None):
        """Create a booking for this service"""
        service = self.get_object()
        
        # Add service to request data
        data = request.data.copy()
        data['service'] = service.id
        
        serializer = ServiceBookingCreateSerializer(
            data=data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            booking = serializer.save()
            response_serializer = ServiceBookingDetailSerializer(booking)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured services"""
        services = self.get_queryset().filter(is_featured=True)[:10]
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular services based on bookings"""
        services = self.get_queryset().annotate(
            booking_count=Count('bookings')
        ).order_by('-booking_count', '-average_rating')[:10]
        
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories_summary(self, request):
        """Get services grouped by categories"""
        from django.db.models import Count
        
        categories = ServiceCategory.objects.annotate(
            services_count=Count('services', filter=Q(services__is_active=True))
        ).filter(services_count__gt=0).order_by('-services_count')
        
        result = []
        for category in categories:
            services = category.services.filter(is_active=True)[:4]
            result.append({
                'category': ServiceCategorySerializer(category).data,
                'services': ServiceListSerializer(services, many=True).data,
                'total_services': category.services_count
            })
        
        return Response(result)


class ServiceBookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service bookings
    Provides CRUD operations for service bookings
    """
    queryset = ServiceBooking.objects.all()
    filterset_class = ServiceBookingFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['booking_reference', 'customer_name', 'service__title', 'provider__business_name']
    ordering_fields = ['booking_date', 'scheduled_date', 'total_amount', 'status']
    ordering = ['-booking_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceBookingListSerializer
        elif self.action == 'create':
            return ServiceBookingCreateSerializer
        return ServiceBookingDetailSerializer
    
    def get_queryset(self):
        queryset = ServiceBooking.objects.select_related(
            'service',
            'provider'
        ).prefetch_related(
            'service__images',
            'service__category'
        )
        
        # Filter by profile for authenticated users
        if self.request.user.is_authenticated:
            # Users can see their own bookings or bookings for their services
            user_id = str(self.request.user.id)
            profile_id = self.request.user.profile_id
            
            queryset = queryset.filter(
                Q(customer_user_id=user_id) |  # Customer's bookings
                Q(profile_id=profile_id)       # Provider's bookings
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(
            profile_id=self.request.user.profile_id,
            created_by_id=str(self.request.user.id)
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response(
                {'error': 'Only pending bookings can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'confirmed'
        booking.confirmation_date = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel completed or already cancelled bookings'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.cancellation_date = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start_service(self, request, pk=None):
        """Mark service as started"""
        booking = self.get_object()
        
        if booking.status != 'confirmed':
            return Response(
                {'error': 'Only confirmed bookings can be started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'in_progress'
        booking.actual_start_time = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete_service(self, request, pk=None):
        """Mark service as completed"""
        booking = self.get_object()
        
        if booking.status != 'in_progress':
            return Response(
                {'error': 'Only in-progress bookings can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update final price if provided
        final_price = request.data.get('final_price')
        if final_price:
            booking.final_price = final_price
            booking.total_amount = (
                final_price + booking.travel_charge + 
                booking.material_cost + booking.taxes
            )
        
        booking.status = 'completed'
        booking.actual_end_time = timezone.now()
        booking.completion_date = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Get current user's bookings"""
        user_id = str(request.user.id)
        bookings = self.get_queryset().filter(customer_user_id=user_id)
        
        # Apply filters
        filterset = self.filterset_class(request.GET, queryset=bookings)
        bookings = filterset.qs
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def provider_bookings(self, request):
        """Get bookings for current user's services"""
        profile_id = request.user.profile_id
        bookings = self.get_queryset().filter(profile_id=profile_id)
        
        # Apply filters
        filterset = self.filterset_class(request.GET, queryset=bookings)
        bookings = filterset.qs
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)


class ServiceReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service reviews
    Provides CRUD operations for service reviews
    """
    queryset = ServiceReview.objects.all()
    filterset_class = ServiceReviewFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'comment', 'reviewer_name', 'service__title', 'provider__business_name']
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ServiceReviewCreateSerializer
        return ServiceReviewSerializer
    
    def get_queryset(self):
        queryset = ServiceReview.objects.select_related(
            'service',
            'provider',
            'booking'
        ).filter(is_published=True)
        
        # Filter by profile for authenticated users
        if self.request.user.is_authenticated:
            user_id = str(self.request.user.id)
            profile_id = self.request.user.profile_id
            
            # Users can see all published reviews, but only edit their own
            if self.action in ['update', 'partial_update', 'destroy']:
                queryset = queryset.filter(reviewer_user_id=user_id)
            elif self.request.GET.get('my_reviews'):
                queryset = queryset.filter(reviewer_user_id=user_id)
            elif self.request.GET.get('provider_reviews'):
                queryset = queryset.filter(provider__profile_id=profile_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(
            profile_id=self.request.user.profile_id,
            created_by_id=str(self.request.user.id)
        )
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Provider response to review"""
        review = self.get_object()
        
        # Check if user is the provider
        if review.provider.profile_id != request.user.profile_id:
            return Response(
                {'error': 'Only the service provider can respond to this review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response_text = request.data.get('response')
        if not response_text:
            return Response(
                {'error': 'Response text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review.response = response_text
        review.response_date = timezone.now()
        review.save()
        
        serializer = self.get_serializer(review)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's reviews"""
        user_id = str(request.user.id)
        reviews = self.get_queryset().filter(reviewer_user_id=user_id)
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class ServiceAvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service availability
    Provides CRUD operations for service availability
    """
    queryset = ServiceAvailability.objects.all()
    filterset_class = ServiceAvailabilityFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['date', 'start_time']
    ordering = ['date', 'start_time']
    serializer_class = ServiceAvailabilitySerializer
    
    def get_queryset(self):
        queryset = ServiceAvailability.objects.select_related(
            'provider',
            'service'
        )
        
        # Filter by profile for authenticated users
        if self.request.user.is_authenticated:
            profile_id = self.request.user.profile_id
            queryset = queryset.filter(profile_id=profile_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(
            profile_id=self.request.user.profile_id,
            created_by_id=str(self.request.user.id)
        )
    
    def perform_update(self, serializer):
        serializer.save(modified_by_id=str(self.request.user.id))
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple availability slots"""
        data_list = request.data if isinstance(request.data, list) else [request.data]
        
        created_slots = []
        errors = []
        
        for i, data in enumerate(data_list):
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                slot = serializer.save(
                    profile_id=request.user.profile_id,
                    created_by_id=str(request.user.id)
                )
                created_slots.append(serializer.data)
            else:
                errors.append({
                    'index': i,
                    'errors': serializer.errors
                })
        
        if errors:
            return Response({
                'created': created_slots,
                'errors': errors
            }, status=status.HTTP_207_MULTI_STATUS)
        
        return Response(created_slots, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Update multiple availability slots"""
        updates = request.data.get('updates', [])
        
        updated_slots = []
        errors = []
        
        for update in updates:
            slot_id = update.get('id')
            if not slot_id:
                errors.append({'error': 'ID is required for updates'})
                continue
            
            try:
                slot = self.get_queryset().get(id=slot_id)
                serializer = self.get_serializer(slot, data=update, partial=True)
                if serializer.is_valid():
                    serializer.save(modified_by_id=str(request.user.id))
                    updated_slots.append(serializer.data)
                else:
                    errors.append({
                        'id': slot_id,
                        'errors': serializer.errors
                    })
            except ServiceAvailability.DoesNotExist:
                errors.append({
                    'id': slot_id,
                    'error': 'Availability slot not found'
                })
        
        return Response({
            'updated': updated_slots,
            'errors': errors
        })


class ServiceCertificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service provider certifications
    Provides CRUD operations for certifications
    """
    queryset = ServiceCertification.objects.all()
    serializer_class = ServiceCertificationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'issuing_organization', 'provider__business_name']
    ordering_fields = ['issue_date', 'expiry_date', 'name']
    ordering = ['-issue_date']
    
    def get_queryset(self):
        queryset = ServiceCertification.objects.select_related('provider')
        
        # Filter by profile for authenticated users
        if self.request.user.is_authenticated:
            profile_id = self.request.user.profile_id
            queryset = queryset.filter(profile_id=profile_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(
            profile_id=self.request.user.profile_id,
            created_by_id=str(self.request.user.id)
        )
    
    def perform_update(self, serializer):
        serializer.save(modified_by_id=str(self.request.user.id))
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a certification (admin only)"""
        certification = self.get_object()
        
        # This would typically require admin permissions
        # For now, allow the provider to self-verify
        certification.is_verified = True
        certification.verified_by_id = str(request.user.id)
        certification.verified_at = timezone.now()
        certification.save()
        
        serializer = self.get_serializer(certification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get certifications expiring in the next 30 days"""
        from datetime import timedelta
        
        expiry_threshold = timezone.now().date() + timedelta(days=30)
        certifications = self.get_queryset().filter(
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=timezone.now().date()
        )
        
        serializer = self.get_serializer(certifications, many=True)
        return Response(serializer.data)
