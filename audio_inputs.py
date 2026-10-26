"""Wire supplied audio into stock ComfyUI H3 Ref2VA graphs.

Graph preparation only; GPU compatibility and media limits need live validation.
"""
import uuid
from urllib.parse import urlparse
from pathlib import PurePosixPath


def attach_reference_audio(graph, job, upload, media_bytes):
    sources = job.get("reference_audio")
    if sources is None:
        return graph
    if not isinstance(sources, list) or not 1 <= len(sources) <= 3:
        raise ValueError("reference_audio must contain 1 to 3 audio objects")
    targets = [(key, node) for key, node in graph.items()
               if node.get("class_type") == "MiniMaxH3ReferenceToVideo"]
    if len(targets) != 1:
        raise ValueError("Audio upload requires exactly one stock H3 ReferenceToVideo node; Director and FL2VA are not supported by this extension")
    target_inputs = targets[0][1].get("inputs", {})
    if not isinstance(target_inputs.get("audio_vae"), list):
        raise ValueError("Reference audio requires a connected audio VAE")
    if any(key.startswith("ref_audios.") for key in target_inputs):
        raise ValueError("Workflow already contains standalone audio references")
    prepared = []
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("data"), str) or not source["data"]:
            raise ValueError("Each audio object needs data (HTTPS URL or base64) and a filename")
        value = source["data"]
        parsed = urlparse(value)
        if parsed.scheme and parsed.scheme != "https":
            raise ValueError("Audio URLs must use HTTPS; otherwise supply raw base64")
        name = source.get("filename") or (parsed.path if parsed.scheme else "")
        if not isinstance(name, str):
            raise ValueError("Audio filename must be a string")
        suffix = PurePosixPath(name).suffix.lower()
        if suffix not in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}:
            raise ValueError("Audio needs a supported filename extension")
        prepared.append((value, suffix))
    # Validate all source descriptors before doing any network operations.
    for index, (value, suffix) in enumerate(prepared):
        node_id = "studio_audio_" + uuid.uuid4().hex
        filename = upload(node_id + suffix, media_bytes(value))
        graph[node_id] = {"class_type": "LoadAudio", "inputs": {"audio": filename}}
        target_inputs[f"ref_audios.ref_audio_{index}"] = [node_id, 0]
    return graph
