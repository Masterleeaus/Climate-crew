import os
from PIL import Image
from io import BytesIO
from google import genai
from google.genai import types

class ClimateVisualizer:
    def __init__(self, client):
        self.client = client
        self.model = "imagen-4.0-generate-001"

    def generate_sequence(self, prompts, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []
        
        for i, prompt in enumerate(prompts):
            print(f"Generating image frame {i+1}/{len(prompts)} for prompt: {prompt[:30]}...")
            try:
                response = self.client.models.generate_images(
                    model=self.model,
                    prompt=prompt + ", photorealistic, 4k, cinematic lighting",
                    config=types.GenerateImagesConfig(number_of_images=1)
                )
                
                if response.generated_images:
                    img_bytes = response.generated_images[0].image.image_bytes
                    img = Image.open(BytesIO(img_bytes))
                    filename = f"frame_{i:02d}.png"
                    path = os.path.join(output_dir, filename)
                    img.save(path)
                    image_paths.append(path)
            except Exception as e:
                print(f"Failed to generate image for prompt '{prompt[:20]}...': {e}")
                
                
        return image_paths

    def create_video(self, image_paths, output_path):
        # Using GIF as fallback to avoid codec issues on Windows
        output_path = output_path.replace(".webm", ".gif").replace(".mp4", ".gif")
        if not image_paths:
            return None
            
        frames = [Image.open(p) for p in image_paths]
        frames[0].save(
            output_path,
            format='GIF',
            append_images=frames[1:],
            save_all=True,
            duration=500, # 500ms per frame
            loop=0
        )
        return output_path

    def merge_videos(self, video_paths, output_path):
        # Merging GIFs
        output_path = output_path.replace(".webm", ".gif").replace(".mp4", ".gif")
        if not video_paths:
            return None

        all_frames = []
        for vp in video_paths:
            if vp.endswith(".gif"):
                im = Image.open(vp)
                for i in range(im.n_frames):
                    im.seek(i)
                    all_frames.append(im.copy())
            
        if all_frames:
             all_frames[0].save(
                output_path,
                format='GIF',
                append_images=all_frames[1:],
                save_all=True,
                duration=500,
                loop=0
            )
             return output_path
        return None
