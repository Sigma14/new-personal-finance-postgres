from django.apps import AppConfig
from django.db.models.signals import post_migrate


class MyFinanceConfig(AppConfig):
    name = 'my_finance'

    def ready(self):
        from .models import AISubscriptionPlan, AIFeatureLimits
        from django.db.utils import OperationalError, ProgrammingError

        def create_default_plans(sender, **kwargs):
            SUBSCRIPTION_PLANS = {
                "basic": {
                    "ai_portfolio_analysis": 30,
                    "ai_stock_analysis": 20,
                    "ai_personal_finance_budget": 25,
                    "ai_transaction_analysis": 15,
                    "ai_real_estate_analysis": 10,
                    "price": 9.99,
                    "duration_days": 30
                },
                "standard": {
                    "ai_portfolio_analysis": 60,
                    "ai_stock_analysis": 40,
                    "ai_personal_finance_budget": 50,
                    "ai_transaction_analysis": 30,
                    "ai_real_estate_analysis": 20,
                    "price": 19.99,
                    "duration_days": 30
                },
                "premium": {
                    "ai_portfolio_analysis": 100,
                    "ai_stock_analysis": 80,
                    "ai_personal_finance_budget": 100,
                    "ai_transaction_analysis": 60,
                    "ai_real_estate_analysis": 40,
                    "price": 29.99,
                    "duration_days": 30
                },
            }

            try:
                for plan_name, data in SUBSCRIPTION_PLANS.items():
                    plan_obj, _ = AISubscriptionPlan.objects.update_or_create(
                        plan_name=plan_name,
                        defaults={
                            'price': data["price"],
                            'duration_days': data["duration_days"]
                        }
                    )

                    # Add or update feature limits
                    for feature, limit in data.items():
                        if feature in ["price", "duration_days"]:
                            continue
                        AIFeatureLimits.objects.update_or_create(
                            plan=plan_obj,
                            feature_name=feature,
                            defaults={'usage_limit': limit}
                        )

            except (OperationalError, ProgrammingError):
                # Ignore errors if database or tables aren't ready
                pass

        post_migrate.connect(create_default_plans, sender=self)
