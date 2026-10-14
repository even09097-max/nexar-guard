import json
import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم البوت: {bot.user.name}")
    print("نظام NEXAR GUARD يعمل بكفاءة وحماية تامة.")

@bot.command(name="الحالة")
async def bot_status(ctx):
    embed = discord.Embed(
        title="🛡️ نظام حماية NEXAR GUARD",
        description="البوت يعمل بشكل مستقل وجاهز لتأمين السيرفر وإدارة الرتب والرومات.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# ضع توكن البوت الخاص بك بين علامتي التنصيص أدناه
TOKEN =MTU1OTkwNTIzMjQ5Mjk1Nzc0Ng.Gr_y4l.zBmQHAPTq9ulXUa7XEeDEL9FdHO1P-CsRz5G8M
bot.run(TOKEN)
