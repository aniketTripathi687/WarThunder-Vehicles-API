import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://www.wtvehiclesapi.sgambe.serv00.net/api"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def fetch_vehicle_by_name(name):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/vehicles/search/{name}") as resp:
            if resp.status != 200:
                return None
            ids = await resp.json()
            if not ids:
                return None
            vehicle_id = ids[0]
        async with session.get(f"{API_BASE}/vehicles/{vehicle_id}") as resp:
            if resp.status != 200:
                return None
            return await resp.json()

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="vehicle", description="Get info about a War Thunder vehicle")
@app_commands.describe(name="The name of the vehicle to search for")
async def vehicle_slash(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    vehicle = await fetch_vehicle_by_name(name)
    if not vehicle:
        await interaction.followup.send(f'No vehicle found with name "{name}".')
        return

    embed = discord.Embed(
        title=vehicle.get('identifier', 'Unknown Vehicle'),
        description=f"Country: {vehicle.get('country', 'N/A')}\nType: {vehicle.get('vehicle_type', 'N/A')}",
        color=discord.Color.blue()
    )
    embed.add_field(name="BR (Arcade)", value=vehicle.get('arcade_br', 'N/A'))
    embed.add_field(name="BR (Realistic)", value=vehicle.get('realistic_br', 'N/A'))
    embed.add_field(name="BR (Simulator)", value=vehicle.get('simulator_br', 'N/A'))
    embed.add_field(name="Era", value=vehicle.get('era', 'N/A'))
    embed.add_field(name="Premium", value=str(vehicle.get('is_premium', False)))
    embed.add_field(name="Pack", value=str(vehicle.get('is_pack', False)))
    embed.add_field(name="Squadron", value=str(vehicle.get('squadron_vehicle', False)))
    embed.add_field(name="Marketplace", value=str(vehicle.get('on_marketplace', False)))
    if vehicle.get('release_date'):
        embed.add_field(name="Release Date", value=vehicle.get('release_date'))
    if vehicle.get('event'):
        embed.add_field(name="Event", value=vehicle.get('event'))
    images = vehicle.get('images', {})
    if images and isinstance(images, dict):
        thumb = images.get('card') or images.get('preview')
        if thumb:
            embed.set_thumbnail(url=thumb)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="shutdown", description="Shut down the bot (owner only)")
async def shutdown(interaction: discord.Interaction):
    # Only allow the bot owner to shut down
    app_info = await bot.application_info()
    if interaction.user.id != app_info.owner.id:
        await interaction.response.send_message("You are not authorized to shut down the bot.", ephemeral=True)
        return
    await interaction.response.send_message("Shutting down...", ephemeral=True)
    await bot.close()

if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)