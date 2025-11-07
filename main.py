import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque

# قائمة انتظار لكل سيرفر
queues = {}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 🎵 أمر التشغيل
@bot.command(aliases=['ش', 'p'])
async def playsearch(ctx, *, search):
    try:
        guild_id = ctx.guild.id

        if guild_id not in queues:
            queues[guild_id] = deque()

        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if voice is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            else:
                return await ctx.send("⚠️ لازم تكون داخل روم صوتي!")

        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'ytsearch',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search, download=False)
            url = info['entries'][0]['url']
            title = info['entries'][0]['title']

        ffmpeg_opts = {
            'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -loglevel panic'
        }

        async def play_next():
            if queues[guild_id]:
                next_url, next_title = queues[guild_id].popleft()
                voice.play(discord.FFmpegPCMAudio(next_url, **ffmpeg_opts),
                           after=lambda e: asyncio.run_coroutine_threadsafe(play_next(), bot.loop))
                asyncio.run_coroutine_threadsafe(ctx.send(f"🎶 شغال الآن: **{next_title}**"), bot.loop)

        if voice.is_playing():
            queues[guild_id].append((url, title))
            await ctx.send(f"⏳ الأغنية **{title}** انتظرت الدور!")
        else:
            voice.play(discord.FFmpegPCMAudio(url, **ffmpeg_opts),
                       after=lambda e: asyncio.run_coroutine_threadsafe(play_next(), bot.loop))
            await ctx.send(f"🎶 شغال الآن: **{title}**")

    except Exception as e:
        print(e)
        await ctx.send("❌ صار خطأ أثناء التشغيل!")


# 🚪 أمر الطرد من الروم الصوتي (ك / k)
@bot.command(aliases=['ك', 'k'])
async def leave(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send("👋 تم طردي من الروم الصوتي!")
    else:
        await ctx.send("❌ أنا مو داخل أي روم صوتي.")


# ⏭️ أمر تخطي الأغنية الحالية (س / s)
@bot.command(aliases=['س', 's'])
async def skip(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("⏭️ تم تخطي الأغنية الحالية!")
    else:
        await ctx.send("⚠️ ما في أغنية شغالة حالياً.")


# شغّل البوت باستخدام التوكن من بيئة Render
bot.run(os.getenv("DISCORD_TOKEN"))
