#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

import alembic
from alembic import config as alembic_config
import alembic.migration as alembic_migration

from oslo_db.sqlalchemy.migration_cli import ext_base


class AlembicExtension(ext_base.MigrationExtensionBase):

    order = 2

    @property
    def enabled(self):
        return os.path.exists(self.alembic_ini_path)

    def __init__(self, engine, migration_config):
        """Extension to provide alembic features.

        :param engine: SQLAlchemy engine instance for a given database
        :type engine: sqlalchemy.engine.Engine
        :param migration_config: Stores specific configuration for migrations
        :type migration_config: dict
        """
        self.alembic_ini_path = migration_config.get('alembic_ini_path', '')
        self.config = alembic_config.Config(self.alembic_ini_path)
        # TODO(viktors): Remove this, when we will use Alembic 0.7.5 or
        #                higher, because the ``attributes`` dictionary was
        #                added to Alembic in version 0.7.5.
        if not hasattr(self.config, 'attributes'):
            self.config.attributes = {}
        # option should be used if script is not in default directory
        repo_path = migration_config.get('alembic_repo_path')
        if repo_path:
            self.config.set_main_option('script_location', repo_path)
        self.engine = engine

    def upgrade(self, version):
        with self.engine.begin() as connection:
            self.config.attributes['connection'] = connection
            return alembic.command.upgrade(self.config, version or 'head')

    def downgrade(self, version):
        if isinstance(version, int) or version is None or version.isdigit():
            version = 'base'
        with self.engine.begin() as connection:
            self.config.attributes['connection'] = connection
            return alembic.command.downgrade(self.config, version)

    def version(self):
        with self.engine.connect() as conn:
            context = alembic_migration.MigrationContext.configure(conn)
            return context.get_current_revision()

    def revision(self, message='', autogenerate=False):
        """Creates template for migration.

        :param message: Text that will be used for migration title
        :type message: string
        :param autogenerate: If True - generates diff based on current database
                             state
        :type autogenerate: bool
        """
        with self.engine.begin() as connection:
            self.config.attributes['connection'] = connection
            return alembic.command.revision(self.config, message=message,
                                            autogenerate=autogenerate)

    def stamp(self, revision):
        """Stamps database with provided revision.

        :param revision: Should match one from repository or head - to stamp
                         database with most recent revision
        :type revision: string
        """
        with self.engine.begin() as connection:
            self.config.attributes['connection'] = connection
            return alembic.command.stamp(self.config, revision=revision)
