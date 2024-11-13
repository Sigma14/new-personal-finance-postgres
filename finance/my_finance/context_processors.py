import datetime
import json
from .helper import create_categories, create_category_group
from .models import Category, SuggestiveCategory, MyNotes


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


def user_notes(request):
    """
    Retrieves the user's notes and returns them in the context.

    Args:
        request: The HTTP request object containing user data.

    Returns:
        dict: Context with note title, description, and today's date.
    """
    try:
        user_name = request.user
        user_note = MyNotes.objects.filter(user=user_name)
        current_date = datetime.date.today()
        user_index = 0
        if user_note:
            for data in user_note:
                if user_index == 0:
                    note_title = data.title
                    note_desc = json.dumps(data.notes)
                user_index += 1
        else:
            note_title = ""
            note_desc = ""

        context = {
            "note_title": note_title,
            "note_desc": note_desc,
            "user_notes": user_note,
            "today_date": str(current_date)
        }
        return context

    except:
        note_title = False
        note_desc = ""
        print("NOTES NOT AVAILABLE")
        context = {
            "note_title": note_title,
            "note_desc": note_desc
        }
        return context
