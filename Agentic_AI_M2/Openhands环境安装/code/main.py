import asyncio
import os

from openhands.core.config import load_openhands_config, OpenHandsConfig
from openhands.core.main import run_controller
from openhands.core.setup import generate_sid
from openhands.events.action import Action, NullAction, MessageAction


def do_openhands_original():
    config: OpenHandsConfig = load_openhands_config(config_file="./config.toml")
    task_file = './task.txt'
    # Read task from file, CLI args, or stdin
    instruction_path = os.path.join(os.path.dirname(__file__), task_file)
    with open(instruction_path, 'r') as file:
        instruction = file.read().strip()
    task_str = instruction
    initial_user_action: Action = NullAction()
    if config.replay_trajectory_path:
        if task_str:
            raise ValueError(
                'User-specified task is not supported under trajectory replay mode'
            )
    else:
        if not task_str:
            raise ValueError('No task provided. Please specify a task through -t, -f.')

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
