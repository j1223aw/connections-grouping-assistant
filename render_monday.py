import asyncio
import subprocess

SCRIPT_TEXT = """Do not fall for the five-word hustler trap on today's Monday NYT Connections.

Scanning the board, five words immediately scream scam: CON JOB, SHELL GAME, FLIMFLAM, RIP-OFF, and CARD SHARK. 

If you guess CARD SHARK with the con artists, you burn a life. CARD SHARK is the pivot hinge. Look across the board at NAVY SEAL, GAMMA RAY, and FUN SPONGE. What do SEAL, RAY, and SPONGE have in common? They are all sea creatures hiding at the end of phrases. Add SHARK, and you isolate the Purple tier: Words ending in marine animals.

With Purple secured, the scam quartet clears easily: CON JOB, FLIMFLAM, RIP-OFF, and SHELL GAME take Yellow.

Now look at the clothing terms. BOOTCUT, LOW-RISE, SKINNY, and DISTRESSED lock in the Green category for styles of jeans.

That leaves the trickiest four: STEAK KNIFE, TAPE DISPENSER, GRAPEFRUIT SPOON, and MINT LEAF. What connects kitchen cutlery, office supplies, and foliage? Every single one features serrated edges.

Lock them in, protect your streak, and test your boards on the neural scratchboard at connectionsassistant.com."""

async def generate_narration():
    import edge_tts
    communicate = edge_tts.Communicate(SCRIPT_TEXT, voice="en-US-ChristopherNeural", rate="+4%")
    await communicate.save("narration_1552.mp3")

if __name__ == "__main__":
    print("[1/3] Generating edge-tts narration...")
    asyncio.run(generate_narration())
    
    print("[2/3] Rendering 1080x1920 Short via NVENC on RTX 3050...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x0f0f13:s=1080x1920:r=60",
        "-i", "narration_1552.mp3",
        "-c:v", "h264_nvenc",
        "-preset", "p6",
        "-tune", "hq",
        "-b:v", "12M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "Connections_1552_Monday.mp4"
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print("[3/3] Video complete: Connections_1552_Monday.mp4")
