from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import BlogCategory, BlogPost


class BlogListView(ListView):
    model = BlogPost
    template_name = "blog/blog_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        qs = (
            BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)
            .select_related("category")
            .prefetch_related("tags")
        )

        # Filter by category
        cat = self.request.GET.get("category")
        if cat:
            qs = qs.filter(category__slug=cat)

        # Filter by tag
        tag = self.request.GET.get("tag")
        if tag:
            qs = qs.filter(tags__slug=tag)

        # Search
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(body__icontains=q) | Q(excerpt__icontains=q)
            )

        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = BlogCategory.objects.all()
        ctx["current_filters"] = {
            "category": self.request.GET.get("category", ""),
            "tag": self.request.GET.get("tag", ""),
            "q": self.request.GET.get("q", ""),
        }
        return ctx


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = "blog/blog_detail.html"
    context_object_name = "post"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)
            .select_related("category")
            .prefetch_related("tags")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = self.object
        ctx["related_posts"] = (
            BlogPost.objects.filter(
                status=BlogPost.Status.PUBLISHED, category=post.category
            )
            .exclude(pk=post.pk)
            .select_related("category")[:3]
        )
        return ctx
