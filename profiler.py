import cProfile
from bot.liquidator_bot import LiquidatorBot
import pstats
from pstats import SortKey

name = "main_loop_profile"
bot = LiquidatorBot("http://localhost:8545")

cProfile.run("bot.main_loop()",name)
p = pstats.Stats(name)
p.strip_dirs().sort_stats(-1).print_stats(10)
p.sort_stats(SortKey.CUMULATIVE).print_stats(10)
