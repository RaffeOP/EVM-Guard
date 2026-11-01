# Discarded runs

`ethor_docker_oom_4shards/` — first eThor run (2026-11-01), four containers at once in a 4 GB
Docker VM while EVMLiSA ran on the host. eThor peaks at about 1.6 GB per contract, so
containers were starved or killed: front_running__odds_and_evens, recorded as error after 94 s,
finishes in 25 s with verdict `insecure` when run alone, and the Docker daemon stopped
responding during the labeled corpus. None of these rows is used. eThor was rerun from scratch
with three containers in a 6 GB VM (results/baselines_round3/ethor/).
