import asyncio

from app.bot.feed_subscription import register_feed_subscription_commands


class FakeResponse:
    def __init__(self) -> None:
        self.message: str | None = None
        self.ephemeral = False

    async def send_message(self, message: str, *, ephemeral: bool = False) -> None:
        self.message = message
        self.ephemeral = ephemeral


class FakePermissions:
    def __init__(self, manage_guild: bool) -> None:
        self.manage_guild = manage_guild


class FakeUser:
    def __init__(self, manage_guild: bool) -> None:
        self.guild_permissions = FakePermissions(manage_guild)


class FakeInteraction:
    channel_id = 123

    def __init__(self, manage_guild: bool = True) -> None:
        self.user = FakeUser(manage_guild)
        self.response = FakeResponse()


class FakeCommandTree:
    def __init__(self) -> None:
        self.commands = {}

    def command(self, name: str, description: str):
        def decorator(callback):
            self.commands[name] = {"callback": callback, "description": description}
            return callback

        return decorator


class FakeSubscriptionRepository:
    def __init__(self) -> None:
        self.saved: list[tuple[str, str, str | None]] = []
        self.disabled: list[tuple[str, str]] = []
        self.disable_result = True

    def save(self, *, category: str, channel_id: str, role_id: str | None = None) -> None:
        self.saved.append((category, channel_id, role_id))

    def disable(self, *, category: str, channel_id: str) -> bool:
        self.disabled.append((category, channel_id))
        return self.disable_result


def test_register_feed_subscription_commands_registers_both_commands() -> None:
    command_tree = FakeCommandTree()

    register_feed_subscription_commands(command_tree, FakeSubscriptionRepository())

    assert set(command_tree.commands) == {"subscribe", "unsubscribe"}


def test_subscribe_command_saves_current_channel_setting() -> None:
    command_tree = FakeCommandTree()
    repository = FakeSubscriptionRepository()
    interaction = FakeInteraction()
    register_feed_subscription_commands(command_tree, repository)

    asyncio.run(command_tree.commands["subscribe"]["callback"](interaction, "notice"))

    assert repository.saved == [("notice", "123", None)]
    assert interaction.response.message == "Subscribed <#123> to notice."
    assert interaction.response.ephemeral is True


def test_subscribe_command_rejects_unsupported_category() -> None:
    command_tree = FakeCommandTree()
    repository = FakeSubscriptionRepository()
    interaction = FakeInteraction()
    register_feed_subscription_commands(command_tree, repository)

    asyncio.run(command_tree.commands["subscribe"]["callback"](interaction, "other"))

    assert repository.saved == []
    assert interaction.response.message == "Unsupported category. Use notice, event, or devlog."


def test_subscription_commands_require_manage_guild_permission() -> None:
    command_tree = FakeCommandTree()
    repository = FakeSubscriptionRepository()
    interaction = FakeInteraction(manage_guild=False)
    register_feed_subscription_commands(command_tree, repository)

    asyncio.run(command_tree.commands["unsubscribe"]["callback"](interaction, "notice"))

    assert repository.disabled == []
    assert interaction.response.message == "You need Manage Server permission to change subscriptions."


def test_unsubscribe_command_reports_missing_active_subscription() -> None:
    command_tree = FakeCommandTree()
    repository = FakeSubscriptionRepository()
    repository.disable_result = False
    interaction = FakeInteraction()
    register_feed_subscription_commands(command_tree, repository)

    asyncio.run(command_tree.commands["unsubscribe"]["callback"](interaction, "notice"))

    assert repository.disabled == [("notice", "123")]
    assert interaction.response.message == "No active notice subscription exists for <#123>."
