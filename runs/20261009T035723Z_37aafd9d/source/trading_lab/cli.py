import argparse
from pathlib import Path
from .data import load_config, synthetic, read_data
from .research import run_research


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/demo.json")
    p.add_argument("--data")
    p.add_argument("--output", default="runs")
    args = p.parse_args()
    c = load_config(args.config)
    if not args.data and c["data_kind"] != "synthetic":
        p.error("Dados reais exigem --data")
    d = read_data(args.data, c) if args.data else synthetic(c)
    if not args.data:
        Path("data").mkdir(exist_ok=True)
        d.to_csv("data/demo_intraday.csv", index=False)
        d.to_parquet("data/demo_intraday.parquet", index=False)
    out, summary, _ = run_research(d, c, args.output)
    print(out)
    print(summary[["particao", "estrategia", "retorno_liquido", "operacoes_fechadas", "evidencia"]].to_string(index=False))


if __name__ == "__main__":
    main()
