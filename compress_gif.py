import os
import sys
from PIL import Image
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from tqdm import tqdm

console = Console()


def get_file_size(filepath):
    """Returns the file size in MB."""
    return os.path.getsize(filepath) / (1024 * 1024)


def process_gif():
    console.print(
        Panel.fit(
            "[bold blue]Advanced Interactive GIF Compressor[/bold blue] \nPowered by Rich, TQDM, and Pillow"
        )
    )

    # 1. Get Input File
    input_path = Prompt.ask(
        "[bold green]Enter the path to the input GIF file[/bold green]"
    )
    if not os.path.exists(input_path) or not input_path.lower().endswith(".gif"):
        console.print(
            "[bold red]Error:[/bold red] File does not exist or is not a GIF."
        )
        sys.exit(1)

    original_size = get_file_size(input_path)
    console.print(f"Original File Size: [bold cyan]{original_size:.2f} MB[/bold cyan]")

    # 2. Get Output File
    default_output = input_path.replace(".gif", "_compressed.gif")
    output_path = Prompt.ask(
        "[bold green]Enter the output path[/bold green]", default=default_output
    )

    # 3. Advanced Options
    console.print("\n[bold yellow]--- Compression Options ---[/bold yellow]")

    scale_percent = IntPrompt.ask(
        "Enter resize percentage (1-100) [100 means no resizing]",
        default=100,
        choices=[str(i) for i in range(1, 101)],
    )

    colors = IntPrompt.ask(
        "Enter max colors for palette (2-256) [Lower = smaller file, less quality]",
        default=128,
        choices=[str(i) for i in range(2, 257)],
    )

    # 4. Process the GIF
    console.print("\n[bold yellow]Loading frames...[/bold yellow]")
    try:
        img = Image.open(input_path)
        frames = []

        # Extract durations and loop info
        duration = img.info.get("duration", 100)
        loop = img.info.get("loop", 0)

        # Extract all frames
        try:
            while True:
                frames.append(img.copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass  # End of sequence

        total_frames = len(frames)
        console.print(
            f"Loaded [bold cyan]{total_frames}[/bold cyan] frames. Starting compression...\n"
        )

        processed_frames = []

        # TQDM progress bar. Because we process frame-by-frame, TQDM automatically
        # calculates the iterations per second (it/s) and estimates the time remaining
        # based strictly on how fast your CPU crunches through the loop.
        for frame in tqdm(
            frames, desc="Compressing Frames", unit="frame", dynamic_ncols=True
        ):
            # Convert to standard format for manipulation
            frame = frame.convert("RGBA")

            # Resize if requested
            if scale_percent < 100:
                new_width = int(frame.width * (scale_percent / 100))
                new_height = int(frame.height * (scale_percent / 100))
                # Using LANCZOS for high-quality downsampling
                frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Quantize (reduce colors)
            # method=2 corresponds to fast octree color quantization
            frame = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)

            processed_frames.append(frame)

        # 5. Save the final GIF
        console.print("\n[bold yellow]Saving compressed GIF to disk...[/bold yellow]")
        processed_frames[0].save(
            output_path,
            save_all=True,
            append_images=processed_frames[1:],
            optimize=True,
            duration=duration,
            loop=loop,
        )

        # 6. Final Feedback
        new_size = get_file_size(output_path)
        savings = ((original_size - new_size) / original_size) * 100

        console.print(
            Panel.fit(
                f"[bold green]Compression Complete![/bold green]\n"
                f"Original Size: {original_size:.2f} MB\n"
                f"New Size:      {new_size:.2f} MB\n"
                f"Space Saved:   [bold cyan]{savings:.1f}%[/bold cyan]"
            )
        )

    except Exception as e:
        console.print(f"[bold red]An error occurred during processing:[/bold red] {e}")


if __name__ == "__main__":
    process_gif()
