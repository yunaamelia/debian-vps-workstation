"""
Database clients module.

Handles:
- PostgreSQL client
- MySQL/MariaDB client
- Redis CLI
- MongoDB tools
"""

from configurator.modules.base import ConfigurationModule


class DatabasesModule(ConfigurationModule):
    """
    Database clients installation module.

    Installs command-line clients for common databases.
    Does NOT install database servers (use Docker for that).
    """

    name = "Databases"
    description = "Database clients (PostgreSQL, MySQL/MariaDB, SQLite, Redis)"
    depends_on = ["system"]
    priority = 52
    mandatory = False

    def validate(self) -> bool:
        """Validate prerequisites."""
        return True

    def configure(self) -> bool:
        """Install database clients."""
        self.logger.info("Installing database clients...")

        # 1. PostgreSQL client
        if self.get_config("postgresql", True):
            self._install_postgresql_client()

        # 2. MySQL/MariaDB client
        if self.get_config("mysql", True):
            self._install_mysql_client()

        # 3. Redis CLI
        if self.get_config("redis", True):
            self._install_redis_cli()

        # 4. MongoDB tools
        if self.get_config("mongodb", False):
            self._install_mongodb_tools()

        # 5. SQLite
        if self.get_config("sqlite", True):
            self._install_sqlite()

        self.logger.info("✓ Database clients installed")
        return True

    def verify(self) -> bool:
        """Verify installation."""
        checks_passed = True

        if self.get_config("postgresql", True):
            if self.command_exists("psql"):
                result = self.run("psql --version", check=False)
                self.logger.info(f"✓ PostgreSQL: {result.stdout.strip()}")
            else:
                self.logger.warning("PostgreSQL client not found")

        if self.get_config("mysql", True):
            if self.command_exists("mysql"):
                result = self.run("mysql --version", check=False)
                self.logger.info(f"✓ MySQL: {result.stdout.strip()}")
            else:
                self.logger.warning("MySQL client not found")

        if self.get_config("redis", True):
            if self.command_exists("redis-cli"):
                result = self.run("redis-cli --version", check=False)
                self.logger.info(f"✓ Redis: {result.stdout.strip()}")
            else:
                self.logger.warning("Redis CLI not found")

        if self.get_config("sqlite", True):
            if self.command_exists("sqlite3"):
                result = self.run("sqlite3 --version", check=False)
                self.logger.info(f"✓ SQLite: {result.stdout.strip()}")
            else:
                self.logger.warning("SQLite not found")

        return checks_passed

    def _install_postgresql_client(self):
        """Install PostgreSQL client."""
        self.logger.info("Installing PostgreSQL client...")
        self.install_packages(
            [
                "postgresql-client",
                "libpq-dev",  # For Python psycopg2
            ]
        )
        self.logger.info("✓ PostgreSQL client installed")

    def _install_mysql_client(self):
        """Install MySQL/MariaDB client."""
        self.logger.info("Installing MySQL client...")
        self.install_packages(
            [
                "default-mysql-client",
                "libmysqlclient-dev",  # For Python mysqlclient
            ]
        )
        self.logger.info("✓ MySQL client installed")

    def _install_redis_cli(self):
        """Install Redis CLI."""
        self.logger.info("Installing Redis CLI...")
        self.install_packages(["redis-tools"])
        self.logger.info("✓ Redis CLI installed")

    def _install_mongodb_tools(self):
        """Install MongoDB tools."""
        self.logger.info("Installing MongoDB tools...")

        # Add MongoDB repo
        self.run(
            "curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | "
            "gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg",
            check=False,
        )

        self.run(
            "echo 'deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] "
            "http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main' | "
            "tee /etc/apt/sources.list.d/mongodb-org-7.0.list",
            check=False,
        )

        self.run("apt-get update", check=False)
        self.install_packages(["mongodb-mongosh", "mongodb-database-tools"], update_cache=False)

        self.logger.info("✓ MongoDB tools installed")

    def _install_sqlite(self):
        """Install SQLite."""
        self.logger.info("Installing SQLite...")
        self.install_packages(["sqlite3", "libsqlite3-dev"])
        self.logger.info("✓ SQLite installed")
