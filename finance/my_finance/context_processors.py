from .helper import create_categories, create_category_group
from .models import Category, SuggestiveCategory


def user_category(request):
    try:
        if request.user.is_anonymous:
            return {}
        category = Category.objects.filter(user=request.user)
        print(category)
        suggest_category = SuggestiveCategory.objects.filter()
        if not category:
            create_categories(request.user)
        if not suggest_category:
            create_category_group()
        return {}
    except Exception as e:
        print("e as =====>", e)
        return {}
