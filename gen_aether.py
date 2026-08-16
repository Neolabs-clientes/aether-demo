#!/usr/bin/env python3
"""Genera fotos de producto fotorrealistas del frasco AETHER: hero + 4 fragancias (misma semilla, solo cambia el liquido)."""
import requests, json, time, os, shutil, sys

COMFY = "http://127.0.0.1:8190"
ASSETS = "/home/dorti/clients/aether-demo/assets"
os.makedirs(ASSETS, exist_ok=True)
WF = "/home/dorti/neo-libros/chatgpt-profesionales/workflows/portada_2x3.json"

NEG = (
    "worst quality, low quality, blurry, out of focus, distorted, deformed, ugly, "
    "duplicate, clone, mirrored, extra limbs, mutated, malformed, "
    "text, letters, words, numbers, watermark, signature, logo, label text, barcode, "
    "cartoon, illustration, painting, 3d render, cgi, "
    "oversaturated, overexposed, blown out, grain, noise, jpeg artifacts, pixelated, "
    "multiple bottles, two bottles, reflection of bottle in glass, window reflection"
)

BASE = (
    "luxury perfume bottle product photography, {LIQ} in a rectangular black glass bottle, "
    "polished gold cap and gold collar, standing on a dark reflective surface, black background, "
    "dramatic studio lighting with a sharp warm rim light, ultra sharp focus, "
    "premium cosmetic advertising photography, photorealistic, highly detailed, 8k, "
    "centered composition, vertical"
)

IMAGES = [
    ("hero.jpg",
     "luxury perfume bottle product photography, floating golden dust particles and soft smoke in the air, "
     "rectangular black glass bottle with polished gold cap, standing on a dark reflective surface, "
     "black background, dramatic side rim lighting, moody cinematic luxury atmosphere, "
     "ultra sharp focus, premium advertising photography, photorealistic, highly detailed, 8k"),
    ("noir.jpg",     BASE.format(LIQ="deep violet-black liquid")),
    ("rouge.jpg",    BASE.format(LIQ="deep crimson red liquid")),
    ("emeraude.jpg", BASE.format(LIQ="deep emerald green liquid")),
    ("azur.jpg",     BASE.format(LIQ="deep sapphire blue liquid")),
]

SEED = 777333111

def generate(out, prompt, seed):
    with open(WF) as f:
        wf = json.load(f)
    for nid, node in wf.items():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs", {})
        ct = node.get("class_type", "")
        if ct == "CLIPTextEncode":
            t = str(inputs.get("text", ""))
            if "PROMPT_HERE" in t:
                inputs["text"] = prompt
            elif "NEGATIVE_PROMPT_HERE" in t:
                inputs["text"] = NEG
        elif ct == "KSampler":
            inputs["seed"] = seed
            inputs["steps"] = 30
        elif ct == "EmptyLatentImage":
            inputs["width"], inputs["height"] = 896, 1152
    r = requests.post(f"{COMFY}/prompt", json={"prompt": wf}, timeout=15)
    res = r.json()
    if "prompt_id" not in res:
        print(f"  ERROR {out}: {res}")
        return False
    pid = res["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 300:
        try:
            hh = requests.get(f"{COMFY}/history/{pid}", timeout=5).json()
            if pid in hh:
                for nid, no in hh[pid].get("outputs", {}).items():
                    for img in no.get("images", []):
                        src = os.path.join("/home/dorti/jarvis/ComfyUI/output",
                                           img.get("subfolder", ""), img.get("filename", ""))
                        if os.path.exists(src):
                            shutil.copy2(src, os.path.join(ASSETS, out))
                            os.remove(src)
                            print(f"  OK {out} ({time.time()-t0:.0f}s) {os.path.getsize(os.path.join(ASSETS,out))//1024} KB")
                            return True
        except Exception:
            pass
        time.sleep(2)
    print(f"  TIMEOUT {out}")
    return False

if __name__ == "__main__":
    print(f"Generando {len(IMAGES)} fotos AETHER (30 pasos, seed {SEED})...")
    for out, prompt in IMAGES:
        generate(out, prompt, SEED)
    print("DONE")
