from __future__ import unicode_literals

__author__ = 'David Baum'

import logging, time

from asana.error import NotFoundError, InvalidTokenError, ForbiddenError
from django.apps import apps
from django.core.management.base import OutputWrapper
from djasana.connect import client_connect
from djasana.settings import settings
from djasana.models import (
    Attachment,
    Project,
    Story,
    SyncToken,
    Tag,
    Task,
    Team,
    User,
    Webhook,
    Workspace,
)
from djasana.utils import (
    pop_unsupported_fields,
    set_webhook,
    sync_attachment,
    sync_project,
    sync_story,
    sync_task,
)

from typing import Union, List

logger = logging.getLogger(__name__)


class AsanaSynchronizer(object):
    def __init__(
            self,
            commit: Union[bool, None] = True,
            process_archived: Union[bool, None] = False,
            exclude_models: List[str] = [],
            include_models: List[str] = [],
            verbosity: int = 0,
            workspaces: List[str] = [],
            projects: List[str] = [],
            stdout: Union[OutputWrapper, None] = None,
            app_logger: Union[logging.Logger, None] = None,
    ):
        self.synced_ids = []
        self.commit = commit
        self.stdout = stdout
        self.process_archived = process_archived
        self.exclude_models = exclude_models
        self.include_models = include_models
        self.logger = app_logger or logger
        self.process_models = self._get_models()
        if verbosity >= 1:
            message = "Synchronizing data from Asana."
            if self.stdout:
                self.stdout.write(message)
            self.logger.info(message)
        self.workspaces = workspaces
        if settings.ASANA_WORKSPACE:
            workspaces.append(settings.ASANA_WORKSPACE)
        self.client = client_connect()
        self.workspace_ids = self._get_workspace_ids(workspaces)
        self.projects = projects

    def run_sync(self):
        for workspace_id in self.workspace_ids:
            self._sync_workspace_id(workspace_id, self.projects, self.process_models)

    def _sync_workspace_id(self, workspace_id, projects, models):
        workspace_dict = self.client.workspaces.find_by_id(workspace_id)
        self.logger.debug("Sync workspace %s", workspace_dict["name"])
        self.logger.debug(workspace_dict)
        if Workspace in models and self.commit:
            remote_id = workspace_dict["gid"]
            workspace_dict.pop("email_domains")
            workspace = Workspace.objects.update_or_create(
                remote_id=remote_id, defaults=workspace_dict
            )[0]
        else:
            workspace = None
        project_ids = self._get_project_ids(projects, workspace_id)
        if (
                "workspace_id" in self.client.options
                and workspace_id != self.client.options["workspace_id"]
        ):
            self.client.options["workspace_id"] = str(workspace_id)

        if User in models:
            for user in self.client.users.find_all({"workspace": workspace_id}):
                self._sync_user(user, workspace)
                time.sleep(0.5)

        if Tag in models:
            for tag in self.client.tags.find_by_workspace(workspace_id):
                self._sync_tag(tag, workspace)
                time.sleep(0.5)

        if Team in models:
            for team in self.client.teams.find_by_organization(workspace_id):
                self._sync_team(team)
                time.sleep(0.5)

        if Project in models:
            for project_id in project_ids:
                self._check_sync_project_id(project_id, workspace, models)

        if workspace:
            message = f"Successfully synced workspace {workspace.name}."
            if self.stdout:
                self.stdout.write(self.style.SUCCESS(message))
            self.logger.info(message)

    def _check_sync_project_id(self, project_id, workspace, models):
        """If we have a valid sync token for this project sync new events
        else sync the project"""
        new_sync = False
        try:
            sync_token = SyncToken.objects.get(project_id=project_id)
            try:
                events = self.client.events.get(
                    {"resource": project_id, "sync": sync_token.sync}
                )
                self._process_events(project_id, events, models)
                self._set_webhook(workspace, project_id)
                return
            except InvalidTokenError as error:
                sync_token.sync = error.sync
                sync_token.save()
        except SyncToken.DoesNotExist:
            try:
                self.client.events.get({"resource": project_id})
            except InvalidTokenError as error:
                new_sync = error.sync
        is_archived = self._sync_project_id(project_id, models)
        if not is_archived:
            self._set_webhook(workspace, project_id)
        if new_sync:
            SyncToken.objects.create(project_id=project_id, sync=new_sync)

    def _get_workspace_ids(self, workspaces):
        workspace_ids = []
        bad_list = []
        workspaces_ = self.client.workspaces.find_all()
        if workspaces:
            for workspace in workspaces:
                for wks in workspaces_:
                    if workspace in (wks["gid"], wks["name"]):
                        workspace_ids.append(wks["gid"])
                        break
                else:
                    bad_list.append(workspace)
        else:
            workspace_ids = [wks["gid"] for wks in workspaces_]
        if bad_list:
            if len(bad_list) == 1:
                raise ValueError(f"{workspaces[0]} is not an Asana workspace")
            raise ValueError(
                f'Specified workspaces are not valid: {", ".join(bad_list)}'
            )
        # Return newer workspaces first so they get synced earlier
        return sorted(workspace_ids, reverse=True)

    def _get_project_ids(self, projects, workspace_id):
        project_ids = []
        bad_list = []

        projects_ = self.client.projects.find_all({"workspace": workspace_id})
        self.logger.info("Sync project %s", projects)

        if projects:
            for project in projects:
                for prj in projects_:
                    if project in (prj["gid"], prj["name"]):
                        project_ids.append(prj["gid"])
                        break
                else:
                    bad_list.append(project)
        else:
            project_ids = [prj["gid"] for prj in projects_]
        if bad_list:
            if len(bad_list) == 1:
                raise ValueError(f"{bad_list[0]} is not an Asana project")
            raise ValueError(
                f"Specified projects are not valid: {', '.join(bad_list)}"
            )
        # Return newer projects first so they get synced earlier
        return sorted(project_ids, reverse=True)

    def _set_webhook(self, workspace, project_id):
        """Sets a webhook if the setting is configured and
        a webhook does not currently exist"""
        if not (self.commit and settings.DJASANA_WEBHOOK_URL):
            return
        webhooks = list(
            self.client.webhooks.get_all(
                {"workspace": workspace.remote_id, "resource": project_id}
            )
        )
        if webhooks:
            # If there is exactly one, and it is active, we are good to go,
            # else delete them and start a new one.
            webhooks_ = Webhook.objects.filter(project_id=project_id)
            if len(webhooks) == webhooks_.count() == 1 and webhooks[0]["active"]:
                return
            for webhook in webhooks:
                self.client.webhooks.delete_by_id(webhook["id"])
            Webhook.objects.filter(
                id__in=webhooks_.values_list("id", flat=True)[1:]
            ).delete()
        set_webhook(self.client, project_id)

    def _process_events(self, project_id, events, models):
        project = Project.objects.get(remote_id=project_id)
        ignored_tasks = 0
        for event in events["data"]:
            if event["type"] == "project":
                if Project in models:
                    if event["action"] == "removed":
                        Project.objects.get(remote_id=event["resource"]["gid"]).delete()
                    else:
                        self._sync_project_id(project_id, models)
                else:
                    ignored_tasks += 1
            elif event["type"] == "task":
                if Task in models:
                    if event["action"] == "removed":
                        Task.objects.get(remote_id=event["resource"]["gid"]).delete()
                    else:
                        self._sync_task(event["resource"], project, models)
                else:
                    ignored_tasks += 1
            elif event["type"] == "story":
                if Story in models:
                    self._sync_story(event["resource"])
                else:
                    ignored_tasks += 1
        tasks_done = len(events["data"]) - ignored_tasks
        if self.commit:
            message = "Successfully synced {0} events for project {1}.".format(
                tasks_done, project.name
            )
            if ignored_tasks:
                message += " {0} events ignored for excluded models.".format(
                    ignored_tasks
                )
            if self.stdout:
                self.stdout.write(self.style.SUCCESS(message))
            self.logger.info(message)

    def _sync_project_id(self, project_id, models):
        """Sync this project by polling it. Returns boolean 'is archived?'"""
        project_dict = self.client.projects.find_by_id(project_id)
        self.logger.debug("Sync project %s", project_dict["name"])
        self.logger.debug(project_dict)
        if self.commit:
            project = sync_project(self.client, project_dict)

        if Task in models and not project_dict["archived"] or self.process_archived:
            for task in self.client.tasks.find_all({"project": project_id}):
                self._sync_task(task, project, models)
                time.sleep(0.5)
            # Delete local tasks for this project that are no longer in Asana.
            tasks_to_delete = (
                Task.objects.filter(projects=project)
                .exclude(remote_id__in=self.synced_ids)
                .exclude(remote_id__isnull=True)
            )
            if tasks_to_delete.count() > 0:
                id_list = list(tasks_to_delete.values_list("remote_id", flat=True))
                tasks_to_delete.delete()
                message = "Deleted {} tasks no longer present: {}".format(
                    len(id_list), id_list
                )
                if self.stdout:
                    self.stdout.write(self.style.SUCCESS(message))
                self.logger.info(message)
        if self.commit:
            message = f"Successfully synced project {project.name}."
            if self.stdout:
                self.stdout.write(self.style.SUCCESS(message))
            self.logger.info(message)
        return project_dict["archived"]

    def _sync_story(self, story):
        story_id = story.get("gid")
        try:
            story_dict = self.client.stories.find_by_id(story_id)
        except NotFoundError as error:
            self.logger.info(error.response)
            return
        self.logger.debug(story_dict)
        remote_id = story_dict["gid"]
        sync_story(remote_id, story_dict)

    def _sync_tag(self, tag, workspace):
        tag_dict = self.client.tags.find_by_id(tag["gid"])
        self.logger.debug(tag_dict)
        if self.commit:
            remote_id = tag_dict["gid"]
            tag_dict["workspace"] = workspace
            followers_dict = tag_dict.pop("followers")
            pop_unsupported_fields(tag_dict, Tag)
            tag = Tag.objects.get_or_create(remote_id=remote_id, defaults=tag_dict)[0]
            follower_ids = [follower["gid"] for follower in followers_dict]
            followers = User.objects.filter(id__in=follower_ids)
            tag.followers.set(followers)

    def _sync_task(self, task, project, models, skip_subtasks=False):
        """Sync this task and its parent, dependencies, and subtasks

        For parents and subtasks, this method is called recursively,
        so skip_subtasks True is passed when syncing a parent task from a subtask.
        """
        task_id = task["gid"]
        try:
            task_dict = self.client.tasks.find_by_id(task_id)
        except (ForbiddenError, NotFoundError):
            try:
                Task.objects.get(remote_id=task_id).delete()
            except Task.DoesNotExist:
                pass
            return
        self.logger.debug("Sync task %s", task_dict["name"])
        self.logger.debug(task_dict)

        if Task in models and self.commit:
            remote_id = task_dict["gid"]
            parent = task_dict.pop("parent", None)
            dependencies = task_dict.pop("dependencies", None) or []
            if parent:
                # If this is a task we already know about, assume it was just synced.
                parent_id = parent["gid"]
                if (
                        parent_id not in self.synced_ids
                        and not Task.objects.filter(remote_id=parent_id).exists()
                ):
                    self._sync_task(parent, project, models, skip_subtasks=True)
                task_dict["parent_id"] = parent_id
            task_ = sync_task(remote_id, task_dict, project, sync_tags=Tag in models)
            self.synced_ids.append(remote_id)
            if not skip_subtasks:
                for subtask in self.client.tasks.subtasks(task_id):
                    if subtask["gid"] not in self.synced_ids:
                        self._sync_task(subtask, project, models)
                if dependencies:
                    for subtask in dependencies:
                        if subtask["gid"] not in self.synced_ids:
                            self._sync_task(subtask, project, models)
                    task_.dependencies.set(
                        Task.objects.filter(
                            remote_id__in=[dep["gid"] for dep in dependencies]
                        )
                    )
        if Attachment in models and self.commit:
            for attachment in self.client.attachments.find_by_task(task_id):
                sync_attachment(self.client, task_, attachment["gid"])
        if Story in models and self.commit:
            for story in self.client.stories.find_by_task(task_id):
                self._sync_story(story)
        return

    def _sync_team(self, team):
        team_dict = self.client.teams.find_by_id(team["gid"])
        self.logger.debug(team_dict)
        if self.commit:
            remote_id = team_dict["gid"]
            organization = team_dict.pop("organization")
            team_dict["organization_id"] = organization["gid"]
            team_dict["organization_name"] = organization["name"]
            pop_unsupported_fields(team_dict, Team)
            Team.objects.get_or_create(remote_id=remote_id, defaults=team_dict)

    def _sync_user(self, user, workspace):
        user_dict = self.client.users.find_by_id(user["gid"])
        self.logger.debug(user_dict)
        if self.commit:
            remote_id = user_dict["gid"]
            user_dict.pop("workspaces")
            if user_dict["photo"]:
                user_dict["photo"] = user_dict["photo"]["image_128x128"]
            user = User.objects.update_or_create(
                remote_id=remote_id, defaults=user_dict
            )[0]
            if workspace:
                user.workspaces.add(workspace)

    def _get_models(self):
        """Returns a list of models to sync"""
        app_models = list(apps.get_app_config("djasana").get_models())
        if self.include_models:
            good_models = []
            model_names = [model_.__name__.lower() for model_ in app_models]
            for model in self.include_models:
                try:
                    index = model_names.index(model.lower())
                except ValueError:
                    raise ValueError(f"{model} is not an Asana model")
                else:
                    good_models.append(app_models[index])
            models = good_models
        else:
            models = app_models
        if self.exclude_models:
            models = [
                model
                for model in models
                if model.__name__.lower() not in [m.lower() for m in self.exclude_models]
            ]
        return models
