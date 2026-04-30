"""Discord command metadata configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SlashCommandConfig:
    """Static metadata for a Discord slash command."""

    name: str
    description: str


PING_COMMAND = SlashCommandConfig(
    name="ping",
    description="Check whether the bot is responsive.",
)

NOTICE_COMMAND = SlashCommandConfig(
    name="공지",
    description="최신 메이플랜드 공지사항 5개를 보여줍니다.",
)
