
import json, io
import gradio as gr
from dt_simulator import run_all

TITLE = "Granted Digital Twin — Scenario Runner"
DESC = """
Run **Scenario A (Shadow Mode)** and **Scenario B (Scrape Mode)** using your config.
Upload a JSON config (schema compatible), or edit the template below and click **Run**.
"""

# Load a template to prefill editor
with open("dt_config_template.json") as f:
    TEMPLATE = json.load(f)

def run_sim(json_text: str):
    try:
        cfg = json.loads(json_text)
    except Exception as e:
        return gr.update(value=""), gr.update(value=f"❌ Invalid JSON: {e}")
    try:
        results = run_all(cfg)
        return json.dumps(results, indent=2), gr.update(value="✅ Simulation completed.")
    except Exception as e:
        return "", gr.update(value=f"❌ Simulation error: {e}")

def use_template():
    return json.dumps(TEMPLATE, indent=2)

with gr.Blocks() as demo:
    gr.Markdown(f"# {TITLE}")
    gr.Markdown(DESC)

    with gr.Row():
        with gr.Column(scale=1):
            btn_template = gr.Button("Load Template", variant="secondary")
            cfg_in = gr.Code(label="Simulation Config (JSON)", language="json", value=json.dumps(TEMPLATE, indent=2), lines=30)
            run_btn = gr.Button("Run Scenarios", variant="primary")
        with gr.Column(scale=1):
            out_json = gr.Code(label="Results (JSON)", language="json", value="", lines=30)
            status = gr.Textbox(label="Status", value="", interactive=False)

    btn_template.click(fn=use_template, inputs=None, outputs=cfg_in)
    run_btn.click(fn=run_sim, inputs=cfg_in, outputs=[out_json, status])

if __name__ == "__main__":
    demo.launch()
