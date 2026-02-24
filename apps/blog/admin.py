from django.contrib import admin

from .models import BlogCategory, BlogPost, Tag


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "sort_order"]
    list_editable = ["sort_order"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "author_name", "published_at"]
    list_filter = ["status", "category", "published_at"]
    search_fields = ["title", "body", "excerpt"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["tags"]
    fieldsets = (
        (
            None,
            {
                "fields": ("title", "title_th", "slug", "status", "published_at"),
            },
        ),
        (
            "Content",
            {
                "fields": ("excerpt", "excerpt_th", "body", "body_th"),
            },
        ),
        (
            "Classification",
            {
                "fields": ("category", "tags", "author_name"),
            },
        ),
        (
            "Media",
            {
                "fields": ("featured_image", "featured_image_url"),
            },
        ),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description"),
                "classes": ("collapse",),
            },
        ),
    )
