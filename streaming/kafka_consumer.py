from kafka_scoring_consumer import parse_args, run_consumer


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(run_consumer(max_records=args.max_records))
