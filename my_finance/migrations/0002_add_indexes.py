"""
Add database indexes for better performance.
"""
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('my_finance', '0001_initial'),
    ]

    operations = [
        # Property indexes
        migrations.AddIndex(
            model_name='property',
            index=migrations.Index(fields=['user', 'property_name'], name='property_user_name_idx'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=migrations.Index(fields=['user', 'created_at'], name='property_user_created_idx'),
        ),
        
        # PropertyRentalInfo indexes
        migrations.AddIndex(
            model_name='propertyrentalinfo',
            index=migrations.Index(fields=['property_address', 'tenant_name'], name='rental_property_tenant_idx'),
        ),
        migrations.AddIndex(
            model_name='propertyrentalinfo',
            index=migrations.Index(fields=['property_address', 'lease_start_date'], name='rental_property_lease_start_idx'),
        ),
        
        # PropertyInvoice indexes
        migrations.AddIndex(
            model_name='propertyinvoice',
            index=migrations.Index(fields=['property_details', 'invoice_date'], name='invoice_property_date_idx'),
        ),
        migrations.AddIndex(
            model_name='propertyinvoice',
            index=migrations.Index(fields=['property_details', 'invoice_due_date'], name='invoice_property_due_idx'),
        ),
        migrations.AddIndex(
            model_name='propertyinvoice',
            index=migrations.Index(fields=['property_details', 'invoice_paid_date'], name='invoice_property_paid_idx'),
        ),
        
        # PropertyMaintenance indexes
        migrations.AddIndex(
            model_name='propertymaintenance',
            index=migrations.Index(fields=['property_details', 'status'], name='maintenance_property_status_idx'),
        ),
        migrations.AddIndex(
            model_name='propertymaintenance',
            index=migrations.Index(fields=['property_details', 'created_at'], name='maintenance_property_created_idx'),
        ),
        migrations.AddIndex(
            model_name='propertymaintenance',
            index=migrations.Index(fields=['property_details', 'completed_date'], name='maintenance_property_completed_idx'),
        ),
        
        # PropertyExpense indexes
        migrations.AddIndex(
            model_name='propertyexpense',
            index=migrations.Index(fields=['property_details', 'expense_date'], name='expense_property_date_idx'),
        ),
        migrations.AddIndex(
            model_name='propertyexpense',
            index=migrations.Index(fields=['property_details', 'expense_category'], name='expense_property_category_idx'),
        ),
        
        # Transaction indexes
        migrations.AddIndex(
            model_name='transaction',
            index=migrations.Index(fields=['user', 'transaction_date'], name='transaction_user_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=migrations.Index(fields=['user', 'account'], name='transaction_user_account_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=migrations.Index(fields=['user', 'categories'], name='transaction_user_category_idx'),
        ),
        
        # Account indexes
        migrations.AddIndex(
            model_name='account',
            index=migrations.Index(fields=['user', 'name'], name='account_user_name_idx'),
        ),
        migrations.AddIndex(
            model_name='account',
            index=migrations.Index(fields=['user', 'created_at'], name='account_user_created_idx'),
        ),
        
        # Budget indexes
        migrations.AddIndex(
            model_name='budget',
            index=migrations.Index(fields=['user', 'created_at'], name='budget_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='budget',
            index=migrations.Index(fields=['user', 'category'], name='budget_user_category_idx'),
        ),
        
        # Category indexes
        migrations.AddIndex(
            model_name='category',
            index=migrations.Index(fields=['user', 'name'], name='category_user_name_idx'),
        ),
        
        # SubCategory indexes
        migrations.AddIndex(
            model_name='subcategory',
            index=migrations.Index(fields=['category', 'name'], name='subcategory_category_name_idx'),
        ),
    ] 