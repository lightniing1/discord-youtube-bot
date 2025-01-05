import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from discord.ext import tasks

# Configure file logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MusicTrack:
    """Dataclass to store music track information"""
    title: str
    url: str
    duration: int
    filepath: str

class CommandLogger:
    """Handles logging of commands and bot responses"""
    @staticmethod
    async def log_command(ctx: commands.Context, response: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = f"{ctx.author.name}#{ctx.author.discriminator}"
        guild = ctx.guild.name if ctx.guild else "DM"
        channel = ctx.channel.name if ctx.channel else "Direct Message"
        command = ctx.message.content
        
        log_message = (
            f"[{timestamp}] "
            f"Guild: {guild} | "
            f"Channel: {channel} | "
            f"User: {user} | "
            f"Command: {command} | "
            f"Response: {response}"
        )
        
        logger.info(log_message)

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.music_queues = {}
        self.command_logger = CommandLogger()
        self.ytdl = yt_dlp.YoutubeDL({
            'format': 'bestaudio/best',
            'postprocessors': [],
            'quiet': True,
            'noplaylist': True,
            'outtmpl': 'downloads/%(title)s.%(ext)s'
        })

        self.last_activity = {}

    async def setup_hook(self):
        """Create necessary directories on startup"""
        os.makedirs('downloads', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        self.check_inactivity.start()

    def get_queue(self, guild_id: int) -> deque:
        """Get or create queue for guild"""
        if guild_id not in self.music_queues:
            self.music_queues[guild_id] = deque()
        return self.music_queues[guild_id]

    async def extract_track_info(self, query: str) -> MusicTrack:
        """Extract track information from URL or search query"""
        try:
            if not query.startswith(('http://', 'https://')):
                query = f'ytsearch:{query}'

            data = await asyncio.to_thread(self.ytdl.extract_info, query, download=True)
            
            if 'entries' in data:
                data = data['entries'][0]
            
            if data.get('duration', 0) < 60:
                raise ValueError("Video muito curto ou Short do YouTube detectado.")

            return MusicTrack(
                title=data['title'],
                url=data['webpage_url'],
                duration=data['duration'],
                filepath=data['requested_downloads'][0]['filepath']
            )
        except Exception as e:
            logger.error(f"Error extracting track info: {str(e)}")
            raise

    async def cleanup_file(self, filepath: str):
        """Clean up downloaded file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.debug(f"Deleted file: {filepath}")
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {str(e)}")

    @tasks.loop(minutes=1)
    async def check_inactivity(self):
        """Check for voice channel inactivity and disconnect if inactive for 10 minutes"""
        for guild in self.guilds:
            if guild.voice_client:
                last_activity = self.last_activity.get(guild.id, datetime.now())
                if not guild.voice_client.is_playing() and (datetime.now() - last_activity).total_seconds() > 600:  # 10 minutes
                    await guild.voice_client.disconnect()
                    logger.info(f"Disconnected from {guild.name} due to inactivity")

    @check_inactivity.before_loop
    async def before_check_inactivity(self):
        await self.wait_until_ready()

    async def play_next(self, ctx: commands.Context):
        """Play next track in queue"""
        queue = self.get_queue(ctx.guild.id)
        self.last_activity[ctx.guild.id] = datetime.now()
        
        if not queue:
            #await ctx.voice_client.disconnect()
            response = "Fila vazia"
            await self.command_logger.log_command(ctx, response)
            return

        try:
            track = await self.extract_track_info(queue.popleft())
            
            def after_playback(error):
                if error:
                    logger.error(f"Playback error: {str(error)}")
                    
                asyncio.run_coroutine_threadsafe(
                    self.cleanup_file(track.filepath), self.loop
                )
                
                if ctx.voice_client:
                    ctx.voice_client.stop()
                    
                asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.loop
                )

            ctx.voice_client.play(
                discord.FFmpegPCMAudio(track.filepath),
                after=after_playback
            )
            response = f"🎵 Tocando agora: {track.title}"
            await ctx.send(response)
            await self.command_logger.log_command(ctx, response)
            
        except Exception as e:
            response = f"❌ Erro ao tocar música: {str(e)}"
            await ctx.send(response)
            await self.command_logger.log_command(ctx, response)
            await self.play_next(ctx)

bot = MusicBot()

@bot.event
async def on_ready():
    logger.info(f"Bot connected as {bot.user}")

@bot.command(name="play")
async def play(ctx: commands.Context, *, query: str):
    """Play a song by URL or search query"""
    if not ctx.author.voice:
        response = "❌ Você precisa estar em um canal de voz!"
        await ctx.send(response)
        await bot.command_logger.log_command(ctx, response)
        return

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    try:
        track = await bot.extract_track_info(query)
        queue = bot.get_queue(ctx.guild.id)
        
        if not ctx.voice_client.is_playing():
            queue.append(query)
            await bot.play_next(ctx)
        else:
            queue.append(query)
            response = f"📝 Adicionado à fila: {track.title}"
            await ctx.send(response)
            await bot.command_logger.log_command(ctx, response)
            
    except Exception as e:
        response = f"❌ Erro: {str(e)}"
        await ctx.send(response)
        await bot.command_logger.log_command(ctx, response)

@bot.command(name="skip")
async def skip(ctx: commands.Context):
    """Skip current track"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        response = "⏭️ Pulando para próxima música..."
        await ctx.send(response)
        await bot.command_logger.log_command(ctx, response)
    else:
        response = "❌ Nenhuma música tocando!"
        await ctx.send(response)
        await bot.command_logger.log_command(ctx, response)

@bot.command(name="stop")
async def stop(ctx: commands.Context):
    """Stop playback and clear queue"""
    if ctx.voice_client:
        queue = bot.get_queue(ctx.guild.id)
        queue.clear()
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        response = "⏹️ Reprodução parada e fila limpa."
        await ctx.send(response)
        await bot.command_logger.log_command(ctx, response)
    else:
        response = "❌ Bot não está em um canal de voz!"
        await ctx.send(response)
        await bot.command_logger.log_command(ctx, response)

@bot.command(name="queue")
async def queue(ctx: commands.Context):
    """Show current queue"""
    queue = bot.get_queue(ctx.guild.id)
    if not queue:
        response = "📝 Fila vazia!"
        await ctx.send(response)
        await bot.command_logger.log_command(ctx, response)
        return
        
    queue_list = "\n".join(
        f"{i+1}. {url}" for i, url in enumerate(queue)
    )
    response = f"📝 Fila atual:\n{queue_list}"
    await ctx.send(response)
    await bot.command_logger.log_command(ctx, response)

@bot.command(name="commands")
async def commands(ctx: commands.Context):
    """Show all available commands"""
    command_list = "\n".join(
        f"{command.name} - {command.help}" for command in bot.commands
    )
    response = f"📜 Comandos disponíveis:\n{command_list}"
    await ctx.send(response)
    await bot.command_logger.log_command(ctx, response)

# Insira seu token aqui
token = os.environ.get('TOKEN')
bot.run(token)
