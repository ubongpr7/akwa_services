"""
Services Microservice Models
Handles professional services (cleaning, repair, tutoring, legal) and personal services (beauty, spa, pet care)
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Address(models.Model):

    
    country = models.CharField(
        max_length=255,
        verbose_name=_('Country'),
        help_text=_('Country of the address'),
        null=True,
        blank=True
    )
    region = models.CharField(
        max_length=255,
        verbose_name=_('Region/State'),
        help_text=_('Region or state within the country'),
        null=True,
        blank=True
    )
    subregion = models.CharField(
        max_length=255,
        verbose_name=_('Subregion/Province'),
        help_text=_('Subregion or province within the region'),
        null=True,
        blank=True
    )
    city = models.CharField(
        max_length=255,
        verbose_name=_('City'),
        help_text=_('City of the address'),
        null=True,
        blank=True
    )
    apt_number = models.PositiveIntegerField(
        verbose_name=_('Apartment number'),
        null=True,
        blank=True
    )
    street_number = models.PositiveIntegerField(
        verbose_name=_('Street number'),
        null=True,
        blank=True
    )
    street = models.CharField(max_length=255,blank=False,null=True)

    postal_code = models.CharField(
        max_length=10,
        verbose_name=_('Postal code'),
        help_text=_('Postal code'),
        blank=True,
        null=True,
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Latitude'),
        help_text=_('Geographical latitude of the address'),
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Longitude'),
        help_text=_('Geographical longitude of the address'),
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.street}, {self.city}, {self.region}, {self.country}'

class ServicesManager(models.Manager):
    """Custom manager for services-related models"""
    
    def for_profile(self, profile_id):
        return self.get_queryset().filter(profile_id=profile_id)
    
    def active(self):
        return self.get_queryset().filter(is_active=True)
    
    def by_category(self, category):
        return self.get_queryset().filter(category__slug=category)
    
    def available_for_date(self, date):
        return self.get_queryset().filter(
            availability__date=date,
            availability__is_available=True,
            is_active=True
        ).distinct()


class ProfileMixin(models.Model):
    """Abstract model providing multi-tenant functionality"""
    
    profile_id = models.CharField(
        max_length=50,
        help_text="Reference to CompanyProfile ID from users service"
    )
    created_by_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Reference to User ID from users service"
    )
    modified_by_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Reference to User ID from users service"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ServicesManager()
    
    class Meta:
        abstract = True


class ServiceType(models.TextChoices):
    # Professional Services
    CLEANING = 'cleaning', _('Cleaning')
    REPAIR = 'repair', _('Repair & Maintenance')
    TUTORING = 'tutoring', _('Tutoring')
    LEGAL = 'legal', _('Legal Services')
    FINANCIAL = 'financial', _('Financial Services')
    CONSULTING = 'consulting', _('Consulting')
    PLUMBING = 'plumbing', _('Plumbing')
    ELECTRICAL = 'electrical', _('Electrical')
    CARPENTRY = 'carpentry', _('Carpentry')
    PAINTING = 'painting', _('Painting')
    MOVING = 'moving', _('Moving Services')
    LANDSCAPING = 'landscaping', _('Landscaping')
    
    # Personal Services
    BEAUTY = 'beauty', _('Beauty Services')
    SPA = 'spa', _('Spa & Wellness')
    PET_CARE = 'pet_care', _('Pet Care')
    MASSAGE = 'massage', _('Massage Therapy')
    HAIR_SALON = 'hair_salon', _('Hair Salon')
    NAIL_SALON = 'nail_salon', _('Nail Salon')
    FITNESS = 'fitness', _('Personal Training')
    PHOTOGRAPHY = 'photography', _('Photography')
    CATERING = 'catering', _('Personal Catering')


class ServiceCategory(models.Model):
    """Categories for organizing services"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    is_professional = models.BooleanField(
        default=True,
        help_text="True for professional services, False for personal services"
    )
    
    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ServiceProvider(ProfileMixin):
    """Service providers (professionals, businesses)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Location and Service Area
    address = models.ForeignKey(Address, on_delete= models.SET_NULL, null=True, blank=True)
   
    service_radius = models.PositiveIntegerField(
        default=10,
        help_text="Service radius in kilometers"
    )
    
    # Business Details
    license_number = models.CharField(max_length=100, blank=True)
    insurance_policy = models.CharField(max_length=100, blank=True)
    years_in_business = models.PositiveIntegerField(default=0)
    employee_count = models.PositiveIntegerField(default=1)
    
    # Specializations
    specializations = models.ManyToManyField(
        ServiceCategory,
        related_name='providers',
        blank=True
    )
    
    # Ratings and Reviews
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    total_jobs_completed = models.PositiveIntegerField(default=0)
    
    # Availability
    is_available = models.BooleanField(default=True)
    response_time = models.DurationField(
        null=True,
        blank=True,
        help_text="Average response time to inquiries"
    )
    
    # Pricing
    hourly_rate_min = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    hourly_rate_max = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(max_length=3, null=True,blank=False)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    background_checked = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile_id', 'is_active']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['average_rating']),
        ]
    
    def __str__(self):
        return f"{self.business_name} - {self.city}"


class Service(ProfileMixin):
    """Individual services offered by providers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='services'
    )

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='services'
    )
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices
    )
    
    # Pricing Options
    pricing_type = models.CharField(
        max_length=20,
        choices=[
            ('hourly', _('Hourly Rate')),
            ('fixed', _('Fixed Price')),
            ('quote', _('Custom Quote')),
            ('package', _('Package Deal')),
        ],
        default='hourly'
    )
    
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    fixed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    minimum_charge = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Service Details
    estimated_duration = models.DurationField(null=True, blank=True)
    materials_included = models.BooleanField(default=False)
    travel_charge = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Requirements and Preparation
    customer_requirements = models.TextField(
        blank=True,
        help_text="What the customer needs to prepare"
    )
    tools_equipment = models.TextField(
        blank=True,
        help_text="Tools/equipment the provider brings"
    )
    
    # Availability
    available_days = models.JSONField(
        default=list,
        help_text="List of available days (0=Monday, 6=Sunday)"
    )
    available_hours_start = models.TimeField(default='09:00')
    available_hours_end = models.TimeField(default='17:00')
    advance_booking_required = models.DurationField(
        null=True,
        blank=True,
        help_text="Minimum advance booking time required"
    )
    
    # Ratings
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    requires_consultation = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['provider', 'slug']
        indexes = [
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['category', 'service_type']),
            models.Index(fields=['pricing_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.provider.business_name}"


class ServiceImage(ProfileMixin):
    """Images for services"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image = models.ImageField(upload_to='services/%Y/%m/%d/')
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_at']


class ServiceAvailability(ProfileMixin):
    """Service provider availability calendar"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='availability'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='availability'
    )
    
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.CharField(max_length=255, blank=True)
    
    # Special pricing for this time slot
    special_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ['provider', 'date', 'start_time']
        indexes = [
            models.Index(fields=['provider', 'date']),
            models.Index(fields=['date', 'is_available']),
        ]


class BookingStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    CONFIRMED = 'confirmed', _('Confirmed')
    IN_PROGRESS = 'in_progress', _('In Progress')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')
    NO_SHOW = 'no_show', _('No Show')
    RESCHEDULED = 'rescheduled', _('Rescheduled')


class ServiceBooking(ProfileMixin):
    """Service booking records"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=20, unique=True)
    
    # Service details
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    
    # Customer information (references to users service)
    customer_user_id = models.CharField(
        max_length=50,
        help_text="Reference to User ID from users service"
    )
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # Service Location
    service_address = models.TextField()
    service_city = models.CharField(max_length=100)
    service_instructions = models.TextField(
        blank=True,
        help_text="Special instructions for finding the location"
    )
    
    # Booking Schedule
    scheduled_date = models.DateField()
    scheduled_start_time = models.TimeField()
    scheduled_end_time = models.TimeField()
    estimated_duration = models.DurationField()
    
    # Actual Service Times
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Pricing
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    travel_charge = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00')
    )
    material_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )
    taxes = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    
    # Payment information (references to payment service)
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reference to payment record in payment service"
    )
    payment_status = models.CharField(max_length=20, default='pending')
    
    # Service Details
    service_description = models.TextField(
        blank=True,
        help_text="Detailed description of work to be done"
    )
    special_requirements = models.TextField(blank=True)
    materials_needed = models.TextField(blank=True)
    
    # Notes and Communication
    customer_notes = models.TextField(blank=True)
    provider_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    booking_date = models.DateTimeField(default=timezone.now)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['profile_id', 'status']),
            models.Index(fields=['customer_user_id']),
            models.Index(fields=['provider', 'scheduled_date']),
            models.Index(fields=['booking_reference']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.service.title}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        
        # Calculate total amount
        self.total_amount = (
            (self.final_price or self.quoted_price) +
            self.travel_charge +
            self.material_cost +
            self.taxes
        )
        
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        
        prefix = "SRV"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}{suffix}"


class ServiceReview(ProfileMixin):
    """Reviews and ratings for services"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    booking = models.OneToOneField(
        ServiceBooking,
        on_delete=models.CASCADE,
        related_name='review'
    )
    
    # Reviewer information (references to users service)
    reviewer_user_id = models.CharField(
        max_length=50,
        help_text="Reference to User ID from users service"
    )
    reviewer_name = models.CharField(max_length=255)
    
    # Review content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    
    # Detailed ratings
    quality_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    timeliness_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    communication_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    professionalism_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Recommendation
    would_recommend = models.BooleanField(null=True, blank=True)
    would_book_again = models.BooleanField(null=True, blank=True)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Response from provider
    response = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service', 'is_published']),
            models.Index(fields=['provider', 'is_published']),
            models.Index(fields=['reviewer_user_id']),
        ]
    
    def __str__(self):
        return f"Review for {self.service.title} by {self.reviewer_name}"


class ServiceCertification(ProfileMixin):
    """Certifications and qualifications for service providers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='certifications'
    )
    
    name = models.CharField(max_length=255)
    issuing_organization = models.CharField(max_length=255)
    certification_number = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Reference to User ID who verified"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Document
    certificate_document = models.FileField(
        upload_to='certifications/%Y/%m/%d/',
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.provider.business_name} - {self.name}"
