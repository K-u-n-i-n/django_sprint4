from django.contrib import admin
from .models import Category, Location, Post

# Установка отображения пустых значений в админке.
admin.site.empty_value_display = 'Не задано'


class PostInline(admin.TabularInline):
    """
    Определение Inline-класса, который используется
    для создания встроенных форм для связанных объектов Post.
    """

    model = Post
    # Количество дополнительных форм для ввода.
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    """Класс администрирования для модели Category."""

    inlines = (
        PostInline,
    )


class LocationAdmin(admin.ModelAdmin):
    """Класс администрирования для модели Location."""

    inlines = (
        PostInline,
    )


class PostAdmin(admin.ModelAdmin):
    """Класс администрирования для модели Post."""

    list_display = (
        'title',
        'text',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at'
    )
    list_editable = (
        'author',
        'location',
        'category',
        'is_published'
    )
    search_fields = ('title',)
    list_filter = ('is_published',)
    list_display_links = ('title',)


# Регистрация моделей в админке.
admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
