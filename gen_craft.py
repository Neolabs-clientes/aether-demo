#!/usr/bin/env python3
"""Genera foto macro de crafting para AETHER: liquido ambar girando con particulas de oro."""
import requests, json, time, os, shutil, sys

COMFY = "http://127.0.0.1:8190"
ASSETS = "/home/dorti/clients/aether-demo/assets"
WF = "/home/dorti/neo-libros/chatgpt-profesionales/workflows/portada_2x3.json"

NEG = (
    "worst quality, low quality, blurry, out of focus, distorted, deformed, ugly, "
    "text, letters, words, numbers, watermark, logo, label, "
    "cartoon, illustration, painting, 3d render, cgi, "
    "oversaturated, overexposed, blown out, grain, noise, jpeg artifacts, pixelated, "
    "multiple bottles, hands, people, face"
)

PROMPTS = [
    ("craft.jpg",
     "extreme macro photography of golden amber perfume liquid swirling in dark glass, "
     "glowing gold particles suspended in the liquid, wisps of smoke, dramatic backlight, "
     "dark black background, luxury cosmetic advertising photography, "
     "ultra sharp macro detail, shallow depth of field, photorealistic, 8k"),
    ("detail.jpg",
     "luxury perfume bottle cap in macro detail, polished gold cap with engraved rings, "
     "fine mist of golden oil droplets in the air, dark black background, "
     "dramatic warm rim light, ultra sharp macro photography, luxury advertising, photorealistic, 8k"),
]

SEED = 777333112

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
            inputs["width"], inputs["height"] = 768, 1024
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
                            print(f"  OK {out} ({time.time()-t0:.0f}s)")
                            return True
        except Exception:
            pass
        time.sleep(2)
    print(f"  TIMEOUT {out}")
    return False

if __name__ == "__main__":
    print(f"Generando {len(PROMPTS)} macros (30 pasos, seed {SEED})...")
    for out, prompt in PROMPTS:
        generate(out, prompt, SEED)
    print("DONE")
