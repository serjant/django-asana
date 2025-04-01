from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from djasana import models


def asana_link(obj):
    return mark_safe(f'<a href="{obj.asana_url()}" target="_blank">View on Asana</a>')


def text_short(obj):
    return f"{obj.text[:300]}..." if len(obj.text) > 200 else obj.text


class ParentRawIdWidget(widgets.ForeignKeyRawIdWidget):
    def url_parameters(self):
        params = super().url_parameters()
        object_ = self.attrs.get("object", None)
        if object_:
            # Filter parent choices by project
            params["projects__id__exact"] = object_.projects.first().pk
        return params


@admin.register(models.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    exclude = ("resource_type",)
    list_display = ("__str__", "name", "parent", asana_link)
    raw_id_fields = ("parent",)
    readonly_fields = (asana_link, "gid")


@admin.register(models.CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    exclude = ("resource_type", "type")
    readonly_fields = (asana_link, "gid")
    list_fields = ("default_access_level",)


@admin.register(models.CustomFieldSetting)
class CustomFieldSettingAdmin(admin.ModelAdmin):
    exclude = ("resource_type",)
    readonly_fields = (asana_link, "gid")


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    exclude = ("resource_type",)
    list_display = ("__str__", "owner", "archived", asana_link)
    list_filter = ("workspace", "team", "archived")
    readonly_fields = ("workspace", "team", asana_link, "gid")
    search_fields = ("remote_id", "name")


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    exclude = ("resource_type",)
    list_display = ("__str__", "color", "notes", "workspace_link", "followers_list",)
    list_filter = ("workspace",)
    readonly_fields = ("workspace", "followers",)
    search_fields = ("notes", "color")

    def workspace_link(self, obj):
        """Render workspace as a clickable link in the admin list."""
        if obj.workspace:
            url = reverse(
                f"admin:{models.Workspace._meta.app_label}_{models.Workspace._meta.model_name}_change",
                args=[obj.workspace.id]
            )
            return format_html('<a href="{}">{}</a>', url, obj.workspace)
        return "-"

    def followers_list(self, obj):
        """Render followers as links in the admin list."""
        followers = obj.followers.all()
        if not followers:
            return "-"

        links = [
            format_html(
                '<a href="{}">{}</a>',
                reverse(
                    f"admin:{models.User._meta.app_label}_{models.User._meta.model_name}_change",
                    args=[user.id]),
                user.username
            )
            for user in followers
        ]
        return format_html(", ".join(links))

    followers_list.short_description = "Followers"
    workspace_link.short_description = "Workspace"


class TaskForm(forms.ModelForm):
    class Meta:
        fields = (
            "name",
            "assignee",
            "completed",
            "completed_at",
            "due_at",
            "due_on",
            "parent",
            "notes",
            "projects",
            "custom_fields",
            "tags"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["parent"].widget = ParentRawIdWidget(
                rel=self.instance._meta.get_field("parent").remote_field,
                admin_site=admin.site,
                # Pass the object to attrs
                attrs={"object": self.instance},
            )


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    exclude = ("resource_type",)
    form = TaskForm
    list_display = (
        "name",
        "assignee",
        "completed",
        "due",
        "completed_at",
        "modified_at",
        "due_at",
        "due_on",
        "tags_list",
        asana_link
    )
    list_filter = (
        "completed",
        "projects__workspace",
        "completed_at",
        "due_at",
        "due_on",
        "modified_at",
        "assignee",
        "projects",
    )
    raw_id_fields = ("assignee", "parent")
    readonly_fields = (asana_link, "gid")
    search_fields = ("remote_id", "name")
    list_per_page = 25

    def tags_list(self, obj):
        """Render followers as links in the admin list."""
        tags = obj.tags.all()
        if not tags:
            return "-"

        links = [
            format_html(
                '<a href="{}">{}</a>',
                reverse(
                    f"admin:{models.Tag._meta.app_label}_{models.Tag._meta.model_name}_change",
                    args=[tag.id]),
                tag.name
            )
            for tag in tags
        ]
        return format_html(", ".join(links))


@admin.register(models.Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = [
        "type",
        "resource_subtype",
        text_short,
        "created_by",
        "created_at",
        asana_link,
    ]
    list_filter = [
        "type",
        "resource_type",
        "resource_subtype",
        "created_at",
        "created_by",
    ]


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    exclude = ("resource_type",)
    list_display = ("__str__", asana_link)
    readonly_fields = (asana_link, "gid")


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    exclude = ("resource_type",)
    list_display = ("__str__",)
    readonly_fields = (asana_link, "gid")


@admin.register(models.Webhook)
class WebhookAdmin(admin.ModelAdmin):
    exclude = ("resource_type",)
    list_display = ("__str__", "project")
    readonly_fields = ("secret", "project")

    def has_add_permission(self, request):
        return False


@admin.register(models.Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    exclude = ("resource_type",)
    list_display = ("__str__", asana_link)
    readonly_fields = (asana_link, "gid")
