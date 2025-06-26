import cProfile, asyncio, os, logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from utils.arg_parser import parse_and_validate_console_args
from utils.performance_results_saver import save_or_append_performance_results
from core.bot_management.bot_controller.bot_controller import BotController
from core.bot_management.event_bus import EventBus
from config.trading_mode import TradingMode
from core.bot_management.notification.notification_handler import NotificationHandler
from core.bot_management.grid_trading_bot import GridTradingBot
from core.bot_management.health_check import HealthCheck
from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.exceptions import ConfigError
from utils.logging_config import setup_logging
from utils.config_name_generator import generate_config_name

def initialize_config(config_path: str) -> ConfigManager:
    load_dotenv()
    try:
        return ConfigManager(config_path, ConfigValidator())

    except ConfigError as e:
        logging.error(f"An error occured during the initialization of ConfigManager {e}")
        exit(1)

def parse_notification_urls() -> List[str]:
    """Parse and validate notification URLs from environment variable."""
    env_var = os.getenv("APPRISE_NOTIFICATION_URLS", "")
    if not env_var.strip():
        logging.info("No notification URLs configured in APPRISE_NOTIFICATION_URLS")
        return []

    urls = [url.strip() for url in env_var.split(",") if url.strip()]
    if urls:
        logging.info(f"Loaded {len(urls)} notification URL(s)")
        for i, url in enumerate(urls, 1):
            # Log URL type without exposing sensitive tokens
            if url.startswith("tgram://"):
                logging.info(f"  URL {i}: Telegram notification")
            elif url.startswith("discord://"):
                logging.info(f"  URL {i}: Discord notification")
            else:
                logging.info(f"  URL {i}: {url.split('://')[0]} notification")
    else:
        logging.warning("APPRISE_NOTIFICATION_URLS is set but contains no valid URLs")

    return urls

def initialize_notification_handler(config_manager: ConfigManager, event_bus: EventBus) -> NotificationHandler:
    notification_urls = parse_notification_urls()
    trading_mode = config_manager.get_trading_mode()

    if notification_urls and trading_mode == TradingMode.BACKTEST:
        logging.warning("Notifications are disabled in backtest mode. Use 'live' or 'paper_trading' mode to enable notifications.")

    return NotificationHandler(event_bus, notification_urls, trading_mode)

async def run_bot(
    config_path: str,
    profile: bool = False, 
    save_performance_results_path: Optional[str] = None, 
    no_plot: bool = False
) -> Optional[Dict[str, Any]]:
    config_manager = initialize_config(config_path)
    config_name = generate_config_name(config_manager)
    setup_logging(config_manager.get_logging_level(), config_manager.should_log_to_file(), config_name)
    event_bus = EventBus()
    notification_handler = initialize_notification_handler(config_manager, event_bus)
    bot = GridTradingBot(config_path, config_manager, notification_handler, event_bus, save_performance_results_path, no_plot)
    bot_controller = BotController(bot, event_bus)
    health_check = HealthCheck(bot, notification_handler, event_bus)
    
    if profile:
        cProfile.runctx("asyncio.run(bot.run())", globals(), locals(), "profile_results.prof")
        return None

    try:
        if bot.trading_mode in {TradingMode.LIVE, TradingMode.PAPER_TRADING}:
            bot_task = asyncio.create_task(bot.run(), name="BotTask")
            bot_controller_task = asyncio.create_task(bot_controller.command_listener(), name="BotControllerTask")
            health_check_task = asyncio.create_task(health_check.start(), name="HealthCheckTask")
            await asyncio.gather(bot_task, bot_controller_task, health_check_task)
        else:
            await bot.run()
    
    except asyncio.CancelledError:
        logging.info("Cancellation received. Shutting down gracefully.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
    
    finally:
        try:
            await event_bus.shutdown()

        except Exception as e:
            logging.error(f"Error during EventBus shutdown: {e}", exc_info=True)

async def cleanup_tasks():
    logging.info("Shutting down bot and cleaning up tasks...")

    current_task = asyncio.current_task()
    tasks_to_cancel = {
        task for task in asyncio.all_tasks()
        if task is not current_task and not task.done() and not task.cancelled()
    }

    logging.info(f"Tasks to cancel: {len(tasks_to_cancel)}")

    for task in tasks_to_cancel:
        logging.info(f"Task to cancel: {task} - Done: {task.done()} - Cancelled: {task.cancelled()}")
        task.cancel()

    try:
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

    except asyncio.CancelledError:
        logging.info("Tasks cancelled successfully.")

    except Exception as e:
        logging.error(f"Error during task cancellation: {e}", exc_info=True)

if __name__ == "__main__":
    args = parse_and_validate_console_args()
    
    async def main():
        try:
            tasks = [
                run_bot(config_path, args.profile, args.save_performance_results, args.no_plot)
                for config_path in args.config
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for index, result in enumerate(results):
                if isinstance(result, Exception):
                    logging.error(
                        f"Error occurred while running bot for config {args.config[index]}: {result}",
                        exc_info=True
                    )
                else:
                    if args.save_performance_results:
                        save_or_append_performance_results(result, args.save_performance_results)

        except Exception as e:
            logging.error(f"Critical error in main: {e}", exc_info=True)

        finally:
            await cleanup_tasks()
            logging.info("All tasks have completed.")

    asyncio.run(main())