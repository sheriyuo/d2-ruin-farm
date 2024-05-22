import time
from pathlib import Path
from loguru import logger

X_SIMILARITY_CHECK_INTERVAL = 4
BOSS_HP_BAR_CHECK_INTERVAL = 0.5

def run():
    from pydirectinput import press
    from screenshot import (
        get_x_similarity,
        get_boss_hp_bar_mask_ratio,
        get_finish_hp_bar_mask_ratio,
        get_normal_hp_bar_mask_ratio,
    )
    from directx import (
        kick_boss_by_indebted_kindess,
        start_next_round,
        refresh_checkpoint,
        hide_indebted_kindess,
        self_kill,
        open_dim_and_collect,
    )
    from settings import base_settings, monitor_settings

    logger.add("./logs/d2-ruin-farm_{time}.log", level=base_settings.log_level)
    logger.info(base_settings)
    logger.info(monitor_settings)

    total_time = 0
    max_time = 0
    start_count = 0
    finish_count = 0
    success_count = 0
    is_collected = 0
    continuous_fail_count = 0
    need_refresh_checkpoint = False

    logger.info("程序启动")

    if base_settings.debug:
        logger.info("已开启调试模式")
        Path("./debug").mkdir(exist_ok=True)

    time.sleep(2)

    while True:
        while True:
            x_similarity = get_x_similarity()
            if x_similarity > 0.8:
                # logger.info("检测到X技能准备就绪")
                break
            time.sleep(X_SIMILARITY_CHECK_INTERVAL)

        if continuous_fail_count >= 30:
            # logger.info("连续失败次数超过30次，重新进本")
            start_next_round()
            need_refresh_checkpoint = True
            continuous_fail_count = 0
            continue

        if need_refresh_checkpoint:
            refresh_checkpoint()
            need_refresh_checkpoint = False
            continue

        if success_count % 5 == 1 and is_collected == 0:
            open_dim_and_collect()
            is_collected = 1

        logger.info(
            f"start_count: {start_count}, finish_count: {finish_count}, \
success_count: {success_count}, avg_time: {0 if success_count == 0 else total_time / success_count:.2f}, \
max_time: {max_time:.2f}, succ_rate: {0 if success_count == 0 else success_count / start_count:.4f}"
        )
        start_count += 1

        kick_boss_by_indebted_kindess()
        time.sleep(0.1)

        hp_bar_mask_ratio = get_finish_hp_bar_mask_ratio()

        if not hp_bar_mask_ratio >= 0.8:
            continuous_fail_count += 1
            # logger.info("未在玩家血条上检测到感应护盾，准备团灭重试")

            press(base_settings.职业技能按键)
            time.sleep(3.5)
            self_kill()

            continue

        finish_count += 1
        # logger.info("玩家血条蓝盾检测成功")
        start_time = time.monotonic()

        # 躲起来等待boss血条消失
        time.sleep(2)
        hide_indebted_kindess()

        while True:
            if time.monotonic() - start_time >= 22.5:
                continuous_fail_count += 1
                # logger.info("等待boss血条消失超时，准备团灭重试")

                self_kill()

                break

            boss_hp_bar_mask_ratio = get_boss_hp_bar_mask_ratio()

            # 如果boss血条消失，进行玩家血条的检测
            if boss_hp_bar_mask_ratio <= 0.1:
                # logger.info("boss血条已消失")

                normal_hp_bar_mask_ratio = get_normal_hp_bar_mask_ratio()

                # 如果再检测到玩家血条，说明正常结算
                if normal_hp_bar_mask_ratio >= 0.8:
                    now_time = time.monotonic() - start_time
                    if now_time > max_time:
                        max_time = now_time
                    total_time += now_time
                    success_count += 1
                    is_collected = 0
                    continuous_fail_count = 0
                    need_refresh_checkpoint = True
                    logger.success(f"success, now_time: {now_time:.2f}")
                    time.sleep(2)
                    start_next_round()

                    break
                # 如果没有检测到玩家血条，说明灭了
                else:
                    # logger.info("未检测到玩家的血条，本轮团灭")
                    continuous_fail_count += 1
                    break

            time.sleep(BOSS_HP_BAR_CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        ...
    except Exception as e:
        import sys

        logger.exception(e)
        sys.exit(1)
