"""Holy Symbol slash command metadata configuration."""

from app.bot.command_config import SlashCommandConfig

HOLY_SYMBOL_START_COMMAND = SlashCommandConfig(
    name="홀심시작",
    description="홀리심볼 타이머를 시작합니다.",
)

HOLY_SYMBOL_STOP_COMMAND = SlashCommandConfig(
    name="홀심중지",
    description="실행 중인 홀리심볼 타이머를 중지합니다.",
)

HOLY_SYMBOL_STATUS_COMMAND = SlashCommandConfig(
    name="홀심상태",
    description="홀리심볼 타이머 남은 시간을 확인합니다.",
)
