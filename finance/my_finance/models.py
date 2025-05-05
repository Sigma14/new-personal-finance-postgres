# from django.db import models
from ast import mod
import datetime
from ast import mod
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
# from djongo import models
from django.db import models
from django.utils.timezone import now
import bleach

ALLOWED_TAGS = []  # No HTML allowed
ALLOWED_ATTRIBUTES = {}

from .constants import (
    BUDGET_ACCOUNT_TYPES,
    BUDGET_PERIODS,
    CURRENCIES,
    INTEREST_PERIODS,
    MAINTENANCE_CATEGORY,
    MAINTENANCE_STATUS,
    MORTGAGE_TYPES,
    PROPERTY_TYPE,
)

# Create your models here.

# Define allowed tags and attributes (none in this case)
ALLOWED_TAGS = []  # No HTML allowed
ALLOWED_ATTRIBUTES = {}

class UserBudgets(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Sanitize the name field to prevent unwanted HTML."""
        if self.name:
            # Clean the name field using bleach, then strip tags
            cleaned_name = bleach.clean(self.name, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
            self.name = cleaned_name.strip()

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure validation and sanitization
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)

@receiver(post_save, sender=User)
def add_user_budget(sender, instance, created, **kwargs):
    if created:
        UserBudgets.objects.create(name="Default Budget", user=instance)


# class Property(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="property_user"
#     )
#     property_name = models.CharField(max_length=255, blank=True, null=True)
#     property_image = models.ImageField(upload_to="property_pics", blank=True, null=True)
#     property_type = models.CharField(
#         max_length=10, choices=PROPERTY_TYPE, blank=True, null=True
#     )
#     address_line1 = models.CharField(max_length=255, blank=True, null=True)
#     address_line2 = models.CharField(max_length=255, blank=True, null=True)
#     post_code = models.CharField(max_length=255, blank=True, null=True)
#     city = models.CharField(max_length=255, blank=True, null=True)
#     state = models.CharField(max_length=255, blank=True, null=True)
#     country = models.CharField(max_length=255, blank=True, null=True)
#     unit_details = models.CharField(max_length=500, blank=True, null=True)
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     value = models.CharField(max_length=255, blank=True, null=True)
#     include_net_worth = models.BooleanField(default=False)
#     units_no = models.CharField(max_length=255, blank=True, null=True)
#     total_monthly_rent = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     total_tenants = models.CharField(max_length=255, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.property_name)

class Property(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_user"
    )
    property_name = models.CharField(max_length=255, blank=True, null=True)
    property_image = models.ImageField(upload_to="property_pics", blank=True, null=True)
    property_type = models.CharField(
        max_length=10, choices=PROPERTY_TYPE, blank=True, null=True
    )
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    post_code = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    unit_details = models.CharField(max_length=500, blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    value = models.CharField(max_length=255, blank=True, null=True)
    include_net_worth = models.BooleanField(default=False)
    units_no = models.CharField(max_length=255, blank=True, null=True)
    total_monthly_rent = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_tenants = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.property_name)

    def clean(self):
        # Clean any potentially unsafe HTML input in fields
        # Sanitize the 'unit_details' field (or other fields that require sanitization)
        if self.unit_details:
            self.unit_details = bleach.clean(self.unit_details)

        if self.address_line1:
            self.address_line1 = bleach.clean(self.address_line1)

        if self.address_line2:
            self.address_line2 = bleach.clean(self.address_line2)

        if self.city:
            self.city = bleach.clean(self.city)

        if self.state:
            self.state = bleach.clean(self.state)

        if self.country:
            self.country = bleach.clean(self.country)

        # Add other fields you want to sanitize in the same way
        return super(Property, self).clean()

    def save(self, *args, **kwargs):
        # Optionally, you can also clean data before saving
        if self.unit_details:
            self.unit_details = bleach.clean(self.unit_details)

        if self.address_line1:
            self.address_line1 = bleach.clean(self.address_line1)

        if self.address_line2:
            self.address_line2 = bleach.clean(self.address_line2)

        if self.city:
            self.city = bleach.clean(self.city)

        if self.state:
            self.state = bleach.clean(self.state)

        if self.country:
            self.country = bleach.clean(self.country)

        # Save the model
        super(Property, self).save(*args, **kwargs)


# class PropertyRentalInfo(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="property_rental_user"
#     )
#     property_address = models.ForeignKey(
#         Property, on_delete=models.CASCADE, related_name="property_address"
#     )
#     unit_name = models.CharField(max_length=255, blank=True, null=True)
#     rental_term = models.CharField(max_length=255, blank=True, null=True)
#     rental_start_date = models.DateField(blank=True, null=True)
#     rental_end_date = models.DateField(blank=True, null=True)
#     deposit_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     deposit_due_date = models.DateField(blank=True, null=True)
#     deposit_check = models.CharField(max_length=255, blank=True, null=True)
#     rent_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     rent_due_every_month = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     rent_due_date = models.DateField(blank=True, null=True)
#     rental_summary = models.CharField(max_length=500, blank=True, null=True)
#     first_name = models.CharField(max_length=255, blank=True, null=True)
#     last_name = models.CharField(max_length=255, blank=True, null=True)
#     email = models.CharField(max_length=255, blank=True, null=True)
#     mobile_number = models.CharField(max_length=255, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

    

#     def __str__(self):
#         return str(
#             self.first_name
#             + " "
#             + self.property_address.property_name
#             + " "
#             + self.unit_name
#         )
class PropertyRentalInfo(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_rental_user"
    )
    property_address = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_address"
    )
    unit_name = models.CharField(max_length=255, blank=True, null=True)
    rental_term = models.CharField(max_length=255, blank=True, null=True)
    rental_start_date = models.DateField(blank=True, null=True)
    rental_end_date = models.DateField(blank=True, null=True)
    deposit_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    deposit_due_date = models.DateField(blank=True, null=True)
    deposit_check = models.CharField(max_length=255, blank=True, null=True)
    rent_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rent_due_every_month = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rent_due_date = models.DateField(blank=True, null=True)
    rental_summary = models.CharField(max_length=500, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    mobile_number = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize text fields before saving
        text_fields = ["unit_name", "rental_term", "deposit_check", "rental_summary", 
                       "first_name", "last_name", "email", "mobile_number"]

        for field in text_fields:
            value = getattr(self, field, None)
            if value:
                setattr(self, field, bleach.clean(value))

        super().save(*args, **kwargs)

    def __str__(self):
        return str(
            (self.first_name or "") 
            + " " 
            + (self.property_address.property_name if self.property_address else "") 
            + " " 
            + (self.unit_name or "")
        )

# class PropertyInvoice(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="property_invoice_user"
#     )
#     property_details = models.ForeignKey(
#         Property, on_delete=models.CASCADE, related_name="property_details"
#     )
#     tenant_name = models.CharField(max_length=255, blank=True, null=True)
#     unit_name = models.CharField(max_length=255, blank=True, null=True)
#     item_type = models.CharField(max_length=255, blank=True, null=True)
#     item_description = models.CharField(max_length=255, blank=True, null=True)
#     quantity = models.CharField(max_length=255, blank=True, null=True)
#     item_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     already_paid = models.CharField(max_length=255, blank=True, null=True)
#     balance_due = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     invoice_due_date = models.DateField(blank=True, null=True)
#     invoice_paid_date = models.DateField(blank=True, null=True)
#     invoice_status = models.CharField(max_length=255, blank=True, null=True)
#     record_payment = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(
#             self.tenant_name
#             + " "
#             + self.property_details.property_name
#             + " "
#             + self.unit_name
#             + str(self.id)
#         )

class PropertyInvoice(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_invoice_user"
    )
    property_details = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_details"
    )
    tenant_name = models.CharField(max_length=255, blank=True, null=True)
    unit_name = models.CharField(max_length=255, blank=True, null=True)
    item_type = models.CharField(max_length=255, blank=True, null=True)
    item_description = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.CharField(max_length=255, blank=True, null=True)
    item_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    already_paid = models.CharField(max_length=255, blank=True, null=True)
    balance_due = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    invoice_due_date = models.DateField(blank=True, null=True)
    invoice_paid_date = models.DateField(blank=True, null=True)
    invoice_status = models.CharField(max_length=255, blank=True, null=True)
    record_payment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize text fields before saving
        text_fields = [
            "tenant_name", "unit_name", "item_type", "item_description",
            "quantity", "already_paid", "invoice_status", "record_payment"
        ]

        for field in text_fields:
            value = getattr(self, field, None)
            if value:
                setattr(self, field, bleach.clean(value))

        super().save(*args, **kwargs)

    def __str__(self):
        return str(
            (self.tenant_name or "") + " " +
            (self.property_details.property_name if self.property_details else "") + " " +
            (self.unit_name or "") + " #" + str(self.id)
        )


# class PropertyMaintenance(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="property_maintenance_user"
#     )
#     property_details = models.ForeignKey(
#         Property, on_delete=models.CASCADE, related_name="property_maintenance_details"
#     )
#     unit_name = models.CharField(max_length=255, blank=True, null=True)
#     tenant_name = models.CharField(max_length=255, blank=True, null=True)
#     category = models.CharField(
#         max_length=10, choices=MAINTENANCE_CATEGORY, blank=True, null=True
#     )
#     name = models.CharField(max_length=255, blank=True, null=True)
#     description = models.TextField(blank=True, null=True)
#     status = models.CharField(
#         max_length=10, choices=MAINTENANCE_STATUS, blank=True, null=True
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(
#             self.name + " " + self.property_details.property_name + " " + self.unit_name
#         )

#     def get_absolute_url(self):
#         return reverse("property_maintenance_list")

class PropertyMaintenance(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_maintenance_user"
    )
    property_details = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_maintenance_details"
    )
    unit_name = models.CharField(max_length=255, blank=True, null=True)
    tenant_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(
        max_length=10, choices=MAINTENANCE_CATEGORY, blank=True, null=True
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=MAINTENANCE_STATUS, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize text fields before saving
        text_fields = ["unit_name", "tenant_name", "name", "description"]

        for field in text_fields:
            value = getattr(self, field, None)
            if value:
                setattr(self, field, bleach.clean(value))

        super().save(*args, **kwargs)

    def __str__(self):
        return str(
            (self.name or "") + " " +
            (self.property_details.property_name if self.property_details else "") + " " +
            (self.unit_name or "")
        )

    def get_absolute_url(self):
        return reverse("property_maintenance_list")



# class PropertyExpense(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="property_expense_user"
#     )
#     property_details = models.ForeignKey(
#         Property, on_delete=models.CASCADE, related_name="property_info"
#     )
#     payee_name = models.CharField(max_length=255, blank=True, null=True)
#     expense_date = models.DateField(blank=True, null=True)
#     unit_name = models.CharField(max_length=255, blank=True, null=True)
#     category = models.CharField(max_length=255, blank=True, null=True)
#     description = models.CharField(max_length=255, blank=True, null=True)
#     # amount = models.DecimalField(max_length=255, blank=True, null=True)
#     amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(
#             self.payee_name
#             + " "
#             + self.property_details.property_name
#             + " "
#             + self.unit_name
#             + str(self.id)
#         )

#     def get_absolute_url(self):
#         return reverse("property_expense_list")

class PropertyExpense(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_expense_user"
    )
    property_details = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_info"
    )
    payee_name = models.CharField(max_length=255, blank=True, null=True)
    expense_date = models.DateField(blank=True, null=True)
    unit_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize text fields before saving
        text_fields = ["payee_name", "unit_name", "category", "description"]

        for field in text_fields:
            value = getattr(self, field, None)
            if value:
                setattr(self, field, bleach.clean(value))

        super().save(*args, **kwargs)

    def __str__(self):
        return str(
            (self.payee_name or "") + " " +
            (self.property_details.property_name if self.property_details else "") + " " +
            (self.unit_name or "") + " #" + str(self.id)
        )

    def get_absolute_url(self):
        return reverse("property_expense_list")


# class Category(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     name = models.CharField(max_length=50)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.name)

#     def get_absolute_url(self):
#         return reverse("category_list")

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize the name field before saving
        if self.name:
            self.name = bleach.clean(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("category_list")

# class SubCategory(models.Model):
#     category = models.ForeignKey(Category, on_delete=models.CASCADE)
#     name = models.CharField(max_length=50)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{str(self.category.name)}: {str(self.name)}"

#     def get_absolute_url(self):
#         return reverse("category_list")

class SubCategory(models.Model):
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize the name field before saving
        if self.name:
            self.name = bleach.clean(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{str(self.category.name)}: {str(self.name)}"

    def get_absolute_url(self):
        return reverse("category_list")



# class SuggestiveCategory(models.Model):
#     name = models.CharField(max_length=50)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.name)

class SuggestiveCategory(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize the name field before saving
        if self.name:
            self.name = bleach.clean(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)
    

# class TemplateBudget(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     start_date = models.DateField(blank=True, null=True)
#     end_date = models.DateField(blank=True, null=True)
#     name = models.CharField(max_length=255, blank=True, null=True)
#     category = models.ForeignKey(
#         SubCategory, on_delete=models.CASCADE, null=True, blank=True
#     )
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     initial_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     budget_spent = models.CharField(max_length=15, default=0, blank=True, null=True)
#     budget_left = models.CharField(max_length=15, default=0, blank=True, null=True)
#     auto_budget = models.BooleanField(default=True)
#     auto_pay = models.BooleanField(default=True)
#     budget_period = models.CharField(
#         max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
#     )
#     budget_status = models.BooleanField(default=False)
#     budget_start_date = models.DateField(blank=True, null=True)
#     created_at = models.DateField(blank=True, null=True)
#     ended_at = models.DateField(blank=True, null=True)

#     def __str__(self):
#         return f"{self.name}{self.id}{self.currency}"

#     def get_absolute_url(self):
#         return reverse("template_budget_list")

class TemplateBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(
        "SubCategory", on_delete=models.CASCADE, null=True, blank=True
    )
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    initial_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    budget_spent = models.CharField(max_length=15, default=0, blank=True, null=True)
    budget_left = models.CharField(max_length=15, default=0, blank=True, null=True)
    auto_budget = models.BooleanField(default=True)
    auto_pay = models.BooleanField(default=True)
    budget_period = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    budget_status = models.BooleanField(default=False)
    budget_start_date = models.DateField(blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    ended_at = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Sanitize fields before saving
        if self.name:
            self.name = bleach.clean(self.name)
        if self.currency:
            self.currency = bleach.clean(self.currency)
        if self.budget_period:
            self.budget_period = bleach.clean(self.budget_period)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}{self.id}{self.currency}"

    def get_absolute_url(self):
        return reverse("template_budget_list")


# class PlaidItem(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     access_token = models.CharField(max_length=255)
#     item_id = models.CharField(max_length=255)

class PlaidItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    item_id = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # Sanitize fields before saving
        if self.access_token:
            self.access_token = bleach.clean(self.access_token)
        if self.item_id:
            self.item_id = bleach.clean(self.item_id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PlaidItem {self.item_id}"
    

# class Account(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="account_user"
#     )
#     name = models.CharField(max_length=50, null=True)
#     account_type = models.CharField(
#         max_length=50, choices=BUDGET_ACCOUNT_TYPES, blank=True, null=True
#     )
#     balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     available_balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     lock_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     interest_rate = models.FloatField(verbose_name="Interest rate", default=0.00)
#     include_net_worth = models.BooleanField(default=True)
#     liability_type = models.CharField(
#         max_length=10, choices=MORTGAGE_TYPES, blank=True, null=True
#     )
#     interest_period = models.CharField(
#         max_length=10, choices=INTEREST_PERIODS, blank=True, null=True
#     )
#     mortgage_date = models.DateField(blank=True, null=True)
#     mortgage_monthly_payment = models.CharField(max_length=10, blank=True, null=True)
#     mortgage_year = models.CharField(max_length=10, blank=True, null=True)
#     transaction_count = models.IntegerField(default=0, blank=True, null=True)
#     plaid_account_id = models.CharField(max_length=200, blank=True, null=True)
#     mask = models.CharField(max_length=200, blank=True, null=True)
#     subtype = models.CharField(max_length=200, blank=True, null=True)
#     item = models.ForeignKey(PlaidItem, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.name + "(" + self.currency + ")")

#     def get_absolute_url(self):
#         return reverse("account_box")

class Account(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="account_user"
    )
    name = models.CharField(max_length=50, null=True)
    account_type = models.CharField(
        max_length=50, choices=BUDGET_ACCOUNT_TYPES, blank=True, null=True
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    lock_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    interest_rate = models.FloatField(verbose_name="Interest rate", default=0.00)
    include_net_worth = models.BooleanField(default=True)
    liability_type = models.CharField(
        max_length=10, choices=MORTGAGE_TYPES, blank=True, null=True
    )
    interest_period = models.CharField(
        max_length=10, choices=INTEREST_PERIODS, blank=True, null=True
    )
    mortgage_date = models.DateField(blank=True, null=True)
    mortgage_monthly_payment = models.CharField(max_length=10, blank=True, null=True)
    mortgage_year = models.CharField(max_length=10, blank=True, null=True)
    transaction_count = models.IntegerField(default=0, blank=True, null=True)
    plaid_account_id = models.CharField(max_length=200, blank=True, null=True)
    mask = models.CharField(max_length=200, blank=True, null=True)
    subtype = models.CharField(max_length=200, blank=True, null=True)
    item = models.ForeignKey(PlaidItem, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize fields before saving
        self.name = bleach.clean(self.name) if self.name else None
        self.account_type = bleach.clean(self.account_type) if self.account_type else None
        self.currency = bleach.clean(self.currency) if self.currency else None
        self.liability_type = bleach.clean(self.liability_type) if self.liability_type else None
        self.interest_period = bleach.clean(self.interest_period) if self.interest_period else None
        self.mortgage_monthly_payment = bleach.clean(self.mortgage_monthly_payment) if self.mortgage_monthly_payment else None
        self.mortgage_year = bleach.clean(self.mortgage_year) if self.mortgage_year else None
        self.plaid_account_id = bleach.clean(self.plaid_account_id) if self.plaid_account_id else None
        self.mask = bleach.clean(self.mask) if self.mask else None
        self.subtype = bleach.clean(self.subtype) if self.subtype else None

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name + "(" + self.currency + ")") if self.name and self.currency else "Account"

    def get_absolute_url(self):
        return reverse("account_box")

# class BillDetail(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
#     user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
#     label = models.CharField(max_length=50)
#     account = models.ForeignKey(
#         Account,
#         on_delete=models.CASCADE,
#         related_name="bill_details_account",
#         blank=True,
#         null=True,
#     )
#     amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     date = models.DateField()
#     frequency = models.CharField(
#         max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
#     )
#     auto_bill = models.BooleanField(default=False)
#     auto_pay = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.label + self.user.username)

class BillDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
    label = models.CharField(max_length=50)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="bill_details_account",
        blank=True,
        null=True,
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    date = models.DateField()
    frequency = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    auto_bill = models.BooleanField(default=False)
    auto_pay = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize input fields before saving
        self.label = bleach.clean(self.label) if self.label else None
        self.frequency = bleach.clean(self.frequency) if self.frequency else None
        
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.label + " - " + self.user.username) if self.user else self.label


# class Bill(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
#     label = models.CharField(max_length=50)
#     account = models.ForeignKey(
#         Account,
#         on_delete=models.CASCADE,
#         related_name="bill_account",
#         blank=True,
#         null=True,
#     )
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     date = models.DateField()
#     bill_details = models.ForeignKey(
#         BillDetail,
#         on_delete=models.CASCADE,
#         related_name="bill_details",
#         blank=True,
#         null=True,
#     )
#     status = models.CharField(max_length=50, default="unpaid", blank=True, null=True)
#     frequency = models.CharField(
#         max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
#     )
#     auto_bill = models.BooleanField(default=False)
#     auto_pay = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.label + "(" + self.currency + ")")

#     def get_absolute_url(self):
#         return reverse("bill_list")

class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
    label = models.CharField(max_length=50)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="bill_account",
        blank=True,
        null=True,
    )
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    date = models.DateField()
    bill_details = models.ForeignKey(
        BillDetail,
        on_delete=models.CASCADE,
        related_name="bill_details",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=50, default="unpaid", blank=True, null=True)
    frequency = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    auto_bill = models.BooleanField(default=False)
    auto_pay = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize the input fields before saving
        self.label = bleach.clean(self.label) if self.label else None
        self.status = bleach.clean(self.status) if self.status else None
        self.frequency = bleach.clean(self.frequency) if self.frequency else None
        
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.label + " (" + self.currency + ")")

    def get_absolute_url(self):
        return reverse("bill_list")


# class Budget(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
#     start_date = models.DateField(blank=True, null=True)
#     end_date = models.DateField(blank=True, null=True)
#     name = models.CharField(max_length=255, blank=True, null=True)
#     category = models.ForeignKey(
#         SubCategory, on_delete=models.CASCADE, null=True, blank=True
#     )
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     account = models.ForeignKey(
#         Account,
#         on_delete=models.CASCADE,
#         related_name="budget_account",
#         blank=True,
#         null=True,
#     )
#     initial_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     budget_spent = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     budget_left = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     auto_budget = models.BooleanField(default=True)
#     auto_pay = models.BooleanField(default=True)
#     budget_period = models.CharField(
#         max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
#     )
#     budget_status = models.BooleanField(default=False)
#     budget_start_date = models.DateField(blank=True, null=True)
#     created_at = models.DateField(blank=True, null=True)
#     ended_at = models.DateField(blank=True, null=True)

#     def __str__(self):
#         return f"{self.name}{self.id}{self.currency}"

#     def get_absolute_url(self):
#         return reverse("current-budgets")

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="budget_account",
        blank=True,
        null=True,
    )
    initial_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    budget_spent = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    budget_left = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    auto_budget = models.BooleanField(default=True)
    auto_pay = models.BooleanField(default=True)
    budget_period = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    budget_status = models.BooleanField(default=False)
    budget_start_date = models.DateField(blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    ended_at = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Sanitize the input fields before saving
        self.name = bleach.clean(self.name) if self.name else None
        self.currency = bleach.clean(self.currency) if self.currency else None
        self.budget_period = bleach.clean(self.budget_period) if self.budget_period else None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}{self.id}{self.currency}"

    def get_absolute_url(self):
        return reverse("current-budgets")


# class AvailableFunds(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fund_user")
#     account = models.ForeignKey(
#         Account, on_delete=models.CASCADE, related_name="fund_account"
#     )
#     total_fund = models.CharField(max_length=20)
#     lock_fund = models.CharField(max_length=20)
#     created_at = models.DateField(auto_now=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.account)

class AvailableFunds(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fund_user")
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="fund_account"
    )
    total_fund = models.CharField(max_length=20)
    lock_fund = models.CharField(max_length=20)
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize the input fields before saving
        self.total_fund = bleach.clean(self.total_fund) if self.total_fund else None
        self.lock_fund = bleach.clean(self.lock_fund) if self.lock_fund else None

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.account)


# class Goal(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goal_user")
#     user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)
#     goal_date = models.DateField(blank=True, null=True)
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     label = models.ForeignKey(
#         SubCategory, on_delete=models.CASCADE, null=True, blank=True
#     )
#     goal_amount = models.FloatField()
#     allocate_amount = models.FloatField()
#     fund_amount = models.FloatField(default=0)
#     budget_amount = models.FloatField(default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.label)

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goal_user")
    user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    goal_date = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    label = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    goal_amount = models.FloatField()
    allocate_amount = models.FloatField()
    fund_amount = models.FloatField(default=0)
    budget_amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize the label field (if applicable) before saving
        self.label = bleach.clean(str(self.label)) if self.label else None

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.label)


# class PropertyPurchaseDetails(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="property_purchase_user"
#     )
#     best_case_price = models.CharField(max_length=30)
#     likely_case_price = models.CharField(max_length=30)
#     worst_case_price = models.CharField(max_length=30)
#     selected_case = models.CharField(max_length=30)
#     selected_price = models.CharField(max_length=30, blank=True, null=True)
#     down_payment = models.CharField(max_length=30)

class PropertyPurchaseDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_purchase_user"
    )
    best_case_price = models.CharField(max_length=30)
    likely_case_price = models.CharField(max_length=30)
    worst_case_price = models.CharField(max_length=30)
    selected_case = models.CharField(max_length=30)
    selected_price = models.CharField(max_length=30, blank=True, null=True)
    down_payment = models.CharField(max_length=30)

    def save(self, *args, **kwargs):
        # Sanitize the fields before saving
        self.best_case_price = bleach.clean(self.best_case_price)
        self.likely_case_price = bleach.clean(self.likely_case_price)
        self.worst_case_price = bleach.clean(self.worst_case_price)
        self.selected_case = bleach.clean(self.selected_case)
        self.selected_price = bleach.clean(self.selected_price) if self.selected_price else None
        self.down_payment = bleach.clean(self.down_payment)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Property Purchase: {self.selected_case} - {self.selected_price}"


# class MortgageDetails(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="mortgage_user"
#     )
#     start_date = models.DateField(blank=True, null=True)
#     interest_rate = models.CharField(max_length=30)
#     amortization_year = models.CharField(max_length=30)

class MortgageDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="mortgage_user"
    )
    start_date = models.DateField(blank=True, null=True)
    interest_rate = models.CharField(max_length=30)
    amortization_year = models.CharField(max_length=30)

    def save(self, *args, **kwargs):
        # Sanitize the fields before saving
        self.interest_rate = bleach.clean(self.interest_rate)
        self.amortization_year = bleach.clean(self.amortization_year)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mortgage: {self.interest_rate} - {self.amortization_year}"


# class ClosingCostDetails(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="closing_cost_user"
#     )
#     transfer_tax = models.CharField(max_length=30)
#     legal_fee = models.CharField(max_length=30)
#     title_insurance = models.CharField(max_length=30)
#     inspection = models.CharField(max_length=30)
#     appraisal_fee = models.CharField(max_length=30)
#     appliances = models.CharField(max_length=30)
#     renovation_cost = models.CharField(max_length=30)
#     others_cost = models.CharField(max_length=500)
#     total_investment = models.CharField(max_length=30, blank=True, null=True)

class ClosingCostDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="closing_cost_user"
    )
    transfer_tax = models.CharField(max_length=30)
    legal_fee = models.CharField(max_length=30)
    title_insurance = models.CharField(max_length=30)
    inspection = models.CharField(max_length=30)
    appraisal_fee = models.CharField(max_length=30)
    appliances = models.CharField(max_length=30)
    renovation_cost = models.CharField(max_length=30)
    others_cost = models.CharField(max_length=500)
    total_investment = models.CharField(max_length=30, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Sanitize the fields before saving
        self.transfer_tax = bleach.clean(self.transfer_tax)
        self.legal_fee = bleach.clean(self.legal_fee)
        self.title_insurance = bleach.clean(self.title_insurance)
        self.inspection = bleach.clean(self.inspection)
        self.appraisal_fee = bleach.clean(self.appraisal_fee)
        self.appliances = bleach.clean(self.appliances)
        self.renovation_cost = bleach.clean(self.renovation_cost)
        self.others_cost = bleach.clean(self.others_cost)
        self.total_investment = bleach.clean(self.total_investment)

        super().save(*args, **kwargs)

# class RevenuesDetails(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rev_user")
#     unit_1 = models.CharField(max_length=30)
#     others_revenue_cost = models.CharField(max_length=500)
#     total_revenue = models.CharField(max_length=30)
#     rent_increase_assumption = models.CharField(max_length=30)


class RevenuesDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rev_user")
    unit_1 = models.CharField(max_length=30)
    others_revenue_cost = models.CharField(max_length=500)
    total_revenue = models.CharField(max_length=30)
    rent_increase_assumption = models.CharField(max_length=30)

    def save(self, *args, **kwargs):
        # Sanitize the fields before saving
        self.unit_1 = bleach.clean(self.unit_1)
        self.others_revenue_cost = bleach.clean(self.others_revenue_cost)
        self.total_revenue = bleach.clean(self.total_revenue)
        self.rent_increase_assumption = bleach.clean(self.rent_increase_assumption)

        super().save(*args, **kwargs)

# class ExpensesDetails(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="expense_user"
#     )
#     property_tax = models.CharField(max_length=30)
#     insurance = models.CharField(max_length=30)
#     maintenance = models.CharField(max_length=30)
#     water = models.CharField(max_length=30)
#     gas = models.CharField(max_length=30)
#     electricity = models.CharField(max_length=30)
#     water_heater_rental = models.CharField(max_length=30)
#     other_utilities = models.CharField(max_length=500)
#     management_fee = models.CharField(max_length=30)
#     vacancy = models.CharField(max_length=30)
#     capital_expenditure = models.CharField(max_length=30)
#     other_expenses = models.CharField(max_length=500)
#     total_expenses = models.CharField(max_length=30)
#     inflation_assumption = models.CharField(max_length=30)
#     appreciation_assumption = models.CharField(max_length=30)

class ExpensesDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="expense_user"
    )
    property_tax = models.CharField(max_length=30)
    insurance = models.CharField(max_length=30)
    maintenance = models.CharField(max_length=30)
    water = models.CharField(max_length=30)
    gas = models.CharField(max_length=30)
    electricity = models.CharField(max_length=30)
    water_heater_rental = models.CharField(max_length=30)
    other_utilities = models.CharField(max_length=500)
    management_fee = models.CharField(max_length=30)
    vacancy = models.CharField(max_length=30)
    capital_expenditure = models.CharField(max_length=30)
    other_expenses = models.CharField(max_length=500)
    total_expenses = models.CharField(max_length=30)
    inflation_assumption = models.CharField(max_length=30)
    appreciation_assumption = models.CharField(max_length=30)

    def save(self, *args, **kwargs):
        # Sanitize the fields before saving
        self.property_tax = bleach.clean(self.property_tax)
        self.insurance = bleach.clean(self.insurance)
        self.maintenance = bleach.clean(self.maintenance)
        self.water = bleach.clean(self.water)
        self.gas = bleach.clean(self.gas)
        self.electricity = bleach.clean(self.electricity)
        self.water_heater_rental = bleach.clean(self.water_heater_rental)
        self.other_utilities = bleach.clean(self.other_utilities)
        self.management_fee = bleach.clean(self.management_fee)
        self.vacancy = bleach.clean(self.vacancy)
        self.capital_expenditure = bleach.clean(self.capital_expenditure)
        self.other_expenses = bleach.clean(self.other_expenses)
        self.total_expenses = bleach.clean(self.total_expenses)
        self.inflation_assumption = bleach.clean(self.inflation_assumption)
        self.appreciation_assumption = bleach.clean(self.appreciation_assumption)

        super().save(*args, **kwargs)


# class CapexBudgetDetails(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="capex_budget_user"
#     )
#     roof = models.CharField(max_length=500, blank=True, null=True)
#     water_heater = models.CharField(max_length=500, blank=True, null=True)
#     all_appliances = models.CharField(max_length=500, blank=True, null=True)
#     bathroom_fixtures = models.CharField(max_length=500, blank=True, null=True)
#     drive_way = models.CharField(max_length=500, blank=True, null=True)
#     furnance = models.CharField(max_length=500, blank=True, null=True)
#     air_conditioner = models.CharField(max_length=500, blank=True, null=True)
#     flooring = models.CharField(max_length=500, blank=True, null=True)
#     plumbing = models.CharField(max_length=500, blank=True, null=True)
#     electrical = models.CharField(max_length=500, blank=True, null=True)
#     windows = models.CharField(max_length=500, blank=True, null=True)
#     paint = models.CharField(max_length=500, blank=True, null=True)
#     kitchen = models.CharField(max_length=500, blank=True, null=True)
#     structure = models.CharField(max_length=500, blank=True, null=True)
#     components = models.CharField(max_length=500, blank=True, null=True)
#     landscaping = models.CharField(max_length=500, blank=True, null=True)
#     other_budgets = models.CharField(
#         max_length=500, blank=True, null=True
#     )
#     total_budget_cost = models.CharField(max_length=30, blank=True, null=True)


class CapexBudgetDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="capex_budget_user"
    )
    roof = models.CharField(max_length=500, blank=True, null=True)
    water_heater = models.CharField(max_length=500, blank=True, null=True)
    all_appliances = models.CharField(max_length=500, blank=True, null=True)
    bathroom_fixtures = models.CharField(max_length=500, blank=True, null=True)
    drive_way = models.CharField(max_length=500, blank=True, null=True)
    furnance = models.CharField(max_length=500, blank=True, null=True)
    air_conditioner = models.CharField(max_length=500, blank=True, null=True)
    flooring = models.CharField(max_length=500, blank=True, null=True)
    plumbing = models.CharField(max_length=500, blank=True, null=True)
    electrical = models.CharField(max_length=500, blank=True, null=True)
    windows = models.CharField(max_length=500, blank=True, null=True)
    paint = models.CharField(max_length=500, blank=True, null=True)
    kitchen = models.CharField(max_length=500, blank=True, null=True)
    structure = models.CharField(max_length=500, blank=True, null=True)
    components = models.CharField(max_length=500, blank=True, null=True)
    landscaping = models.CharField(max_length=500, blank=True, null=True)
    other_budgets = models.CharField(
        max_length=500, blank=True, null=True
    )
    total_budget_cost = models.CharField(max_length=30, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Sanitize the fields before saving
        self.roof = bleach.clean(self.roof)
        self.water_heater = bleach.clean(self.water_heater)
        self.all_appliances = bleach.clean(self.all_appliances)
        self.bathroom_fixtures = bleach.clean(self.bathroom_fixtures)
        self.drive_way = bleach.clean(self.drive_way)
        self.furnance = bleach.clean(self.furnance)
        self.air_conditioner = bleach.clean(self.air_conditioner)
        self.flooring = bleach.clean(self.flooring)
        self.plumbing = bleach.clean(self.plumbing)
        self.electrical = bleach.clean(self.electrical)
        self.windows = bleach.clean(self.windows)
        self.paint = bleach.clean(self.paint)
        self.kitchen = bleach.clean(self.kitchen)
        self.structure = bleach.clean(self.structure)
        self.components = bleach.clean(self.components)
        self.landscaping = bleach.clean(self.landscaping)
        self.other_budgets = bleach.clean(self.other_budgets)
        self.total_budget_cost = bleach.clean(self.total_budget_cost)

        super().save(*args, **kwargs)


# class RentalPropertyModel(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="property_rental"
#     )
#     property_image = models.ImageField(upload_to="property_pics", blank=True, null=True)
#     name = models.CharField(max_length=30)
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     purchase_price_detail = models.ForeignKey(
#         PropertyPurchaseDetails,
#         on_delete=models.CASCADE,
#         related_name="property_purchase_user",
#     )
#     mortgage_detail = models.ForeignKey(
#         MortgageDetails, on_delete=models.CASCADE, related_name="mortgage_user"
#     )
#     closing_cost_detail = models.ForeignKey(
#         ClosingCostDetails, on_delete=models.CASCADE, related_name="closing_cost_user"
#     )
#     monthly_revenue = models.ForeignKey(
#         RevenuesDetails, on_delete=models.CASCADE, related_name="rev_user"
#     )
#     monthly_expenses = models.ForeignKey(
#         ExpensesDetails, on_delete=models.CASCADE, related_name="expense_user"
#     )
#     capex_budget_details = models.ForeignKey(
#         CapexBudgetDetails, on_delete=models.CASCADE, related_name="capex_budget"
#     )
#     investor_details = models.CharField(max_length=500, blank=True, null=True)
#     include_net_worth = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.name)


class RentalPropertyModel(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="rental_property_user"
    )
    property_image = models.ImageField(upload_to="property_pics", blank=True, null=True)
    name = models.CharField(max_length=30)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    purchase_price_detail = models.ForeignKey(
        PropertyPurchaseDetails,
        on_delete=models.CASCADE,
        related_name="property_purchase_user",
    )
    mortgage_detail = models.ForeignKey(
        MortgageDetails, on_delete=models.CASCADE, related_name="mortgage_user"
    )
    closing_cost_detail = models.ForeignKey(
        ClosingCostDetails, on_delete=models.CASCADE, related_name="closing_cost_user"
    )
    monthly_revenue = models.ForeignKey(
        RevenuesDetails, on_delete=models.CASCADE, related_name="rev_user"
    )
    monthly_expenses = models.ForeignKey(
        ExpensesDetails, on_delete=models.CASCADE, related_name="expense_user"
    )
    capex_budget_details = models.ForeignKey(
        CapexBudgetDetails, on_delete=models.CASCADE, related_name="capex_budget"
    )
    investor_details = models.CharField(max_length=500, blank=True, null=True)
    include_net_worth = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        if self.name:
            self.name = bleach.clean(self.name)
        if self.currency:
            self.currency = bleach.clean(self.currency)
        if self.investor_details:
            self.investor_details = bleach.clean(self.investor_details)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)


# class Tag(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tag_user")
#     name = models.CharField(max_length=30)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return str(self.name)

class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tag_user")
    name = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        # Sanitize the name field before saving
        self.name = bleach.clean(self.name)

        super().save(*args, **kwargs)


# class Transaction(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="transaction_user"
#     )
#     amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     transaction_date = models.DateField(blank=True, null=True)
#     categories = models.ForeignKey(
#         SubCategory, on_delete=models.CASCADE, null=True, blank=True
#     )
#     split_transactions = models.CharField(max_length=255, blank=True, null=True)
#     original_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     budgets = models.ForeignKey(Budget, on_delete=models.CASCADE)
#     payee = models.CharField(max_length=25)
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)
#     bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
#     tags = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True, blank=True)
#     notes = models.CharField(max_length=255, blank=True, null=True)
#     in_flow = models.BooleanField(default=False)
#     out_flow = models.BooleanField(default=True)
#     plaid_account_id = models.CharField(max_length=255, blank=True, null=True)
#     plaid_transaction_id = models.CharField(max_length=255, blank=True, null=True)
#     cleared = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return str(self.payee)

#     def get_absolute_url(self):
#         return reverse("transaction_list")


class Transaction(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transaction_user"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    transaction_date = models.DateField(blank=True, null=True)
    categories = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    split_transactions = models.CharField(max_length=255, blank=True, null=True)
    original_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    budgets = models.ForeignKey(Budget, on_delete=models.CASCADE)
    payee = models.CharField(max_length=25)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    tags = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, null=True)
    in_flow = models.BooleanField(default=False)
    out_flow = models.BooleanField(default=True)
    plaid_account_id = models.CharField(max_length=255, blank=True, null=True)
    plaid_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    cleared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.payee)

    def get_absolute_url(self):
        return reverse("transaction_list")

    def save(self, *args, **kwargs):
        # Sanitize fields that may contain user input
        if self.split_transactions:
            self.split_transactions = bleach.clean(self.split_transactions)
        if self.notes:
            self.notes = bleach.clean(self.notes)
        if self.payee:
            self.payee = bleach.clean(self.payee)

        # Save the instance after sanitizing
        super().save(*args, **kwargs)


# class MortgageCalculator(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="mortgagecalculator_user"
#     )
#     label = models.CharField(max_length=30)
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     amount = models.IntegerField(default=0)
#     years = models.CharField(max_length=10)
#     interest = models.CharField(max_length=10)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.label)

#     def get_absolute_url(self):
#         return reverse("mortgagecalculator_list")


class MortgageCalculator(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="mortgagecalculator_user"
    )
    label = models.CharField(max_length=30)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    amount = models.IntegerField(default=0)
    years = models.CharField(max_length=10)
    interest = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        if self.label:
            self.label = bleach.clean(self.label)
        if self.currency:
            self.currency = bleach.clean(self.currency)
        if self.years:
            self.years = bleach.clean(self.years)
        if self.interest:
            self.interest = bleach.clean(self.interest)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.label)

    def get_absolute_url(self):
        return reverse("mortgagecalculator_list")


# class Income(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     sub_category = models.ForeignKey(
#         SubCategory, on_delete=models.CASCADE, null=True, blank=True
#     )
#     account = models.ForeignKey(
#         Account,
#         on_delete=models.CASCADE,
#         related_name="income_account",
#         blank=True,
#         null=True,
#     )
#     income_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     income_date = models.DateField()
#     auto_income = models.BooleanField(default=False)
#     frequency = models.CharField(
#         max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
#     )
#     auto_credit = models.BooleanField(default=False)
#     primary = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{str(self.sub_category.name)}"

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="income_account",
        blank=True,
        null=True,
    )
    income_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    income_date = models.DateField()
    auto_income = models.BooleanField(default=False)
    frequency = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    auto_credit = models.BooleanField(default=False)
    primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        if self.frequency:
            self.frequency = bleach.clean(self.frequency)

        # If you want to sanitize sub-category names or any other related text fields
        if self.sub_category and self.sub_category.name:
            self.sub_category.name = bleach.clean(self.sub_category.name)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{str(self.sub_category.name)}"


# class IncomeDetail(models.Model):
#     account = models.ForeignKey(
#         Account,
#         on_delete=models.CASCADE,
#         related_name="income_detail_account",
#         blank=True,
#         null=True,
#     )
#     income_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     income_date = models.DateField(blank=True, null=True)
#     income = models.ForeignKey(Income, on_delete=models.CASCADE)
#     credited = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{str(self.income.sub_category.name)}"

class IncomeDetail(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="income_detail_account",
        blank=True,
        null=True,
    )
    income_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    income_date = models.DateField(blank=True, null=True)
    income = models.ForeignKey(Income, on_delete=models.CASCADE)
    credited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        # Sanitize the income sub_category name if it's available
        if self.income and self.income.sub_category and self.income.sub_category.name:
            self.income.sub_category.name = bleach.clean(self.income.sub_category.name)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        # Ensure the sub_category name is sanitized before returning
        return f"{bleach.clean(str(self.income.sub_category.name))}"


# class Revenues(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="revenue_user"
#     )
#     name = models.CharField(max_length=255)
#     month = models.DateField(blank=True, null=True)
#     end_month = models.DateField(blank=True, null=True)
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     primary = models.BooleanField(default=False)
#     non_primary = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.month)


class Revenues(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="revenue_user"
    )
    name = models.CharField(max_length=255)
    month = models.DateField(blank=True, null=True)
    end_month = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    primary = models.BooleanField(default=False)
    non_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        # Sanitize the name field before saving
        self.name = bleach.clean(self.name)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        # Return sanitized string representation
        return str(self.month)


# class Expenses(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="expenses_user"
#     )
#     categories = models.ForeignKey(Category, on_delete=models.CASCADE)
#     name = models.CharField(max_length=255)
#     month = models.DateField(blank=True, null=True)
#     currency = models.CharField(
#         max_length=10, choices=CURRENCIES, blank=True, null=True
#     )
#     amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.month)


class Expenses(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="expenses_user"
    )
    categories = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    month = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        # Sanitize the name field before saving
        self.name = bleach.clean(self.name)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        # Return sanitized string representation
        return str(self.month)


# class StockHoldings(models.Model):
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="stockholdings_user"
#     )
#     port_id = models.CharField(max_length=255, unique=True)
#     name = models.CharField(max_length=255)
#     currency = models.CharField(max_length=10, blank=True, null=True)
#     value = models.CharField(max_length=255)
#     end_at = models.DateTimeField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.name)


class StockHoldings(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="stockholdings_user"
    )
    port_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=10, blank=True, null=True)
    value = models.CharField(max_length=255)
    end_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        # Sanitize the name field before saving
        self.name = bleach.clean(self.name)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        # Return sanitized string representation
        return str(self.name)


# class MyNotes(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     notes = models.TextField()
#     added_on = models.DateField(default=datetime.date.today)

#     def __str__(self):
#         return str(self.title + " " + self.user.username)


class MyNotes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    notes = models.TextField()
    added_on = models.DateField(default=datetime.date.today)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        # Sanitize the notes field before saving
        self.notes = bleach.clean(self.notes)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title + " " + self.user.username)



# Chat Model for chatting with chatgpt
class AIChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="aichat_user")
    message = models.TextField()
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.message}"

    class Meta:
        ordering = ["-created_at"]


# Feedback model

class Feedback(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="feedback_user"
    )
    feature = models.CharField(max_length=255)
    issue = models.CharField(max_length=255)
    screenshot = models.ImageField(
        upload_to="feedback_screenshots/", null=True, blank=True
    )
    description = models.TextField()
    suggestion = models.TextField()
    importance = models.CharField(max_length=255)
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_fields(self, *args, **kwargs):
        """
        Sanitize text-based fields using bleach before saving the model.
        """
        # Sanitize the description and suggestion fields before saving
        self.description = bleach.clean(self.description)
        self.suggestion = bleach.clean(self.suggestion)

        super().clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.issue}"

    class Meta:
        ordering = ["-created_at"]


class AppErrorLog(models.Model):
    class StatusChoices(models.TextChoices):
        RESOLVED = "resolved", "Resolved"
        OPEN = "open", "Open"
        SKIP = "skip", "Skip"
    users = models.ManyToManyField(User, blank=True, related_name="error_logs")
    timestamp = models.DateTimeField(default=now, db_index=True)
    exception_type = models.CharField(max_length=255, db_index=True)
    error_message = models.TextField()
    traceback = models.TextField()
    request_path = models.CharField(max_length=255, blank=True, null=True)
    count = models.PositiveIntegerField(default=1)
    code = models.IntegerField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
        db_index=True,
    )

    class Meta:
        verbose_name = "Error Log"
        verbose_name_plural = "Error Logs"
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"[{self.count}] {self.exception_type} ({self.code}): {self.error_message[:50]}"