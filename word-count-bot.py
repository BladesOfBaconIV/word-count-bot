from discord import Message, Member
import discord
from discord.ext import commands
from functools import wraps
from itertools import repeat
from typing import List, Dict

import re
import sqlite3


# SQLite3 stuff
con = sqlite3.connect('word_count.db')
with open('create-table.sql', 'r') as init_sql:
    con.executescript(init_sql.read())

DB_CURSOR = con.cursor()
INCREASE_TOTAL = "INSERT INTO word_counts (user_id, word) VALUES (?, ?) ON CONFLICT(user_id, word) DO UPDATE SET total = total + 1"
GET_TOTAL_ALL = "SELECT user_id, total FROM word_counts WHERE word=?"
GET_TOTAL_USER = "SELECT total FROM word_counts WHERE user_id=? AND word=?"

def commit_if_no_error(func):
    """Decorator to commit after sql method if no error, else pass the error on"""
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
            con.commit()
        except Exception as e:
            raise e
    return inner


# discord stuff
intent = discord.Intents.default()
intent.members = True
bot = commands.Bot("?", intents=intent)


@bot.event
async def on_message(message: Message) -> None:
    message_text = message.content
    if not message.author.bot and message_text[0] not in ('_', '-', '!', '?', '/', '\\', ):
        _insert_words(message.author.id, _get_words(message_text))
    await bot.process_commands(message)


@bot.command(name='wc')
async def word_count_single_word(ctx, word: str, user: Member=None) -> None:
    """Get the count for a word over all users, @ a user to get the result for just them"""
    word = word.lower()
    if user is not None:
        total = _get_word_count_single(user.id, word)
        await ctx.send(f"{user.name} said `{word}` {total} times since I started counting")
    else:
        totals = await _get_word_count_all(word)
        await ctx.send(f"```\n{_make_table(totals)}```")


# helper methods

def _get_words(text) -> List[str]:
    return re.findall(
        r"\w+", 
        re.sub(r'https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)
    )


@commit_if_no_error
def _insert_words(user_id, words) -> None:
    params = zip(repeat(user_id), words)
    DB_CURSOR.executemany(INCREASE_TOTAL, params)


async def _get_word_count_all(word: str) -> Dict[str, int]:
    await bot.wait_until_ready()
    DB_CURSOR.execute(GET_TOTAL_ALL, (word, ))
    return {
        bot.get_user(id).name: total
        for (id, total) in DB_CURSOR.fetchall()
    }


def _get_word_count_single(user_id: int, word: str) -> int:
    DB_CURSOR.execute(GET_TOTAL_USER, (user_id, word))
    result = DB_CURSOR.fetchone()
    return result[0] if result is not None else 0


def _make_table(word_count_info: Dict[str, int]) -> str:
    longest_name = max(map(len, word_count_info.keys()))
    longest_number = max(map(len, map(str, word_count_info.values())))
    padding = ' ' * 3
    table_top = '-' * (longest_name + longest_number + (2 * len(padding)) + 3)
    row = f"|{{name:<{longest_name}}}{padding}|{padding}{{value:>{longest_number}}}|"
    rows = f"\n".join([
        row.format(name=name, value=value)
        for name, value in sorted(word_count_info.items(), key=lambda x: x[1])
    ])
    return f"{table_top}\n{rows}\n{table_top}"



bot.run('')