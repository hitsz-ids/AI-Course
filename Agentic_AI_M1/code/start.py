import asyncio
from pathlib import Path

from openhands.core.config import load_openhands_config, OpenHandsConfig
from openhands.core.main import run_controller
from openhands.core.setup import generate_sid
from openhands.events.action import MessageAction


def do_openhands_original():
    config: OpenHandsConfig = load_openhands_config(config_file="./config.toml")
    task_file = './task.txt'
    template = Path(task_file).read_text(
        encoding='utf-8')
    prompt = template.format(
        conda_env='填写具体python执行的环境名称，可以是任意的但必须是小写',
        project='填写具体的sota工程代码对应的目录名称，如（RegMean-plusplus）',
        evaluation_bash='填写你的测试脚本（根据具体的benchmark来设置）'
    )
    task_str = prompt

    # Create actual initial user action
    initial_user_action = MessageAction(content=task_str)
    # Set session name
    session_name = ''
    sid = generate_sid(config, session_name)

    asyncio.run(
        run_controller(
            config=config,
            initial_user_action=initial_user_action,
            sid=sid,
            fake_user_response_fn=None
        )
    )


if __name__ == '__main__':
    do_openhands_original()
