"""The django management command sync_from_asana"""
import logging
from django.core.management.base import BaseCommand, CommandError
from djasana.synchronizer import AsanaSynchronizer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Sync data from Asana to the database"""

    help = "Import data from Asana and insert/update model instances"
    commit = True
    process_archived = False
    synced_ids = []  # A running list of remote ids of tasks that have been synced.

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            action="store_false",
            dest="interactive",
            default=True,
            help="If provided, no prompts will be issued to the user "
                 "and the data will be synced.",
        )
        parser.add_argument(
            "-w",
            "--workspace",
            action="append",
            default=[],
            help="Sync only the named workspace (can be used multiple times). "
                 "By default all workspaces will be updated from Asana.",
        )
        parser.add_argument(
            "-p",
            "--project",
            action="append",
            default=[],
            help="Sync only the named project (can be used multiple times). "
                 "By default all projects will be updated from Asana.",
        )
        parser.add_argument(
            "-m",
            "--model",
            action="append",
            default=[],
            help="Sync only the named model (can be used multiple times). "
                 "By default all models will be updated from Asana.",
        )
        parser.add_argument(
            "-mx",
            "--model-exclude",
            action="append",
            default=[],
            help="Exclude the named model (can be used multiple times).",
        )
        parser.add_argument(
            "-a",
            "--archive",
            action="store_false",
            dest="archive",
            help="Sync project tasks etc. even if the project is archived. "
                 "By default, only tasks of unarchived projects are updated from Asana. "
                 "Regardless of this setting, the project itself will be updated, "
                 "perhaps becoming marked as archived. ",
        )
        parser.add_argument(
            "--nocommit",
            action="store_false",
            dest="commit",
            default=True,
            help="Will not commit changes to the database.",
        )

    def handle(self, *args, **options):
        self.commit = not options.get("nocommit")
        if self.commit and options.get("interactive", True):
            self.stdout.write(
                "WARNING: This will irreparably synchronize "
                "your local database from Asana."
            )
            if not self._confirm():
                self.stdout.write("No action taken.")
                return
        if options.get("verbosity", 0) >= 1:
            message = "Synchronizing data from Asana."
            self.stdout.write(message)
            logger.info(message)
        workspaces = options.get("workspace") or []
        projects = options.get("project")

        synchronizer = AsanaSynchronizer(
            commit=self.commit,
            workspaces=workspaces,
            projects=projects,
            verbosity=options.get("verbosity", 0),
            exclude_models=options.get("model_exclude"),
            include_models=options.get("model"),
            process_archived=options.get("archive"),
        )
        try:
            synchronizer.run_sync()
        except Exception as e:
            raise CommandError(e.message)

    @staticmethod
    def _confirm():
        yes_or_no = input("Are you sure you wish to continue? [y/N] ")
        return yes_or_no.lower().startswith("y")
