#!/usr/bin/env python3
import json
import math
import re
import sys
from pathlib import Path


def parse_log(path: Path):
    result = {
        "log": str(path),
        "exists": path.exists(),
        "errors": [],
        "last_thermo": None,
        "loop_time_seconds": None,
        "performance_line": None,
        "cuda_line": None,
    }
    if not path.exists():
        return result
    lines = path.read_text(errors="ignore").splitlines()
    for line in lines:
        low = line.lower()
        if any(token in low for token in ["error", "lost atoms", "nan", "segmentation", "aborted", "exception"]):
            if "warning" not in low:
                result["errors"].append(line)
        if "setting device type" in line or "cuda found" in low or "cuda unavailable" in low:
            result["cuda_line"] = line
        if line.startswith("Loop time of"):
            m = re.search(r"Loop time of\s+([0-9.]+)", line)
            if m:
                result["loop_time_seconds"] = float(m.group(1))
        if line.startswith("Performance:"):
            result["performance_line"] = line
        parts = line.split()
        if len(parts) >= 8:
            try:
                step = int(parts[0])
                time_ps = float(parts[1])
                temp = float(parts[2])
                pe = float(parts[3])
                ke = float(parts[4])
                etotal = float(parts[5])
                press = float(parts[6])
                vol = float(parts[7])
            except ValueError:
                continue
            vals = [time_ps, temp, pe, ke, etotal, press, vol]
            if all(math.isfinite(v) for v in vals):
                result["last_thermo"] = {
                    "step": step,
                    "time_ps": time_ps,
                    "time_ns": time_ps / 1000.0,
                    "temp_K": temp,
                    "pe_eV": pe,
                    "ke_eV": ke,
                    "etotal_eV": etotal,
                    "press_bar": press,
                    "volume_A3": vol,
                }
    return result


def parse_traj(path: Path):
    result = {"trajectory": str(path), "exists": path.exists(), "frames": 0, "last_timestep": None}
    if not path.exists():
        return result
    with path.open(errors="ignore") as handle:
        for line in handle:
            if line.strip() == "ITEM: TIMESTEP":
                raw = next(handle, "").strip()
                try:
                    result["last_timestep"] = int(raw)
                    result["frames"] += 1
                except ValueError:
                    pass
    return result


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: summarize_md.py <lammps.log> <trajectory.lammpstrj>")
    log = parse_log(Path(sys.argv[1]))
    traj = parse_traj(Path(sys.argv[2]))
    print(json.dumps({"log": log, "trajectory": traj}, indent=2))


if __name__ == "__main__":
    main()
